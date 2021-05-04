import json
import random
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Iterator
from urllib.parse import urlparse

import bs4  # type: ignore
import requests

if __package__ is None or __package__ == "":
    # Uses current directory visibility when not running as a package.
    import notify
    from logger import logger
    from my_types import WishlistItem, WishlistDict
else:
    # Uses current package visibility when running as a package or with pytest.
    from . import notify
    from .logger import logger
    from .my_types import WishlistItem, WishlistDict


class PriceWatch:
    """A class to manage interaction with Amazon wishlists.

    Provides methods to create `Wishlist` objects by sending web requests to a
    public wishlist URL and parsing the response into a custom `Wishlist` object.
    `Wishlist` instances can then be compared with results from previous runs to
    determine if an item's price has been reduced.

    Attributes:
        config: A dictionary of configuration values loaded from `config.json`.
        wishlist: A `Wishlist` class instance to store items retrieved and parsed
            during the current run.
        json_man: A `JsonManager` instance to access wishlist data from previous
            runs, and to store data for the next run.
        headers: Headers dictionary to be used in web requests. A user specified
            `User-Agent` is retrieved from `config.json`.
        session: A `requests.session` instance to persist parameters/cookies
            across requests.
        wishlist_url: The wishlist URL used for the initial request.
        wishlist_domain: The domain of the wishlist URL to be concatenated with
            additional page (pagination) paths.
    """

    def __init__(self):
        """Inits the PriceWatch class."""
        self.config = notify.get_config()
        self.wishlist = Wishlist()
        self.json_man = JsonManager()
        self.headers = {
            "User-Agent": self.config["general"]["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)
        self.wishlist_url = self.config["general"]["wishlist_url"]
        self.wishlist_domain = urlparse(self.wishlist_url).netloc

    def request_page(self, wishlist_url: Optional[str] = None) -> requests.Response:
        """Request a wishlist page and return the response.

        If no argument for ``wishlist_url`` is supplied, it is assumed a request to
        the first wishlist page is being made, which is retrieved from the class
        `wishlist_url` attribute. In the event of a failed request a notification
        is triggered to the user via the notification methods specified in
        `config.json` and an exception is raised.

        Args:
            wishlist_url: Optional; The wishlist page URL to request.

        Returns:
            A `requests.Response` object of the wishlist page if the request
            is successful.

        Raises:
            requests.Timeout: The request timed out.
            requests.URLRequired: An invalid URL was supplied.
            requests.ConnectionError: User's IP may be blocked / bot detection.
            requests.exceptions.RequestException: Requests base exception.
        """
        if not wishlist_url:
            # Visiting first page of wishlist.
            wishlist_url = self.wishlist_url
        try:
            res = self.session.get(wishlist_url, timeout=10)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            notify.failed_request_msg()
            logger.exception(f"Failed to request wishlist page: {wishlist_url}")
            raise

        logger.info(f"Success requesting wishlist page: {wishlist_url}")
        return res

    def parse_wishlist(self, response: requests.Response) -> None:
        """Parse wishlist items from a ``requests.Response``.

        Parse the wishlist request response for each item's `title`, `byline`,
        `price`, `url` and `asin`. Add items to the `self.wishlist` obj. If a
        "see more" (pagination) link is found, a recursive call is made to
        request and parse the next page. Sleeps for 1000-2000ms between each
        request.

        Args:
            response: A `requests.Response` object of a wishlist page.

        Returns:
            None
        """
        soup = bs4.BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all("li", attrs={"class": "a-spacing-none g-item-sortable"})

        if items:
            for item in items:
                try:
                    title = item.find("a", attrs={"class": "a-link-normal"})["title"]
                    byline = item.find(
                        "span", attrs={"class": "a-size-base"}
                    ).text.strip()
                    price = item["data-price"]
                    url = item.find("a", attrs={"class": "a-link-normal"})["href"]

                    # Asin found in li class attrs as part of a json string.
                    item_attrs_json = item.attrs["data-reposition-action-params"]
                    item_attrs = json.loads(item_attrs_json)
                    asin_and_marketplace_id = item_attrs["itemExternalId"].split("|")
                    asin = asin_and_marketplace_id[0].lstrip("ASIN:")

                    self.wishlist.add_item(
                        title=title,
                        byline=byline,
                        price=price,
                        url=url,
                        asin=asin,
                    )
                except (KeyError, TypeError) as e:
                    logger.warning("Failed to parse a wishlist item.")

            # Check for pagination / next page of wishlist.
            see_more = soup.find(
                "a",
                attrs={
                    "class": "a-size-base a-link-nav-icon "
                    "a-js g-visible-no-js wl-see-more"
                },
            )
            if see_more:
                # Avoid bombarding Amazon with requests to avoid bot detection.
                time.sleep(random.randint(1000, 2000) / 1000.0)
                self.parse_wishlist(
                    self.request_page(
                        f"https://{self.wishlist_domain}{see_more['href']}"
                    )
                )
            else:
                # No more pages to wishlist.
                logger.info("Success parsing wishlist.")
                return
        else:
            # Pagination led to page without any items or wishlist was empty.
            logger.warning(
                f"End of wishlist or wrong URL? No items found on page {response.url}."
            )
            return

    def compare_prices(self) -> Optional[List[WishlistItem]]:
        """Compare prices of items between two `Wishlist` objects.

        Compare prices of each item found in the current run's `Wishlist`
        against the best price seen for that item across previous runs. Items
        are matched by their `asin`. If a new lowest price is found, a dictionary
        of the item's attrs is added to the list `new_cheaper_items`.

        Returns:
            new_cheaper_items: A list of `WishlistItem` dicts which have a new
                lowest seen price. Or an empty list if no new price reductions
                are found.
        """
        new_cheaper_items = []  # Store items found to have a price reduction.
        # Load wishlist from last run of program.
        prev_wishlist = Wishlist(self.json_man.get_wishlist_dict())
        if prev_wishlist.is_empty():
            logger.info(
                "No previous wishlist to compare against."
                " Probably running for the first time."
            )
            return None
        else:
            for item in prev_wishlist:
                old_price = float(item["price"])
                try:
                    current_price = float(self.wishlist.get_item_price(item["asin"]))
                except KeyError:
                    logger.info(f"{item['asin']} removed from wishlist. Skipping.")
                    continue
                if current_price < old_price:
                    new_cheaper_items.append(self.wishlist.get_item(item["asin"]))
                elif current_price > old_price:
                    # Price has increased. Overwrite current wishlist item price
                    # with the old, cheaper price to be saved to json for next run.
                    # This keeps a record of the lowest ever seen price.
                    self.wishlist.update_price(item["asin"], str(old_price))

            if new_cheaper_items:
                logger.info(
                    f"Success comparing prices. {len(new_cheaper_items)} reduced prices found."
                )
            else:
                logger.info("No items to compare.")

            return new_cheaper_items


class Wishlist:
    """An Amazon wishlist dictionary based data structure.

    A class to interact with an Amazon wishlist stored in a
    `Dict[asin, WishlistItem]` format, with methods for adding, getting or
    iterating over items.

    Args:
        prev_dict: Optional; If creating a `Wishlist` from a previous run, provide
        a ``prev_dict`` loaded from `wishlist_items.json`.

    Attributes:
        wishlist_dict: A dictionary containing all wishlist items in a
        `Dict[asin, WishlistItem]` format.

    Notes:
        The dictionary structure for the `Wishlist` and `WishlistItem` objects
        is outlined in `my_types.py`.
    """

    def __init__(self, prev_dict: Optional[WishlistDict] = None):
        """Init the Wishlist class."""
        if prev_dict:
            self.wishlist_dict = prev_dict
        else:
            self.wishlist_dict = {}  # type: ignore

    def __iter__(self) -> Iterator[WishlistItem]:
        """Iterate over items in the `Wishlist`.

        Returns: `WishlistItem` dictionary.
        """
        for asin in self.wishlist_dict:
            yield self.wishlist_dict[asin]

    def __len__(self) -> int:
        """Return number of wishlist items in `Wishlist` as int."""
        return len(self.wishlist_dict)

    def __getitem__(self, asin: str) -> WishlistItem:
        """Return `WishlistItem` matching ``asin``"""
        return self.wishlist_dict[asin]

    def is_empty(self) -> bool:
        """Return True is `Wishlist` is empty, False otherwise."""
        return self.wishlist_dict == {}

    def add_item(
        self, title: str, price: str, url: str, asin: str, byline: Optional[str] = None
    ) -> None:
        """Add an item to the Wishlist.

        A `WishlistItem` dict is created using the provided arguments and added
        to the `Wishlist` dict using ``asin`` as the key.

        Args:
            title: Title of the item.
            price: Price of the item. Excluding currency symbol.
            url: Full URL of the item on Amazon's website.
            asin: Amazon Standard Identification Number (item id).
            byline: Optional; Item byline, e.g. used for book's author. Defaults
                to `None` if not provided.

        Returns:
            None
        """
        self.wishlist_dict[asin] = {
            "title": title,
            "byline": byline if byline and len(byline) > 0 else None,
            "price": price,
            "url": url,
            "asin": asin,
        }

    def update_price(self, asin: str, price: str) -> None:
        """Update item `price` by ``asin``."""
        self.wishlist_dict[asin]["price"] = price

    def get_item_price(self, asin: str) -> str:
        """Get item `price` by ``asin``."""
        return self.wishlist_dict[asin]["price"]

    def get_item(self, asin: str) -> WishlistItem:
        """Get `WishlistItem` by ``asin``"""
        return self.wishlist_dict[asin]


class JsonManager:
    """Manage loading/saving to/from the `wishlist_items` json file.

    Attributes:
        wishlist_json_path: Path to `wishlist_items.json`. File is expected
            to exist on the same path as this source file.
        prev_wishlist: Json file loaded as a python dict.
    """

    def __init__(self):
        """Init JsonManager using `wishlist_json_path`."""
        self.wishlist_json_path = Path(
            Path(__file__).parent, "wishlist_items.json"
        ).resolve()
        self.prev_wishlist = self.get_wishlist_dict()

    def get_wishlist_dict(self) -> Dict:
        """Open `wishlist_items.json` as dict. Return empty dict if
        no such file.
        """
        try:
            with open(self.wishlist_json_path, "r") as wishlist_json:
                return json.load(wishlist_json)
        except FileNotFoundError:
            # Probably running for the first time.
            return {}

    def save_wishlist_json(self, wishlist: Wishlist) -> None:
        """Save ``wishlist`` as `wishlist_items.json`."""
        with open(self.wishlist_json_path, "w+") as json_file:
            json.dump(wishlist.wishlist_dict, json_file)


def main():
    """Run one full pass of the program.

    Create an instance of `PriceWatch`. Before continuing, check if the user
    has filled in `config.json` or has specified a test notification only run.
    If not, continue to request and parse all pages of the wishlist from
    Amazon's website. If there are any items with a "new lowest price", send
    the user a notification. Save the results from this pass to a json file
    for next run.
    """
    logger.info("Started script.")
    pw = PriceWatch()

    if pw.config["general"]["send_test_notification"] == "1":
        logger.info("Sending test notification and exiting.")
        notify.test_notification()
        sys.exit()
    elif (
        pw.config["general"]["wishlist_url"]
        == "https://www.amazon.co.uk/hz/wishlist/ls/S0M3C0D3"
    ):
        config_file_path = Path(Path(__file__).parent, "config.json").resolve()
        logger.error(f"You need to fill in the config file:\n{config_file_path}")
        sys.exit()

    page = pw.request_page()
    # In parsing the first page, pagination will be followed and requested/parsed.
    pw.parse_wishlist(page)
    new_cheaper_items = pw.compare_prices()
    if new_cheaper_items:
        notify.send_notification(wishlist_item_list=new_cheaper_items)

    pw.json_man.save_wishlist_json(pw.wishlist)
    logger.info("Finished.")


if __name__ == "__main__":
    main()


# TODO: Check for usages of wishlist.wishlist_dict["something"] instead of __getitem__.
# TODO: More logging.
# TODO: Run on startup option for readme: Startup folder shortcut / task sched
# TODO: Google app passwords for docs/readme
# TODO: Test on other country wishlists.
# TODO: ?

import json
import os
import random
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import bs4
import requests

import notify
from logger import logger


class PriceWatch:
    """TODO"""

    def __init__(self):
        self.config = notify.get_config()
        self.wishlist = Wishlist()
        self.json_man = JsonManager()
        self.new_cheaper_items = []
        self.headers = {
            'User-Agent': self.config["general"]["user_agent"],
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

    def request_page(self, wishlist_url=None):
        """"""
        if not wishlist_url:
            # Requesting first wishlist page.
            wishlist_url = self.wishlist_url
        try:
            res = self.session.get(wishlist_url, timeout=10)
            res.raise_for_status()
        except requests.RequestException as e:
            notify.failed_request_msg()
            logger.exception(f"Failed to request wishlist page: {wishlist_url}")
            raise

        return res

    def parse_wishlist(self, response):
        """TODO"""
        soup = bs4.BeautifulSoup(response.text, features="html.parser")
        items = soup.find_all('li', attrs={'class': 'a-spacing-none g-item-sortable'})

        if items:
            for item in items:
                title = item.find('a', attrs={'class': 'a-link-normal'})['title']
                byline = item.find('span', attrs={'class': 'a-size-base'}).text.strip()
                price = item["data-price"]
                url = item.find('a', attrs={'class': 'a-link-normal'})['href']

                # Asin found in li class attrs as part of a json string.
                item_attrs_json = item.attrs['data-reposition-action-params']
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

            see_more = soup.find("a",
                                 attrs={"class": "a-size-base a-link-nav-icon "
                                                 "a-js g-visible-no-js wl-see-more"})
            if see_more:
                # Avoid bombarding Amazon with requests to avoid bot detection.
                time.sleep(random.randint(1000, 2000) / 1000.0)
                self.parse_wishlist(
                    self.request_page(
                        f"https://{self.wishlist_domain}{see_more['href']}"
                    )
                )
            else:
                return
        else:
            logger.warn(f"End of wishlist? No items found on page {response.url}.")
            return

    def compare_prices(self):
        """TODO"""
        prev_wishlist = Wishlist(self.json_man.get_wishlist_dict())
        if prev_wishlist.is_empty():
            logger.info("No previous wishlist to compare against."
                        " Probably running for the first time.")
        else:
            for item in prev_wishlist:
                old_price = float(item["price"])
                try:
                    current_price = float(self.wishlist.get_item_price(item["asin"]))
                except KeyError:
                    logger.info(f"{item['asin']} removed from wishlist. Skipping.")
                    continue
                if current_price < old_price:
                    # Current wishlist item price is lower than we have seen before.
                    self.new_cheaper_items.append(
                        self.wishlist.get_item(item["asin"])
                    )
                elif current_price > old_price:
                    # Price has increased. Overwrite current wishlist item price
                    # with the old, cheaper price to be saved to json for next run.
                    # This keeps a record of the lowest ever seen price.
                    self.wishlist.update_price(item["asin"], str(old_price))


class Wishlist:
    """TODO"""

    def __init__(self, prev_dict=None):
        if prev_dict:
            self.wishlist_dict = prev_dict
        else:
            self.wishlist_dict = {}

    def __iter__(self):
        for asin in self.wishlist_dict:
            yield self.wishlist_dict[asin]

    def add_item(self, title=None, byline=None, price=None, url=None, asin=None):
        """TODO"""
        self.wishlist_dict[asin] = {
            "title": title,
            "byline": byline if byline and len(byline) != 0 else None,
            "price": price,
            "url": url,
            "asin": asin,
        }

    def update_price(self, asin, price):
        """TODO"""
        self.wishlist_dict[asin]["price"] = price

    def get_item_price(self, asin):
        """TODO"""
        return self.wishlist_dict[asin]["price"]

    def get_item(self, asin):
        """TODO"""
        return self.wishlist_dict[asin]

    def is_empty(self):
        """TODO"""
        return self.wishlist_dict == {}


class JsonManager:
    """TODO"""

    def __init__(self):
        self.wishlist_json_path = Path(os.path.realpath(sys.path[0]),
                                       "wishlist_items.json")
        self.prev_wishlist = self.get_wishlist_dict()

    def get_wishlist_dict(self):
        """TODO"""
        try:
            with open(self.wishlist_json_path, "r") as wishlist_json:
                return json.load(wishlist_json)
        except FileNotFoundError:
            return {}

    def save_wishlist_json(self, wishlist):
        """TODO"""
        with open(self.wishlist_json_path, "w+") as json_file:
            json.dump(wishlist.wishlist_dict, json_file)


def main():
    """TODO"""
    logger.info("Started script.")
    pw = PriceWatch()

    if pw.config["general"]["send_test_notification"] == "1":
        logger.info("Sending test notification and exiting.")
        notify.test_notification()
        sys.exit()

    page = pw.request_page()
    pw.parse_wishlist(page)
    pw.compare_prices()
    if pw.new_cheaper_items:
        notify.send_notification(
            wishlist_item_list=pw.new_cheaper_items
        )

    pw.json_man.save_wishlist_json(pw.wishlist)
    logger.info("Finished.")


if __name__ == "__main__":
    main()


# TODO: More logging.
# TODO: Packaging?
# TODO: Black auto format
# TODO: Run on startup option for readme: Startup folder shortcut / task sched
# TODO: Google app passwords for docs/readme
# TODO: Tests?
# TODO: ?

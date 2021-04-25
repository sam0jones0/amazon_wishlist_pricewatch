from pricewatch.amzn_pricewatch import PriceWatch, Wishlist, JsonManager
from pricewatch.my_types import WishlistItem, WishlistDict
import pytest
import json
import pricewatch.notify as notify
from pathlib import Path
import pricewatch.logger as logger

# TODO: Test ordinary cases first, i.e. Expected usage.
#  Test the common case of everything you can.

# amzn_pricewatch.py


class TestPriceWatch:
    """TODO"""

    # TODO: Class level scope PriceWatch()

    def test_parse_wishlist(self, mock_config):
        """TODO"""
        # TODO: Mock or monkeypatch standard response obj.
        pw = PriceWatch()
        page = pw.request_page()
        pw.parse_wishlist(page)
        assert not pw.wishlist.is_empty()

    def test_compare_prices(
        self, example_wishlist_items, mock_prev_wishlist, mock_config
    ):
        """TODO"""
        pw = PriceWatch()
        pw.wishlist = Wishlist(example_wishlist_items)
        cheaper_items = pw.compare_prices()
        # Check the item with a reduced price is added to cheaper_items list.
        assert len(cheaper_items) == 1
        assert cheaper_items[0]["price"] == "6.0"
        # Check the old, cheaper price is saved instead of increased price.
        assert pw.wishlist.get_item_price("2") == "9.15"


class TestWishlist:
    """TODO"""

    def test_init_with_existing_dict(self, example_wishlist_items):
        wishlist = Wishlist(example_wishlist_items)
        assert not wishlist.is_empty()
        assert len(wishlist) == 2

    def test_init_without_existing_dict(self):
        wishlist = Wishlist()
        assert wishlist.is_empty()

    def test_adding_some_items(self):
        wishlist = Wishlist()

        wishlist.add_item(
            title="Test title",
            byline="Test byline",
            price="0.99",
            url="www.example.com",
            asin="1",
        )
        wishlist.add_item(
            title="Test title 2", price="2.99", url="www.example2.com", asin="2"
        )
        assert len(wishlist) == 2

        item_1 = wishlist["1"]
        assert item_1["title"] == "Test title"
        assert item_1["byline"] == "Test byline"
        assert item_1["price"] == "0.99"
        assert item_1["url"] == "www.example.com"
        assert item_1["asin"] == "1"

        item_2 = wishlist["2"]
        assert item_2["title"] == "Test title 2"
        assert item_2["byline"] is None
        assert item_2["price"] == "2.99"
        assert item_2["url"] == "www.example2.com"
        assert item_2["asin"] == "2"

    def test_update_price(self, wishlist_with_two_items: Wishlist):
        assert wishlist_with_two_items["1"]["price"] == "0.99"
        wishlist_with_two_items.update_price(asin="1", price="26.00")
        assert wishlist_with_two_items["1"]["price"] == "26.00"

    def test_get_item_price(self, wishlist_with_two_items: Wishlist):
        price_1 = wishlist_with_two_items.get_item_price("1")
        price_2 = wishlist_with_two_items.get_item_price("2")
        assert price_1 == "0.99"
        assert price_2 == "2.99"

    def test_get_item(self, wishlist_with_two_items: Wishlist):
        item = wishlist_with_two_items.get_item("1")
        assert item["title"] == "Test title"
        assert item["byline"] == "Test byline"
        assert item["price"] == "0.99"
        assert item["url"] == "www.example.com"
        assert item["asin"] == "1"


class TestJsonManager:
    """TODO"""

    def test_get_existing_wishlist_dict(self):
        json_man = JsonManager()
        json_man.wishlist_json_path = Path(
            Path(__file__).parent.absolute(), "wishlist_items.json"
        )

        # Manually json.load the file .get_wishlist_dict should load.
        with open(
            Path(Path(__file__).parent.absolute(), "wishlist_items.json"), "r"
        ) as f:
            wishlist_obj = json.load(f)

        assert json_man.get_wishlist_dict() == wishlist_obj

    def test_get_nonexisting_wishlist_dict(self):
        json_man = JsonManager()
        json_man.wishlist_json_path = Path(
            Path(__file__).parent.absolute(), "does_not_exist.json"
        )

        assert json_man.get_wishlist_dict() == {}

#
#     def test_save_wishlist_json(self):
#         pass
#
#
# # notify.py
#
#
# def test_get_config():
#     pass
#
#
# def test_parse_text_html():
#     pass
#
#
# def test_send_email():
#     pass
#
#
# def test_telegram_message():
#     # NOTE: Might not be an easy way to do this. Might not be worth it anyway.
#     pass


# TODO: Test edge cases. Test the edge cases of a few unusually complex
#  code that you think will probably have errors. Possibly put in another file
#  (advanced tests).

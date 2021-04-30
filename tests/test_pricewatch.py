import json
from pathlib import Path

import pytest

import amazon_wishlist_pricewatch.notify as notify
from amazon_wishlist_pricewatch.pricewatch import PriceWatch, Wishlist, JsonManager


# TODO: May be able to remove config2.json if mock .get_config -> True
#  but would have to supply url in test_parse_wishlist.


TESTS_FOLDER = Path(__file__).parent.resolve()


#################################
# amazon_wishlist_pricewatch.py #
#################################


class TestPriceWatch:
    """Tests for pricewatch.Pricewatch."""

    @pytest.mark.skip(reason="Avoid making network calls during testing.")
    def test_parse_wishlist(self, mock_config):
        pw = PriceWatch()
        # A real web request to tests/config2.json["general"]["wishlist_url"].
        # Decided against mocking out a response due to license issues.
        page = pw.request_page()
        pw.parse_wishlist(page)
        assert not pw.wishlist.is_empty()

    def test_compare_prices(
        self, example_wishlist_items, mock_prev_wishlist, mock_config
    ):
        pw = PriceWatch()
        pw.wishlist = Wishlist(example_wishlist_items)
        cheaper_items = pw.compare_prices()
        # Check the item with a reduced price is added to cheaper_items list.
        assert len(cheaper_items) == 1
        assert cheaper_items[0]["price"] == "6.0"
        # When increased price found check the old, cheaper price is saved instead.
        assert pw.wishlist.get_item_price("2") == "9.15"


class TestWishlist:
    """Tests for pricewatch.Wishlist."""

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
            price="7.0",
            url="/example/path",
            asin="1",
        )
        wishlist.add_item(
            title="Test title 2", price="9.15", url="/another/example/path", asin="2"
        )
        assert len(wishlist) == 2

        item_1 = wishlist["1"]
        assert item_1["title"] == "Test title"
        assert item_1["byline"] == "Test byline"
        assert item_1["price"] == "7.0"
        assert item_1["url"] == "/example/path"
        assert item_1["asin"] == "1"

        item_2 = wishlist["2"]
        assert item_2["title"] == "Test title 2"
        assert item_2["byline"] is None
        assert item_2["price"] == "9.15"
        assert item_2["url"] == "/another/example/path"
        assert item_2["asin"] == "2"

    def test_update_price(self, wishlist_with_two_items: Wishlist):
        assert wishlist_with_two_items["1"]["price"] == "7.0"
        wishlist_with_two_items.update_price(asin="1", price="26.00")
        assert wishlist_with_two_items["1"]["price"] == "26.00"

    def test_get_item_price(self, wishlist_with_two_items: Wishlist):
        price_1 = wishlist_with_two_items.get_item_price("1")
        price_2 = wishlist_with_two_items.get_item_price("2")
        assert price_1 == "7.0"
        assert price_2 == "9.15"

    def test_get_item(self, wishlist_with_two_items: Wishlist):
        item = wishlist_with_two_items.get_item("1")
        assert item["title"] == "Test title"
        assert item["byline"] == "Test byline"
        assert item["price"] == "7.0"
        assert item["url"] == "/example/path"
        assert item["asin"] == "1"


class TestJsonManager:
    """Tests for pricewatch.JsonManager."""

    def test_get_existing_wishlist_dict(self):
        json_man = JsonManager()
        json_man.wishlist_json_path = Path(TESTS_FOLDER, "wishlist_items.json")

        with open(Path(TESTS_FOLDER, "wishlist_items.json"), "r") as f:
            wishlist_obj = json.load(f)

        assert json_man.get_wishlist_dict() == wishlist_obj

    def test_get_nonexisting_wishlist_dict(self):
        json_man = JsonManager()
        json_man.wishlist_json_path = Path(TESTS_FOLDER, "does_not_exist.json")

        assert json_man.get_wishlist_dict() == {}

    def test_save_wishlist_json(self, tmpdir, wishlist_with_two_items):
        truth_wishlist_json = Path(TESTS_FOLDER, "wishlist_items.json")
        temp_wishlist_json = Path(tmpdir, "wishlist_items.json")
        json_man = JsonManager()
        json_man.wishlist_json_path = temp_wishlist_json
        json_man.save_wishlist_json(wishlist_with_two_items)

        with open(temp_wishlist_json, "r") as temp, open(
            truth_wishlist_json, "r"
        ) as truth:
            assert json.load(temp) == json.load(truth)


#############
# notify.py #
#############

def test_send_notification(block_notification_calls, mock_config):
    notify.config = notify.get_config()
    # Type checking error below for wishlist_item_list can be ignored as all
    # calls within send_notification are mocked to return True.
    notify.send_notification(wishlist_item_list="test")  # type: ignore
    notify.send_notification(text="test", html="test")

    with pytest.raises(ValueError):
        notify.send_notification(text="test")
        notify.send_notification()


def test_parse_text_html(mock_config, mock_wishlist_items_list, parsed_text_html):
    notify.config = notify.get_config()
    notify.config["general"]["wishlist_url"] = "https://www.example.com/ex/am/ple"

    text, html = notify.parse_txt_html(mock_wishlist_items_list)
    true_text, true_html = parsed_text_html

    assert text == true_text
    assert html == true_html


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

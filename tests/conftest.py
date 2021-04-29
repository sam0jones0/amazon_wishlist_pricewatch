import json
import logging.handlers
from pathlib import Path

import pytest

import amazon_wishlist_pricewatch.notify as notify
from amazon_wishlist_pricewatch.pricewatch import Wishlist, JsonManager

TESTS_FOLDER = Path(__file__).parent.absolute()


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)


@pytest.fixture()
def mock_prev_wishlist(monkeypatch):
    with open(Path(TESTS_FOLDER, "wishlist_items.json"), "r") as f:
        wishlist_json = json.load(f)

    def mock_wishlist_items(*args, **kwargs):
        return wishlist_json

    monkeypatch.setattr(JsonManager, "get_wishlist_dict", mock_wishlist_items)


@pytest.fixture()
def mock_config(monkeypatch):
    with open(Path(TESTS_FOLDER, "config2.json"), "r") as f:
        config = json.load(f)

    def mock_config(*args, **kwargs):
        return config

    monkeypatch.setattr(notify, "get_config", mock_config)


@pytest.fixture()
def block_notification_calls(monkeypatch):
    def mock_calls(*args, **kwargs):
        return True, True

    monkeypatch.setattr(notify, "parse_txt_html", mock_calls)
    monkeypatch.setattr(notify, "send_email", mock_calls)
    monkeypatch.setattr(notify, "telegram_message", mock_calls)


@pytest.fixture()
def parsed_text_html():
    """Expected output from `notify.parse_txt_html`."""
    with open(Path(TESTS_FOLDER, "parsed_text.txt"), "r") as text_file, open(
        Path(TESTS_FOLDER, "parsed_html.txt"), "r"
    ) as html_file:
        return text_file.read(), html_file.read()


@pytest.fixture()
def example_wishlist_items():
    """Represents what usually populates `amzn_pricewatch.Wishlist.wishlist_dict`."""
    return {
        "1": {
            "title": "Olympia GG925 Cookie Jar with Lid, 3.9 L",
            "byline": None,
            "price": "6.0",
            "url": "/example/path",
            "asin": "1",
        },
        "2": {
            "title": "Oral-B Braun Precision Clean Replacement Rechargeable Toothbrush Heads (2 x Toothbrush Heads)",
            "byline": "Super-fresh clean much brush.",
            "price": "10.15",
            "url": "/another/example/path",
            "asin": "2",
        },
    }


@pytest.fixture()
def wishlist_with_two_items():
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

    return wishlist


@pytest.fixture()
def mock_wishlist_items_list():
    """This represents the list `new_cheaper_items` built in
    `amzn_pricewatch.PriceWatch` which is passed to notify.send_notification`.
    """
    return [
        {
            "title": "Test title",
            "byline": "Test byline",
            "price": "7.0",
            "url": "/example/path",
            "asin": "1",
        },
        {
            "title": "Test title 2",
            "byline": None,
            "price": "9.15",
            "url": "/another/example/path",
            "asin": "2",
        },
    ]

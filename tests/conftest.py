

import pytest
import os
import sys
from pricewatch.amzn_pricewatch import PriceWatch, Wishlist, JsonManager
import pytest
import json
import pricewatch.notify as notify
from pathlib import Path

import pricewatch.logger
import logging.handlers


@pytest.fixture()
def example_wishlist_items():
    return {
        "1": {
            "title": "Olympia GG925 Cookie Jar with Lid, 3.9 L",
            "byline": None,
            "price": "6.0",
            "url": "/dp/B00KQNDJ22/?coliid=IGMMYNR35XB83&colid=SY8C9LJNOM00&psc=1&ref_=lv_vv_lig_dp_it_im",
            "asin": "1",
        },
        "2": {
            "title": "Oral-B Braun Precision Clean Replacement Rechargeable Toothbrush Heads (2 x Toothbrush Heads)",
            "byline": "Super-fresh clean much brush.",
            "price": "10.15",
            "url": "/dp/B01MSJWIM7/?coliid=I35YRVX5OFZF11&colid=SY8C9LJNOM00&psc=1&ref_=lv_vv_lig_dp_it_im",
            "asin": "2",
        },
    }


@pytest.fixture()
def mock_prev_wishlist(monkeypatch):
    with open(Path(Path(__file__).parent.absolute(), "wishlist_items.json"), "r") as f:
        wishlist_json = json.load(f)

    def mock_wishlist_items(*args, **kwargs):
        return wishlist_json

    monkeypatch.setattr(JsonManager, "get_wishlist_dict", mock_wishlist_items)


@pytest.fixture()
def mock_config(monkeypatch):
    with open(Path(Path(__file__).parent.absolute(), "config2.json"), "r") as f:
        config = json.load(f)

    def mock_config(*args, **kwargs):
        return config

    monkeypatch.setattr(notify, "get_config", mock_config)


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)


@pytest.fixture()
def wishlist_with_two_items():
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

    return wishlist


# Could use the following to get the logger (would have to give it name).
# And then could change logging file maybe?
#
# logger = logging.getLogger('mylogger').DoSomethingToLogger()
#
# if os.environ.get('mylogger_level'):
#     logger.setLevel(os.environ.get('mylogger_level'))


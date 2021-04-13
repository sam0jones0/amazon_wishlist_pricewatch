"""TODO"""

from typing import TypedDict, Optional, Dict


class WishlistItem(TypedDict):
    title: str
    byline: Optional[str]
    price: str
    url: str
    asin: str


WishlistDict = Dict[str, WishlistItem]

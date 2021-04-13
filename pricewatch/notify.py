import json
import os
import smtplib
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import (
    List,
    Dict,
    Tuple,
    Optional,
)
from urllib.parse import urlparse

from logger import logger
from my_types import WishlistItem, WishlistDict


def get_config() -> Dict:
    """TODO"""
    with open(
        Path(
            os.path.realpath(sys.path[0]), "config2.json"
        ),  # FIXME: config2 back to config
        "r",
    ) as json_file:
        return json.load(json_file)


config = get_config()


def parse_txt_html(wishlist_item_list: List[WishlistItem]) -> Tuple[str, str]:
    """

    Args:
        wishlist_item_list (list):

    Returns:

    """
    wishlist_domain = urlparse(config["general"]["wishlist_url"]).netloc

    # Using the + and += operators to accumulate a string within a loop can
    # lead to quadratic rather than linear running time. Instead adding each
    # substring to a list and ''.join the list after the loop terminates
    # consistently has amortized-linear run time complexity.
    text_list = []
    html_list = ["<html><body><p>"]
    for item in wishlist_item_list:
        title = item["title"]
        byline = item["byline"]
        url = f"https://{wishlist_domain}{item['url']}"
        price = item["price"]

        text_list.append(f"{title}\n")
        html_list.append(f"{title}<br>")
        if byline:
            text_list.append(f"{byline}\n")
            html_list.append(f"{byline}<br>")
        text_list.append(f"{url}\n")
        html_list.append(f'<a href="{url}">{url}</a><br>')
        text_list.append(f"Price: {price}\n\n")
        html_list.append(f"Price: {price}<br><br>")
        html_list.append("</p></body></html>")

        logger.info(f"Price alert for {title}: {price}.")
    text = "".join(text_list)
    html = "".join(html_list)

    return text, html


def send_email(text: str, html: str) -> None:
    """

    Args:
        text:
        html:

    Returns:

    """
    email_config = config["email"]
    smtp_server = email_config["smtp_server"]
    smtp_port = int(email_config["smtp_port"])
    sending_email = email_config["sending_email"]
    sending_email_pass = email_config["sending_email_pass"]
    recipients = email_config["receiving_emails"]

    message = MIMEMultipart("alternative")
    message["Subject"] = "Amazon Wishlist Price Alert"
    message["From"] = sending_email
    message["To"] = ", ".join(recipients)

    plain_text = MIMEText(text, "plain")
    html_text = MIMEText(html, "html")

    message.attach(plain_text)
    message.attach(html_text)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sending_email, sending_email_pass)
            server.send_message(
                message,
                from_addr=sending_email,
                to_addrs=recipients,
            )
    except smtplib.SMTPException as e:
        logger.exception("Failed to send email.")


def telegram_message(text: str) -> None:
    """TODO"""
    import telegram  # type: ignore

    chat_id = config["telegram"]["chat_id"]
    token = config["telegram"]["token"]
    bot = telegram.Bot(token=token)
    try:
        bot.send_message(chat_id=chat_id, text=text)
    except telegram.error.TelegramError as e:
        logger.exception("Failed to send telegram message.")


def send_notification(
    wishlist_item_list: Optional[List[WishlistItem]] = None,
    text: Optional[str] = None,
    html: Optional[str] = None,
) -> None:
    """TODO"""
    if wishlist_item_list:
        text, html = parse_txt_html(wishlist_item_list)
    else:
        assert text and html, (
            "text and html should be provided if " "wishlist_item_list is not."
        )
    nm = config["general"]["notification_mode"]
    if "1" in nm:
        send_email(text=text, html=html)
    if "2" in nm:
        telegram_message(text)


def failed_request_msg() -> None:
    """TODO"""
    send_notification(
        text="Failed to request your wishlist page. Your IP may be blocked"
        " or the wishlist URL could be incorrect.",
        html="<html><body><p>Failed to request your wishlist page. Your IP may"
        " be blocked or the wishlist URL could be incorrect.</p></body></html>",
    )


def test_notification() -> None:
    """TODO"""
    send_notification(
        text="Test from Amazon wishlist pricewatch.",
        html="<html><body><p>Test from Amazon wishlist pricewatch.</p></body></html>",
    )

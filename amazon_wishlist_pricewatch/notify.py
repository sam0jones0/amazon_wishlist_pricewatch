import json
import smtplib
import ssl
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

if __package__ is None or __package__ == "":
    # Uses current directory visibility when not running as a package.
    from logger import logger
    from my_types import WishlistItem
else:
    # Uses current package visibility when running as a package or with pytest.
    from .logger import logger
    from .my_types import WishlistItem


def get_config() -> Dict:
    """Load config file from disk as python dict and return it. File is
    expected to exist on the same path as this source file.
    """
    with open(
        Path(Path(__file__).parent, "config.json").resolve(),
        "r",
    ) as json_file:
        return json.load(json_file)


def send_notification(
    wishlist_item_list: Optional[List[WishlistItem]] = None,
    text: Optional[str] = None,
    html: Optional[str] = None,
) -> None:
    """Send a notification using the user's specified notification methods.

    This function dispatches notifications to each notification method specified
    by the user in `config.json`. This allows custom text and html (for
    test/failure notifications) or a list of WishlistItem(s) to be provided.

    Args:
        wishlist_item_list: Optional; A list of `WishlistItem` dicts which have
            a new lowest seen price, which is typically returned from
            ``pricewatch.PriceWatch.compare_prices``.
        text: The plain-text string to be sent. ASCII only.
        html: HTML formatted string to be sent.

    Returns:
        None

    Raises:
        ValueError: Insufficient number or type of arguments provided.
    """
    if wishlist_item_list:
        text, html = parse_txt_html(wishlist_item_list)
    elif not (text and html):
        raise ValueError(
            "text and html should be provided if wishlist_item_list is not."
        )
    nm = config["general"]["notification_mode"]
    if "1" in nm:
        send_email(text=text, html=html)
    if "2" in nm:
        telegram_message(text)


def parse_txt_html(wishlist_item_list: List[WishlistItem]) -> Tuple[str, str]:
    """Parse list of `WishlistItem(s)` to text and html strings.

    This function takes in a list of WishlistItems and returns the key
    product information formatted as plain-text and html strings, formatted
    to be easily sent as a notification to the user.

    Args:
        wishlist_item_list (list): A list of `WishlistItem` dicts which have a new
                lowest seen price, which is typically returned from
                ``pricewatch.PriceWatch.compare_prices``.

    Returns: A tuple containing (text, html) strings of key product information.
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
    """Send an email notification to the user.

    A connection with the `config` specified SMTP server is established over
    SMTP_SLL and a MimeMultipart email is sent to all email addresses listed in
    the `config` file.

    Args:
        text: The plain-text string to be emailed.
        html: HTML formatted string to be emailed.

    Returns:
        None

    Raises:
        smtplib.SMTPException: Base exception class for smtplib.
        smtplib.SMTPAuthenticationError: Most likely the wrong user/pass supplied.
        smtplib.SMTPResponseException: Connection failed with the sending server.
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

    # The last part of a multipart message, in this case the HTML message, is
    # best and preferred (RFC 2046).
    message.attach(plain_text)
    message.attach(html_text)

    # The default context of ssl validates the host name and its certificates
    # and optimizes the security of the connection.
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
        logger.exception("Failed to send email. Check config.")


def telegram_message(text: str) -> None:
    """Send a plain-text telegram message.

    Args:
        text: The text to be sent.

    Returns:
        None

    Raises:
        telegram.error.TelegramError: Base telegram exception.
        telegram.error.NetworkError: Base network error exception.
        telegram.error.InvalidToken: Invalid secret token provided.
        telegram.error.ChatMigrated: `chat_id` incorrect / moved.
    """
    import telegram  # type: ignore

    chat_id = config["telegram"]["chat_id"]
    token = config["telegram"]["token"]
    bot = telegram.Bot(token=token)
    try:
        bot.send_message(chat_id=chat_id, text=text)
    except telegram.error.TelegramError as e:
        logger.exception("Failed to send telegram message. Check config.")


def failed_request_msg() -> None:
    """Send a notification that a web request to Amazon has failed."""
    send_notification(
        text="Failed to request your wishlist page. Your IP may be blocked"
        " or the wishlist URL could be incorrect.",
        html="<html><body><p>Failed to request your wishlist page. Your IP may"
        " be blocked or the wishlist URL could be incorrect.</p></body></html>",
    )


def test_notification() -> None:
    """Send a message testing whether notification methods are correctly configured."""
    send_notification(
        text="Test from Amazon wishlist amazon_wishlist_pricewatch.",
        html="<html><body><p>Test from Amazon wishlist amazon_wishlist_pricewatch.</p></body></html>",
    )


if __name__ == "__main__":
    config = get_config()

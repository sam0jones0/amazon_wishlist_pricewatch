<p align="center">
  <img src="https://github.com/sam0jones0/amazon_wishlist_pricewatch/blob/master/blob/pricewatch_200.png">
</p>

<h1 align="center">Amazon Wishlist Pricewatch</h1>

<p align="center">
  <a href="https://github.com/sam0jones0/amazon_wishlist_pricewatch/blob/master/LICENSE.txt">
    <img src="https://img.shields.io/pypi/l/amazon-wishlist-pricewatch"
      alt="MIT License" />
  </a>
  <a href="">
    <img src="https://img.shields.io/pypi/v/amazon-wishlist-pricewatch"
      alt="PyPI" />
  </a>
  <a href="">
    <img src="https://img.shields.io/pypi/pyversions/amazon-wishlist-pricewatch"
      alt="PyPI" />
  </a>
</p>

<p align="center"><i>Periodically check your public Amazon wishlist for price reductions.</i></p>

This package will send you a notification (SMTP email and/or telegram) each time a product on your **publicly available** wishlist reaches a new lowest price. Price still not low enough? You'll only receive another notification for the same product when the price drops further.

Pip install the package, fill in the configuration file and schedule to run with your preferred task scheduler. E.g. Windows Task Scheduler / launchd (Mac OS) / cron (Mac OS / Unix).

Uses the wonderful `requests` and `BeautifulSoup4`. No need for the overhead of a headless browser as all data can be gathered from the plain html.

## Table of Contents


  * [How It Works](#how-it-works)
  * [Getting Started](#getting-started)
    + [Prerequisites](#prerequisites)
    + [Installation](#installation)
    + [Set Configuration](#set-configuration)
    + [Test Notifications](#test-notifications)
    + [Set Running Schedule](#set-running-schedule)
      - [Windows](#windows)
      - [Mac OS](#mac-os)
      - [Unix/Linux](#unix-linux)
  * [Config File Documentation](#config-file-documentation)
    + [Notification Mode](#notification-mode)
    + [Send Test Notification](#send-test-notification)
    + [Using Gmail](#using-gmail)
    + [Using Telegram](#using-telegram)
    + [User Agent](#user-agent)
  * [Questions, Suggestions and Bugs](#questions--suggestions-and-bugs)
  * [Contributing / Development](#contributing---development)
  * [License](#license)

## How It Works

Once installed and configured, each run of `pricewatch` downloads and stores your wishlist as JSON and does price comparisons against items seen in previous runs. When a new lowest price for a product is seen you receive a notification, and the new price is saved to JSON for future runs.

Schedule the script to run as often as you like with Task Scheduler/launchd/cron, and you're good to go.  

## Getting Started

### Prerequisites

Python >=3.6

### Installation

Install with pip (recommended):

```console 
  pip install amazon-wishlist-pricewatch
  pricewatch
```

Or clone the git repo:

```console 
  git clone https://github.com/sam0jones0/amazon_wishlist_pricewatch.git
  cd amazon_wishlist_pricewatch
  pip install -r requirements.txt
  cd ./amazon_wishlist_pricewatch
  python3 ./pricewatch.py
```

(Optional) If you want telegram notifications:
```console 
  pip install python-telegram-bot
```


### Set Configuration

Fill in the config file located at `amazon_wishlist_pricewatch/config.json`

If you can't find it enter `pricewatch` (or `python3 ./pricewatch.py` if you cloned the repo) into your console. Location of the file will be printed.

Detailed config file documentation [here](#Config-File-Documentation).

### Test Notifications

In `config.json` Set `send_test_notification` to "1" and run `pricewatch`. A test notification(s) should be sent and pricewatch will exit. Remember to set back to "0" once you're done.


### Set Running Schedule 

You can use any task scheduler you like to run `pricewatch` / `pricewatch.py` Here's a few suggestions.

#### Windows

I recommend using "Windows Task Scheduler". You can use the GUI or for e.g. to create a task that runs once each time the system boots enter the following into an elevated (Run as Administrator) cmd.exe/Powershell.
```console 
  schtasks /create /tn "Amazon Wishlist Pricewatch" /tr "C:\Path\To\Your\Python\exe\python.exe D:\Path\To\amazon-wishlist-pricewatch\amazon_wishlist_pricewatch\pricewatch.py" /sc onstart /RU WindowsUserName /RP WindowsPassword
```

More examples and guidance on setting different schedules [here](https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create#to-schedule-a-task-to-run-every-time-the-system-starts)

#### Mac OS

You can use cron, launchd, automator or any other tool. For e.g. to use launchd to create a task that runs once each time the system boots create
the following file `~/Library/LaunchAgents/local.amazonwishlistpricewatch.pricewatch.plist` and paste in:

```xml 
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>local.amazonwishlistpricewatch.pricewatch.plist</string>
	<key>ProgramArguments</key>
	<array>
		<string>/usr/local/bin/python3</string>
		<string>/path/to/amazon_wishlist_pricewatch/pricewatch.py</string>
	</array>
	<key>RunAtLoad</key>
	<true/>
</dict>
</plist>
```
More information on launchd [here](https://www.launchd.info/)

#### Unix/Linux

I assume you'll be fine! Perhaps use cron.


## Config File Documentation

Annotated example config file contents:

```json 
  {
  "general": {
    "notification_mode": "12 (1 for email + 2 for telegram)",
    "wishlist_url": "https://www.amazon.co.uk/hz/wishlist/ls/S0M3C0D3",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
    "send_test_notification": "0"
  },
  "email": {
    "smtp_server": "YOUR-SMTP-SERVER (e.g. smtp.gmail.com)",
    "smtp_port": "YOUR-SMTP-SSL-PORT (e.g. 465 for gmail)",
    "sending_email": "SENDING EMAIL ADDRESS (e.g. example@gmail.com)",
    "sending_email_pass": "SENDING EMAIL ADDRESS PASSWORD",
    "receiving_emails": [
      "person1@gmail.com",
      "person2@optional.com"
    ]
  },
  "telegram": {
    "chat_id": "1234567890",
    "token": "9876543210:HFusj898IEXAMPLEHDKEIIE83exampleuUJ"
  }
}
```

### Notification Mode

- "1" for email.
- "2" for Telegram.
- "12" for email and Telegram.


### Send Test Notification

Set to "1" to have the script attempt to send a notification to each method specified and then exit. Change back to "0" to have the script run normally.

### Using Gmail

If you have 2FA enabled you can [create an app password](https://support.google.com/accounts/answer/185833?hl=en) and put that in `sending_email_pass`.

Not recommended, but you can use your usual Google account password if you [enable "Less secure app access"](https://support.google.com/accounts/answer/6010255?hl=en). I'd recommend creating a new Gmail account if you do this.

### Using Telegram

1. Download / install Telegram.
2. Create a bot with [Telegram's BotFather bot](https://core.telegram.org/bots#6-botfather) and keep a note of the token.
2. Create a new group where you will receive notifications and add your new bot to it.
3. Send at least one message to the group.
4. Visit https://api.telegram.org/botXXX:YYYYY/getUpdates replacing XXX:YYYYY with your token from step 2 and take a note of the `chat` `id`.
5. Add your chat id and token to config.json.

### User Agent

You don't need to change this, but you can. Enter "my user agent" into Google to see your browser's user agent.

## Questions, Suggestions and Bugs

Feel free to open an issue [here](https://github.com/sam0jones0/amazon_wishlist_pricewatch/issues). 

## Contributing / Development

Contributions welcome. 

Clone the repo and `pip install -r requirements_dev.txt` in a new virtual environment.

Uses pytest for testing, Mypy for type checking, and black for code formatting.

## License

[MIT License](./LICENSE.txt). Sam Jones

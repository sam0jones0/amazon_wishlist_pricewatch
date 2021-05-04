
# Amazon Wishlist Pricewatch

> Periodically check your public Amazon wishlist for price reductions. 

This package will send you a notification (SMTP email and/or telegram) each time a product on your **publicly available** wishlist reaches a new lowest price. Price still not low enough? You'll only receive another notification for the same product when the price drops further.

Pip install the package, fill in the configuration file and schedule to run with your preferred task scheduler. E.g. Windows Task Scheduler / launchd (Mac OS) / cron (Mac OS / Unix).

Uses `requests` and `BeautifulSoup4`. No need for the overhead of a headless browser as all data can be gathered from the plain html.

## How It Works

Once installed and configured, each time you run `pricewatch` your wishlist is downloaded and product data is parsed out for comparison with price data from previous runs. When a new lowest price for a product is seen you receive a notification and the new price is saved to json for future runs.

Schedule the script to run as often as you like with Task Scheduler/launchd/cron and you're good to go.  

## Getting Started

### Prerequisites

Python >=3.6

### Installation

Install with pip (recommended):

```console 
  pip install amazon-wishlist-pricewatch
  pip install python-telegram-bot
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

TODO: Link Detailed config file documentation below.

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

I assume you'll be fine. Perhaps use cron.

## Config File Documentation

Example config file contents:

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

If you have 2FA enabled you can [create an app password](https://support.google.com/accounts/answer/185833?hl=en) and put that in the `sending_email_pass`.

Not recommended, but you can use your usual Google account password if you [enable "Less secure app access"](https://support.google.com/accounts/answer/6010255?hl=en). I'd recommend creating a new Gmail account if you do this.

### Using Telegram

1. Download / install Telegram.
2. Create a bot with [Telegram's BotFather bot](https://core.telegram.org/bots#6-botfather) and keep a note of the token.
2. Create a new group where you will receive notifications and add your new bot to it.
3. Send at least one message to the group.
4. Visit https://api.telegram.org/botXXX:YYYYY/getUpdates replacing XXX:YYYYY with your token from step 2 and take a note of the `chat` `id`.
5. Add your chat id and token to config.json.

### User Agent

You don't need to change this. But you can. Enter "my user agent" into Google to see your browser's user agent.

#
#
#
#
#
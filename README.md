# neuro-schedule

Uses a discord bot to get the info of neuro's latest schedule and then puts it in a shared calendar

## Setup

Clone the github repository wherever you want to run the bot.

Copy `.env.example` to `.env`.

### Discord bot with the following permissions

- Read Message History
- View Channels

Following scopes:

- bot

Message Content Intent _activated_

Take the bot token and put it in

### Google Calendar

Create a new calendar and copy the calendar ID into the right environment variable `.env`
Check make available to public

Google Cloud Platform:

- Create a new project
- Activate the Google Calendar API
- Create a service account
    - Create a key in JSON format and put it in the root of the project and rename it to `service_account.json`

## Server setup

Python 3.10 or higher

### create a virtual environment and install the requirements

To create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:
linux/macOS:

```bash
source venv/bin/activate
```

windows:

```
venv\Scripts\activate
```

Install the requirements:
with pip:

```bash
python -m pip install -r requirements.txt
```

Make sure to have the ENV variables set in the `.env` file.
And the service account JSON file in the root of the project.

You can now run the bot with:

```bash
python discordtocalendar.py
```

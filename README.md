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

Clone the github repository wherever you want to run the bot.
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

## Dockerfile Setup
To install neuro-schedule using the provided dockerfile

Make sure you have the service_account.json file in the root and a filled .env file

```bash
docker run --rm -t --env-file .env -v "$(pwd)/service_account.json:/app/service_account.json:ro" roxblox3/neuro-schedule python -u discordtocalendar.py
```

You can also run the app using the docker compose with :


```bash
docker compose up app
```

## Test Dockerfile Setup
To install neuro-schedule using the provided dockerfile

Make sure you have the service_account.json file in the root and a filled .env file

```bash
docker run --rm -t -v "$(pwd)/service_account.json:/tmp/fake_credentials.json:ro" -e CALENDAR_ID=test_calendar -e DISCORD_BOT_TOKEN=test_token -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/fake_credentials.json -e ENABLE_LOGS=false roxblox3/neuro-schedule:test-latest python -m pytest -q
```

You can also run the app using the docker compose with :

```bash
docker compose up --rm tests
```

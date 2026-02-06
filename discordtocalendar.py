import os
import re
import logging
from typing import Optional, Tuple
import discord
from datetime import datetime, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dateutil import parser

load_dotenv()

ENABLE_LOGS = os.getenv("ENABLE_LOGS", "0").lower() in ("1", "true", "yes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if ENABLE_LOGS:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    logger = logging.getLogger(__name__)
else:
    # Disable only this module's logger when logging is off
    logger = logging.getLogger(__name__)
    logger.disabled = True

class CalendarDiscordClient(discord.Client):
    def __init__(self, *, google_service=None, **kwargs):
        super().__init__(**kwargs)
        self.google_service = google_service

    async def on_message(self, message):
        if not message.content:
            return
        logger.debug("New message: %s", message.content)
        service = self.google_service
        if service is None:
            logger.warning("Google Calendar service not initialized.")
            return
        try:
            lines = message.content.strip().split("\n")
            for line in lines:
                split_message, start_timestamp, end_timestamp = parse_message_line(line)
                if not split_message or not start_timestamp or not end_timestamp:
                    continue
                if not event_exists(service, split_message, start_timestamp, end_timestamp):
                    try:
                        insert_event(service, split_message, start_timestamp, end_timestamp)
                        logger.info("Inserting event: %s", split_message)
                    except Exception as e:
                        logger.exception("Failed to insert event: %s", e)
        except Exception as e:
            logger.exception("Failed to parse or create event: %s", e)

# environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CALENDAR_ID = os.getenv("CALENDAR_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

DEFAULT_DESCRIPTION = "No description provided"
EVENT_DURATION_SECONDS = 9000

# patterns for matching timestamps in messages
online_timestamp_pattern = re.compile(r"<t:(\d+):F>")
emoji_pattern = re.compile(r"<a?:[A-Za-z0-9_]+:\d{15,22}>")

def authenticate_google_calendar() -> service_account.Credentials:
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES
    )
    return creds


def insert_event(
    service, message: str, start_timestamp: int, end_timestamp: int
) -> None:
    event = {
        "summary": message,
        "start": {
            "dateTime": datetime.fromtimestamp(
                start_timestamp, tz=timezone.utc
            ).isoformat()
        },
        "end": {
            "dateTime": datetime.fromtimestamp(
                end_timestamp, tz=timezone.utc
            ).isoformat()
        },
    }
    logger.debug("Event payload: %s", event)
    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()


def event_exists(service, summary: str, start_timestamp: int, end_timestamp: int) -> bool:
    # Check if an event with the same summary already exists at the same time window
    start_utc = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
    end_utc = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
    events_result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=start_utc.isoformat(),
            timeMax=end_utc.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    for event in events:
        if event.get("summary") != summary:
            continue
        start_dt = event.get("start", {}).get("dateTime")
        end_dt = event.get("end", {}).get("dateTime")
        event_start = parser.isoparse(start_dt) if start_dt else None
        event_end = parser.isoparse(end_dt) if end_dt else None

        if event_start == start_utc and event_end == end_utc:
            return True
    return False


def sanitize_description(text: str) -> str:
    cleaned = emoji_pattern.sub("", text).strip()
    return cleaned or DEFAULT_DESCRIPTION


def parse_message_line(line: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    match_online = online_timestamp_pattern.search(line)
    if not match_online:
        return None, None, None

    start_timestamp = int(match_online.group(1))
    end_timestamp = start_timestamp + EVENT_DURATION_SECONDS
    parts = line.split(" - ", 2)
    if len(parts) == 3:
        split_message = sanitize_description(parts[2])
    else:
        split_message = DEFAULT_DESCRIPTION

    return split_message, start_timestamp, end_timestamp


def main():
    if not CALENDAR_ID:
        logger.error("CALENDAR_ID environment variable not set.")
        return
    if not GOOGLE_APPLICATION_CREDENTIALS:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
        return
    if DISCORD_BOT_TOKEN is None:
        logger.error("DISCORD_BOT_TOKEN environment variable not set.")
        return

    intents = discord.Intents.default()
    intents.message_content = True

    try:
        logger.info("Authenticating with Google Calendar API...")
        creds = authenticate_google_calendar()
        service = build("calendar", "v3", credentials=creds)
        client = CalendarDiscordClient(google_service=service, intents=intents)
        logger.info("Google Calendar API service initialized.")
    except Exception as e:
        logger.exception("Failed to authenticate with Google Calendar API: %s", e)
        return

    try:
        if DISCORD_BOT_TOKEN is not None:
            client.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.exception("Failed to run bot: %s", e)


if __name__ == "__main__":
    main()

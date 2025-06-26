import os
import re
import discord
from datetime import datetime, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dateutil import parser

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True


class CalendarDiscordClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.google_service = None


client = CalendarDiscordClient(intents=intents)

# environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CALENDAR_ID = os.getenv("CALENDAR_ID")
if not CALENDAR_ID:
    raise ValueError("CALENDAR_ID environment variable not set.")

# patterns for matching timestamps in messages
online_timestamp_pattern = re.compile(r"<t:(\d+):F>")


def authenticate_google_calendar():
    creds = service_account.Credentials.from_service_account_file(
        "service_account.json", scopes=SCOPES
    )
    return creds


def insert_event(service, message, start_timestamp, end_timestamp):
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
    print(event)
    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()


def event_exists(service, start_timestamp, end_timestamp):
    # Check if an event with the same summary already exists
    events_result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=datetime.fromtimestamp(
                start_timestamp, tz=timezone.utc
            ).isoformat(),
            timeMax=datetime.fromtimestamp(end_timestamp, tz=timezone.utc).isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    for event in events:
        start_dt = event.get("start", {}).get("dateTime")
        end_dt = event.get("end", {}).get("dateTime")
        event_start = parser.isoparse(start_dt) if start_dt else None
        event_end = parser.isoparse(end_dt) if end_dt else None

        start_utc = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
        end_utc = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
        if event_start == start_utc and event_end == end_utc:
            return True
    return False


def parse_message_line(line):
    match_online = online_timestamp_pattern.match(line)
    if match_online:
        start_timestamp = int(match_online.group(1))
        end_timestamp = start_timestamp + 9000
        parts = line.split(" - ")
        if len(parts) >= 3:
            split_message = " - ".join(parts[2:])
        else:
            split_message = "No description provided"
        return split_message, start_timestamp, end_timestamp
    return None, None, None


def main():
    try:
        print("Authenticating with Google Calendar API...")
        creds = authenticate_google_calendar()
        service = build("calendar", "v3", credentials=creds)
        client.google_service = service
        print("Google Calendar API service initialized.")
    except Exception as e:
        print(f"Failed to authenticate with Google Calendar API: {e}")

    try:
        if DISCORD_BOT_TOKEN is not None:
            client.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Failed to run bot : {e}")


@client.event
async def on_message(message):
    print(f"New message: {message.content}")
    service = getattr(client, "google_service", None)
    if service is None:
        print("Google Calendar service not initialized.")
        return
    try:
        lines = message.content.strip().split("\n")
        for line in lines:
            split_message, start_timestamp, end_timestamp = parse_message_line(line)
            if not split_message or not start_timestamp or not end_timestamp:
                continue
            if not event_exists(service, start_timestamp, end_timestamp):
                try:
                    insert_event(service, split_message, start_timestamp, end_timestamp)
                    print(f"Inserting event: {split_message}")
                except Exception as e:
                    print(f"Failed to insert event: {e}")
    except Exception as e:
        print(f"Failed to parse or create event: {e}")


if __name__ == "__main__":
    main()

import os
import re
import discord
from datetime import datetime, timezone, time
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CALENDAR_ID = os.getenv("CALENDAR_ID")

# patterns for matching timestamps in messages
offline_timestamp_pattern = r"<t:(\d+):D>"
online_timestamp_pattern = r"<t:(\d+):F>"


def authenticate_google_calendar():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no valid credentials, refresh or obtain new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


try:
    print("Authenticating with Google Calendar API...")
    creds = authenticate_google_calendar()
    service = build("calendar", "v3", credentials=creds)
    print("Google Calendar API service initialized.")
except Exception as e:
    print(f"Failed to authenticate with Google Calendar API: {e}")


def insert_event(message, start_timestamp, end_timestamp):
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


@client.event
async def on_message(message):
    if DISCORD_CHANNEL_ID is not None and message.channel.id == int(DISCORD_CHANNEL_ID):
        print(f"New message: {message.content}")
        try:
            lines = message.content.strip().split("\n")
            for line in lines:
                match_offline = re.match(offline_timestamp_pattern, line)
                match_online = re.match(online_timestamp_pattern, line)
                if match_offline:
                    start_timestamp = int(match_offline.group(1))
                    end_timestamp = start_timestamp + 7200
                    message = line.split(" - ", 1)[1]
                    insert_event(message, start_timestamp, end_timestamp)
                if match_online:
                    start_timestamp = int(match_online.group(1))
                    end_timestamp = start_timestamp + 9000
                    message = " - ".join(line.split(" - ")[2:])
                    insert_event(message, start_timestamp, end_timestamp)
        except Exception as e:
            print(f"Failed to parse or create event: {e}")


try:
    if DISCORD_BOT_TOKEN is not None:
        client.run(DISCORD_BOT_TOKEN)
except Exception as e:
    print(f"Failed to run bot : {e}")

# async def on_ready():
#     print(f"Logged in as {client.user}")
#     channel = client.get_channel(DISCORD_CHANNEL_ID)
#     if channel:
#         messages = [message async for message in channel.history(limit=1)]
#         if messages:
#             latest_message=messages[0]
#             print(f"Latest message in channel: {latest_message.content}")

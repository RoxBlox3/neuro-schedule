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

# Discord bot token and channel ID
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CALENDAR_ID = os.getenv("CALENDAR_ID")

# flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
# creds = InstalledAppFlow.from_client_secrets_file(
#     "credentials.json", SCOPES
# ).run_local_server(port=0)
# service = build("calendar", "v3", credentials=creds)

offline_timestamp_pattern = r"<t:(\d+):D>"
online_timestamp_pattern = r"<t:(\d+):F>"


def authenticate_google_calendar():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)
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


@client.event
async def on_message(message):
    if DISCORD_CHANNEL_ID is not None and message.channel.id == int(DISCORD_CHANNEL_ID):
        print(f"New message: {message.content}")
        try:
            lines = message.content.strip().split("\n")
            removed_empty_line = []
            for full_line in lines:
                # INFO: Skip lines that are empty or contain fanart of the week and ping
                if (
                    full_line != ""
                    and not full_line.startswith("-# Fanart of the week by ")
                    and not full_line.endswith(":neuroPing:")
                ):
                    removed_empty_line.append(full_line)
            for line in removed_empty_line:
                match = re.match(offline_timestamp_pattern, line)
                if match:
                    timestamp = int(match.group(1))
                    message = line.split(" - ", 1)[1]
                    event = {
                        "summary": message,
                        "start": {
                            "dateTime": datetime.fromtimestamp(
                                timestamp, tz=timezone.utc
                            ).isoformat()
                        },
                        "end": {
                            "dateTime": datetime.fromtimestamp(
                                timestamp + 7200, tz=timezone.utc
                            ).isoformat()
                        },
                    }
                    print(timestamp)
                    service.events().insert(
                        calendarId=CALENDAR_ID, body=event
                    ).execute()
                    # TODO: Parse the data
            print(removed_empty_line)
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

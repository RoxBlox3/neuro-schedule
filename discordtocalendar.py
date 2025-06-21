import os
import re

import discord
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

# Discord bot token and channel ID
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")


@client.event
async def on_message(message):
    if DISCORD_CHANNEL_ID is not None and message.channel.id == int(DISCORD_CHANNEL_ID):
        print(f"New message: {message.content}")
        try:
            lines = message.content.strip().split("\n")
            removed_empty_line = []
            for line in lines:
                if line != "" and not line.startswith("Fanart of the week by "):
                    removed_empty_line.append(line)

            print(removed_empty_line)
            # TODO: Add splitting message into variables and adding them to google calendar
            pass
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

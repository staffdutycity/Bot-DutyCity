import os
import asyncio
import requests
import discord
from discord.ext import tasks

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
VOICE_CHANNEL_ID = int(os.environ.get("VOICE_CHANNEL_ID", "0"))
MINECRAFT_SERVER_IP = os.environ.get("MINECRAFT_SERVER_IP", "")

MCSRVSTAT_URL = f"https://api.mcsrvstat.us/2/{MINECRAFT_SERVER_IP}"
UPDATE_INTERVAL_MINUTES = 5

intents = discord.Intents.default()
bot = discord.Client(intents=intents)


def fetch_server_status():
    try:
        response = requests.get(MCSRVSTAT_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("online"):
            online = data.get("players", {}).get("online", 0)
            max_players = data.get("players", {}).get("max", 0)
            return True, online, max_players
        return False, 0, 0
    except Exception as e:
        print(f"[ERROR] Failed to fetch server status: {e}")
        return None, 0, 0


@tasks.loop(minutes=UPDATE_INTERVAL_MINUTES)
async def update_channel_name():
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel is None:
        print(f"[ERROR] Could not find voice channel with ID {VOICE_CHANNEL_ID}")
        return

    online, player_count, max_players = fetch_server_status()

    if online is None:
        new_name = "🔴 MC: API Error"
    elif online:
        new_name = f"🟢 MC: {player_count}/{max_players} online"
    else:
        new_name = "🔴 MC: Offline"

    try:
        await channel.edit(name=new_name)
        print(f"[INFO] Updated channel name to: {new_name}")
    except discord.Forbidden:
        print("[ERROR] Missing permission to edit the voice channel name.")
    except Exception as e:
        print(f"[ERROR] Failed to update channel name: {e}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Tracking Minecraft server: {MINECRAFT_SERVER_IP}")
    print(f"Updating voice channel ID: {VOICE_CHANNEL_ID} every {UPDATE_INTERVAL_MINUTES} minutes")
    print("------")
    update_channel_name.start()


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN secret is not set.")
    if not VOICE_CHANNEL_ID:
        raise ValueError("VOICE_CHANNEL_ID environment variable is not set.")
    if not MINECRAFT_SERVER_IP:
        raise ValueError("MINECRAFT_SERVER_IP environment variable is not set.")

    bot.run(DISCORD_TOKEN)

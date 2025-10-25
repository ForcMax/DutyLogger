# bot.py
import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime, timezone, timedelta
import os

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

def now_malaysia():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz)

def format_duration(minutes: float) -> str:
    if minutes < 1:
        seconds = int(minutes * 60)
        return f"{seconds} seconds"
    elif minutes < 60:
        return f"{minutes:.2f} minutes"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if mins == 0:
            return f"{hours} hours"
        return f"{hours} hours {mins} minutes"

def minutes_between(start_str: str, end_str: str) -> float:
    start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
    diff = end - start
    return diff.total_seconds() / 60.0

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user} (id: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print("Sync error:", e)

@bot.tree.command(name="onduty", description="Start your duty session.")
async def onduty(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    data = load_data()
    user = data.get(user_id, {"overall_minutes": 0.0, "current_start": None})

    if user.get("current_start"):
        await interaction.followup.send("You are already ON DUTY — use /offduty when you finish.", ephemeral=True)
        return

    start_time = now_malaysia().strftime("%Y-%m-%d %H:%M:%S")
    user["current_start"] = start_time
    data[user_id] = user
    save_data(data)

    embed = discord.Embed(title="Duty Started", color=0x00AA00)
    embed.add_field(name="User", value=interaction.user.name, inline=False)
    embed.add_field(name="Start Time", value=start_time, inline=False)
    embed.set_footer(text="Have a productive duty session!")
    await interaction.followup.send(embed=embed, ephemeral=False)

@bot.tree.command(name="offduty", description="End your current duty session.")
async def offduty(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    data = load_data()
    user = data.get(user_id)

    if not user or not user.get("current_start"):
        await interaction.followup.send("You are not ON DUTY right now.", ephemeral=True)
        return

    start_time = user["current_start"]
    end_time = now_malaysia().strftime("%Y-%m-%d %H:%M:%S")

    session_minutes = minutes_between(start_time, end_time)
    overall = float(user.get("overall_minutes", 0.0)) + session_minutes

    user["current_start"] = None
    user["overall_minutes"] = round(overall, 2)
    data[user_id] = user
    save_data(data)

    embed = discord.Embed(title="Duty Ended", color=0xDD3333)
    embed.add_field(name="User", value=interaction.user.name, inline=False)
    embed.add_field(name="Session Duty Time", value=format_duration(session_minutes), inline=False)
    embed.add_field(name="Overall Duty Time", value=format_duration(user['overall_minutes']), inline=False)
    embed.add_field(name="End Time", value=end_time, inline=False)
    embed.set_footer(text="Good job! Duty session has been logged.")
    await interaction.followup.send(embed=embed, ephemeral=False)

@bot.tree.command(name="dutystatus", description="Check your current duty status.")
async def dutystatus(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    data = load_data()
    user = data.get(user_id, {"overall_minutes": 0.0, "current_start": None})
    status = "ON DUTY" if user.get("current_start") else "Not on duty"

    current = user.get("current_start") or "-"
    overall = format_duration(float(user.get("overall_minutes", 0.0)))

    embed = discord.Embed(title="Duty Status", color=0x007BFF)
    embed.add_field(name="Status", value=status, inline=False)
    embed.add_field(name="Current Start", value=current, inline=False)
    embed.add_field(name="Total Duty Time", value=overall, inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)

if __name__ == "__main__":
    token = os.environ.get("MTQzMTQzOTA4NTY2MjI0MDk2OQ.GBkJqx.x3f48PT6QP_s4FPC0V-mc8NGEsl9iKiwdSjp74")
    if not token:
        print("Please set your DISCORD_TOKEN as an environment variable.")
    else:
        bot.run(token)






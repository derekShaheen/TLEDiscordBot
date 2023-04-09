# Standard library imports
import os
from datetime import datetime

# Third-party library imports
import discord
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import requests
import yaml
from matplotlib.ticker import MaxNLocator

# Local imports
from config import DEVELOPER_ID, SERVER_TIMEZONE, GITHUB_TOKEN


def pluralize(count, singular, plural):
    return plural if count > 1 else singular


def get_member_by_name(guild, name):
    """Get a member by name."""
    for member in guild.members:
        if member.name == name:
            return member
    return None


def get_member_by_id(guild, id):
    """Get a member by ID."""
    for member in guild.members:
        if member.id == id:
            return member
    return None


def get_channel_by_name(guild, name):
    """Get a channel by name."""
    for channel in guild.channels:
        if channel.name == name:
            return channel
    return None


def get_channel_by_id(guild, id):
    """Get a channel by ID."""
    for channel in guild.channels:
        if channel.id == id:
            return channel
    return None


def get_role_by_name(guild, name):
    """Get a role by name."""
    for role in guild.roles:
        if role.name == name:
            return role
    return None


def get_role_by_id(guild, id):
    """Get a role by ID."""
    for role in guild.roles:
        if role.id == id:
            return role
    return None


async def find_user_guild(client, user_id: int):
    """Find the guild(s) a user is associated with."""
    associated_guilds = []

    for guild in client.guilds:
        member = guild.get_member(user_id)
        if member:
            associated_guilds.append(guild)

    return associated_guilds


async def create_game_room(guild, category, name):
    return await guild.create_voice_channel("Game Room " + name, category=category)


def is_game_room_channel(channel, category_name):
    return channel.name.startswith("Game Room ") and channel.category and channel.category.name == category_name


def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def user_list(channel):
    if not channel.members:
        return "No users"
    return ", ".join([member.mention for member in channel.members])


def load_config(guild_id):
    config_path = f'guilds/{guild_id}/config.yml'
    default_config = {'log_channel_name': 'server_logs',
                      'logging_enabled': False}

    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    else:
        # Create the config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Create the config file with default values
        with open(config_path, 'w') as file:
            yaml.safe_dump(default_config, file)

        return default_config


def save_config(guild_id, config):
    config_path = f'guilds/{guild_id}/config.yml'

    with open(config_path, 'w') as file:
        yaml.safe_dump(config, file)


async def send_embed(recipient, title, description, color, url=None, fields=None, file=None, thumbnail_url=None):
    embed = discord.Embed(
        title=title, description=description, color=color, url=url)
    embed.timestamp = discord.utils.utcnow()

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

    if file:
        await recipient.send(embed=embed, file=file)
    else:
        await recipient.send(embed=embed)


def manage_voice_activity(guild_id: int, user_id: int = None, add_user: bool = False):
    guild_dir = f'guilds/{guild_id}'
    voice_activity_file = f'{guild_dir}/voice_activity.yml'

    # Create the guild directory if it doesn't exist
    os.makedirs(guild_dir, exist_ok=True)

    # Load existing voice_activity data from the YAML file, if it exists
    if os.path.exists(voice_activity_file):
        with open(voice_activity_file, 'r') as file:
            voice_activity_data = yaml.safe_load(file)
            if voice_activity_data is None:
                voice_activity_data = set()
            else:
                voice_activity_data = set(voice_activity_data)
    else:
        voice_activity_data = set()

    if add_user and user_id:
        # Add the user ID to voice_activity_data
        voice_activity_data.add(user_id)

        # Save updated voice_activity_data to the YAML file
        with open(voice_activity_file, 'w') as file:
            yaml.safe_dump(list(voice_activity_data), file)
    else:
        return list(voice_activity_data)


def clear_voice_activity(guild_id: int):
    guild_dir = f'guilds/{guild_id}'
    voice_activity_file = f'{guild_dir}/voice_activity.yml'

    # Create the guild directory if it doesn't exist
    os.makedirs(guild_dir, exist_ok=True)

    # Clear the voice_activity data
    voice_activity_data = set()

    # Save the cleared voice_activity_data to the YAML file
    with open(voice_activity_file, 'w') as file:
        yaml.safe_dump(list(voice_activity_data), file)


async def send_developer_message(client, title, description, color, file=None, fields=None):
    """Send a private message to the developer as an embed."""
    # Fetch the developer's user object using their ID
    developer = await client.fetch_user(DEVELOPER_ID)

    # Create the embed
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

    # Send the embed with the image (if provided) to the developer
    if file:
        await send_embed(developer, title, description, color, None, fields, file)
    else:
        await send_embed(developer, title, description, color, None, fields)


def save_daily_report(guild_id: int, current_time: datetime, unique_users: int):
    daily_report_file = f'guilds/{guild_id}/daily_report_data.csv'

    # Create the guild directory if it doesn't exist
    guild_dir = os.path.dirname(daily_report_file)
    os.makedirs(guild_dir, exist_ok=True)

    report_data = f'{current_time},{unique_users}\n'
    with open(daily_report_file, 'a') as file:
        file.write(report_data)


def generate_plot(guilds: list):
    plot_image_file = f'daily_report_plot.png'

    plt.figure()

    # Loop through each guild and plot the data
    for guild in guilds:
        guild_id = guild.id
        guild_name = guild.name
        daily_report_file = f'guilds/{guild_id}/daily_report_data.csv'

        # Read the daily report data and create a DataFrame
        data = pd.read_csv(daily_report_file, names=[
                           'date', 'unique_users'], parse_dates=['date'])

        # Generate the plot for the current guild
        plt.plot(data['date'], data['unique_users'], label=f'{guild_name}')

    plt.xlabel('Date')
    plt.ylabel('Unique Users')
    plt.title(f'Daily Voice Channel Users')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    # Set the y-axis ticks to integer values
    ax = plt.gca()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Save the plot as an image
    plt.savefig(plot_image_file)

    return plot_image_file

# Get the current time with config.SERVER_TIMEZONE


def get_current_time(show_time=True, no_format=False):
    if no_format:
        return datetime.now(pytz.timezone(SERVER_TIMEZONE))
    else:
        if show_time:
            return datetime.now(pytz.timezone(SERVER_TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return datetime.now(pytz.timezone(SERVER_TIMEZONE)).strftime('%Y-%m-%d')


def populate_userlist(bot):
    for guild in bot.guilds:
        for channel in guild.channels:
            if isinstance(channel, discord.VoiceChannel):
                for member in channel.members:
                    manage_voice_activity(
                        guild.id, member.id, add_user=True)


def get_latest_commit_sha():
    url = f"https://api.github.com/repos/derekShaheen/TLEDiscordBot/commits"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commits = response.json()
        latest_commit = commits[0]
        full_sha = latest_commit["sha"]
        short_sha = full_sha[:7]

        return short_sha
    else:
        print(f"Error: {response.status_code}")
        return None

# Standard library imports
import os
import stat
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Third-party library imports
import discord
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import pytz
import requests
import yaml
from matplotlib.ticker import MaxNLocator
import numpy as np

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

def set_permissions(path):
    # Define the permission
    permission = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

    # Change the permission
    os.chmod(path, permission)


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

def store_last_seen(guild_id, user_id):
    seen_path = f'guilds/{guild_id}/users_seen.yml'
    seen_data = {}

    if os.path.exists(seen_path):
        with open(seen_path, 'r') as file:
            seen_data = yaml.safe_load(file)
    else:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(seen_path), exist_ok=True)
        
    seen_data[user_id] = get_current_time()

    with open(seen_path, 'w') as file:
        yaml.safe_dump(seen_data, file)


def load_last_seen(guild_id, user_id):
    seen_path = f'guilds/{guild_id}/users_seen.yml'
    
    if os.path.exists(seen_path):
        with open(seen_path, 'r') as file:
            seen_data = yaml.safe_load(file)
            if user_id in seen_data:
                return seen_data[user_id]
    
    return "Never"

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

def save_daily_voice_minutes(guild_id, minutes):
    guild_dir = f'guilds/{guild_id}'
    voice_minutes_file = f'{guild_dir}/voice_minutes.yml'

    os.makedirs(guild_dir, exist_ok=True)

    with open(voice_minutes_file, 'w') as file:
        yaml.safe_dump({'voice_minutes': minutes}, file)

def load_daily_voice_minutes():
    daily_voice_minutes = {}
    for guild_id in os.listdir('guilds'):
        voice_minutes_file = f'guilds/{guild_id}/voice_minutes.yml'
        if os.path.exists(voice_minutes_file):
            with open(voice_minutes_file, 'r') as file:
                daily_voice_minutes[int(guild_id)] = yaml.safe_load(file).get('voice_minutes', 0)
    return daily_voice_minutes

def clear_daily_voice_minutes():
    for guild_id in os.listdir('guilds'):
        voice_minutes_file = f'guilds/{guild_id}/voice_minutes.yml'
        if os.path.exists(voice_minutes_file):
            with open(voice_minutes_file, 'w') as file:
                yaml.safe_dump({'voice_minutes': 0}, file)

def manage_voice_activity(guild_id: int, user_id: int = 0, add_user: bool = False):
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

    if add_user and (user_id != 0):
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

def save_daily_report(guild_id: int, current_time: datetime, unique_users: int, total_voice_minutes: int):
    daily_report_file = f'guilds/{guild_id}/daily_report_data.csv'

    print(f'Saving report data... {current_time}, {unique_users}, {total_voice_minutes}')

    # Create the guild directory if it doesn't exist
    guild_dir = os.path.dirname(daily_report_file)
    os.makedirs(guild_dir, exist_ok=True)

    report_data = f'{current_time},{unique_users},{total_voice_minutes}\n'
    with open(daily_report_file, 'a') as file:
        file.write(report_data)

def generate_plot(guilds: list):
    print(f'Generating plot...')
    plot_image_file = f'daily_report_plot.png'

    plt.figure()

    # Loop through each guild and plot the data
    for guild in guilds:
        guild_id = guild.id
        guild_name = guild.name
        daily_report_file = f'guilds/{guild_id}/daily_report_data.csv'

        # Read the daily report data and create a DataFrame
        with open(daily_report_file, 'r') as file:
            first_line = file.readline().strip()
            columns = first_line.split(',')
            if len(columns) == 2:
                data = pd.read_csv(daily_report_file, names=['date', 'unique_users'], parse_dates=['date'])
                data['total_voice_hours'] = 0  # Add a default column for total_voice_hours
            else:
                data = pd.read_csv(daily_report_file, names=['date', 'unique_users', 'total_voice_minutes'], parse_dates=['date'])
                data['total_voice_hours'] = data['total_voice_minutes'] / 60.0

        max_value = data['unique_users'].max()
        max_value_date = data['date'][data['unique_users'].idxmax()].strftime('%Y-%m-%d')

        # Use only the bottom x rows of the data
        data = data.tail(30)

        mean_value = data['unique_users'].mean()
        median_value = data['unique_users'].median()
        std_dev = data['unique_users'].std()

        fig, ax1 = plt.subplots()

        color = 'tab:blue'
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Unique Users', color=color)
        ax1.bar(data['date'], data['unique_users'], color=color, alpha=0.6, label=f'{guild_name} - Unique Users')
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()  # Instantiate a second axes that shares the same x-axis
        color = 'tab:red'
        ax2.set_ylabel('Total Voice Hours', color=color)
        ax2.plot(data['date'], data['total_voice_hours'].round(2), label=f'{guild_name} - Total Voice Hours', color=color, linestyle='--')
        ax2.tick_params(axis='y', labelcolor=color)

        # Compute the coefficients of the linear trendline for unique users
        x = np.arange(len(data))
        coeffs = np.polyfit(x, data['unique_users'], 1)
        trendline = coeffs[0] * x + coeffs[1]
        trendline_plot, = ax1.plot(data['date'], trendline, label=f'Trend ({coeffs[0]:.2f}x + {coeffs[1]:.2f})', color='tab:blue', linestyle='--')

        # Fill the area between the trendline and the unique_users plot
        ax1.fill_between(data['date'], data['unique_users'], trendline, where=(data['unique_users'] > trendline), interpolate=True, alpha=0.3, color='tab:blue', edgecolor='none')

        # Label the final data point for unique users
        final_date = data['date'].iloc[-1]
        final_value = data['unique_users'].iloc[-1]
        ax1.text(final_date, final_value, f'{final_value}', color='tab:blue')

        # Label the final data point for total voice hours
        final_voice_hours_value = data['total_voice_hours'].round(1).iloc[-1]
        ax2.text(final_date, final_voice_hours_value, f'{final_voice_hours_value}', color='tab:red')

        # Display statistical information along the bottom of the graph
        stats_text = (
            f'Mean: {mean_value:.2f}\n'
            f'Median: {median_value}\n'
            f'Std Deviation: {std_dev:.2f}\n'
            f'Max: {max_value} on {max_value_date}'
        )
        plt.figtext(0.1225, 0.25, stats_text, horizontalalignment='left', verticalalignment='bottom')

        # Format the x-axis to show dates properly
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

        # Add a legend
        fig.legend(handles=[trendline_plot], loc='upper left')
        fig.tight_layout()  # Otherwise the right y-label is slightly clipped
        fig.subplots_adjust(top=0.93)  # Adjust the top padding to ensure the title is not cut off

    plt.title(f'Daily Voice Channel Usage')

    # Save the plot as an image
    plt.savefig(plot_image_file)

    return plot_image_file



def get_current_time(show_time=True, no_format=False):
    if no_format:
        return datetime.now(pytz.timezone(SERVER_TIMEZONE))
    else:
        if show_time:
            return datetime.now(pytz.timezone(SERVER_TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return datetime.now(pytz.timezone(SERVER_TIMEZONE)).strftime('%Y-%m-%d')

def compute_time_difference(time_str):
    fmt = '%Y-%m-%d %H:%M:%S'
    now = datetime.now()
    previous_time = datetime.strptime(time_str, fmt)
    difference = relativedelta(now, previous_time)

    time_diff_str = ""
    if difference.years > 0:
        time_diff_str += f'{difference.years} {pluralize(difference.years, "year", "years")}, '

    if difference.months > 0:
        time_diff_str += f'{difference.months} {pluralize(difference.months, "month", "months")}, '

    if difference.days > 0:
        time_diff_str += f'{difference.days} {pluralize(difference.days, "day", "days")}, '

    if difference.hours > 0:
        time_diff_str += f'{difference.hours} {pluralize(difference.hours, "hour", "hours")}, '

    if difference.minutes > 0:
        time_diff_str += f'{difference.minutes} {pluralize(difference.minutes, "minute", "minutes")}, '

    if difference.seconds > 0:
        time_diff_str += f'{difference.seconds} {pluralize(difference.seconds, "second", "seconds")}, '

    # If the string ends with ', ', remove it
    if time_diff_str.endswith(", "):
        time_diff_str = time_diff_str[:-2]

    return f'{time_diff_str} ago'


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
        print(f"Error checking version: {response.status_code}")
        return None
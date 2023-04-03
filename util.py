import yaml
import os
import discord
from config import DEVELOPER_ID


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
    default_config = {'log_channel_name': 'voice_logs',
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


async def send_embed(recipient, title, description, color, url=None, fields=None):
    embed = discord.Embed(
        title=title, description=description, color=color, url=url)
    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
    embed.timestamp = discord.utils.utcnow()
    await recipient.send(embed=embed)


def manage_voice_activity(guild_id: int, user_id: int = None, add_user: bool = False):
    guild_dir = f'guilds/{guild_id}'
    voice_activity_file = f'{guild_dir}/voice_activity.yaml'

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
    voice_activity_file = f'{guild_dir}/voice_activity.yaml'

    # Create the guild directory if it doesn't exist
    os.makedirs(guild_dir, exist_ok=True)

    # Clear the voice_activity data
    voice_activity_data = set()

    # Save the cleared voice_activity_data to the YAML file
    with open(voice_activity_file, 'w') as file:
        yaml.safe_dump(list(voice_activity_data), file)


async def send_developer_message(client, title, description, color, fields=None, timestamp=None):
    """Send a private message to the developer as an embed."""
    # Fetch the developer's user object using their ID
    developer = await client.fetch_user(DEVELOPER_ID)

    # Send the embed message to the developer
    await send_embed(developer, title, description, color, None, fields)

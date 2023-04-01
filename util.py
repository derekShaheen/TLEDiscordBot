import yaml
import os
import discord

def pluralize(count, singular, plural):
    return plural if count > 1 else singular

# Path: util.py
# Compare this snippet from TLEDiscord.py and provide other useful Discord bot utilities:

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

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def user_list(channel):
    if not channel.members:
        return "No users"
    return ", ".join([member.mention for member in channel.members])

def load_config(guild_id):
    config_path = f'config/{guild_id}.yml'
    default_config = {'log_channel_name': 'voice_logs', 'logging_enabled': True}

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
    config_path = f'config/{guild_id}.yml'

    with open(config_path, 'w') as file:
        yaml.safe_dump(config, file)

async def send_embed(log_channel, title, description, color, fields=None, timestamp=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
    if timestamp:
        embed.timestamp = timestamp
    await log_channel.send(embed=embed)
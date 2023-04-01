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
import discord
from discord.ext import commands
import util
from yaml import safe_load
from os import path

def has_required_role(member, allowed_roles):
    if member.guild is None:
        return False
    # Check if the member has the "Administrator" permission
    if any(role.permissions.administrator for role in member.roles):
        return True

    # Check if the member has any of the allowed roles
    return any(role.name in allowed_roles for role in member.roles)


@commands.command(
    name='move',
    help='Move all users from the source voice channel to the destination voice channel. If no source channel is specified, your current voice channel will be used. \nParameters: \n   <destination> - The name of the destination voice channel. \n   (source) - (Optional) The name of the source voice channel.'
)
async def move(ctx, destination_name: str = None, source_name: str = None):
    # If both destination_name and source_name are None, display help output
    if destination_name is None and source_name is None:
        help_output = (
            "Usage:\n"
            "!move <destination> (source)\n\n"
            "Move all users from the source voice channel to the destination voice channel.\n"
            "If no source channel is specified, your current voice channel will be used.\n"
            "Parameters:\n"
            "<destination> - The name of the destination voice channel.\n"
            "(source) - (Optional) The name of the source voice channel."
        )
        await ctx.send(help_output)
        return

    # Check if the bot is connected to the guild
    if ctx.guild is None:
        # user_id = ctx.author.id
        # associated_guilds = await util.find_user_guild(ctx, user_id)
        
        # if len(associated_guilds) == 1:
        #     for guild in associated_guilds:
        #         response += f"{guild.name}\n"
        #         ctx.guild = guild

        await ctx.send('Error: This command can only be used in a server.')
        return

    # Make sure the user has the required role
    if not await has_required_role(ctx):
        await ctx.send("You do not have the required role to use this command.")
        return

    # Set source voice channel
    if source_name:
        source_channel = discord.utils.get(
            ctx.guild.voice_channels, name=source_name)
        if not source_channel:
            await ctx.send(f'Error: could not find source voice channel "{source_name}"')
            return
    else:
        if not ctx.author.voice:
            await ctx.send('Error: you are not currently in a voice channel.')
            return
        source_channel = ctx.author.voice.channel

    if not source_channel.members:
        await ctx.send(f'No users found in the source channel "{source_name}".')
        return

    # Get destination voice channel
    destination_channel = discord.utils.get(
        ctx.guild.voice_channels, name=destination_name)
    if not destination_channel:
        await ctx.send(f'Error: could not find destination voice channel "{destination_name}"')
        return

    moved_users_count = len(source_channel.members)

    # Move all users in source channel to destination channel
    for member in source_channel.members:
        try:
            await member.move_to(destination_channel)
        except discord.errors.HTTPException as e:
            await ctx.send(f'Error moving {member.display_name}: {str(e)}')

    # Send confirmation message
    await ctx.send(f'Moved {util.pluralize(moved_users_count, "user", "users")} from {source_channel.name} to {destination_channel.name}')


@commands.command(
    name='setlogchannel',
    help='Set the name of the log channel for voice activity.'
)
async def set_log_channel(ctx, log_channel_name: str = None):
    # Make sure the user has the required role
    if not await has_required_role(ctx):
        await ctx.send("You do not have the required role to use this command.")
        return

    if log_channel_name is None:
        await ctx.send("Please provide a log channel name.")
        return

    config = util.load_config(ctx.guild.id)
    config['log_channel_name'] = log_channel_name
    util.save_config(ctx.guild.id, config)

    await ctx.send(f'Successfully set the log channel name to "{log_channel_name}".')


@commands.command(name='toggle_logging')
async def toggle_logging(ctx):
    # Make sure the user has the required role
    if not await has_required_role(ctx):
        await ctx.send("You do not have the required role to use this command.")
        return

    guild_id = ctx.guild.id
    config = util.load_config(guild_id)
    logging_enabled = config.get('logging_enabled', True)
    config['logging_enabled'] = not logging_enabled
    util.save_config(guild_id, config)

    if logging_enabled:
        await ctx.send("Logging has been disabled.")
    else:
        await ctx.send("Logging has been enabled.")


@commands.command(name='modify_allowed_roles')
async def modify_allowed_roles(ctx, action: str, role_name: str):
    # Load the allowed_roles list from the config
    config = util.load_config(ctx.guild.id)
    allowed_roles = config.get('allowed_roles', [])

    # If the user is not an administrator, check if they have an allowed role
    if not ctx.author.guild_permissions.administrator:
        if not has_required_role(ctx.author, allowed_roles):
            await ctx.send("You do not have the required role to use this command.")
            return

    action = action.lower()
    if action == 'add':
        if role_name not in allowed_roles:
            allowed_roles.append(role_name)
            await ctx.send(f'Successfully added "{role_name}" to the allowed roles list.')
        else:
            await ctx.send(f'Role "{role_name}" is already in the allowed roles list.')
    elif action == 'remove':
        if role_name in allowed_roles:
            allowed_roles.remove(role_name)
            await ctx.send(f'Successfully removed "{role_name}" from the allowed roles list.')
        else:
            await ctx.send(f'Role "{role_name}" is not in the allowed roles list.')
    else:
        await ctx.send('Invalid action. Please use "add" or "remove".')

    # Save the updated allowed_roles list to the config
    config['allowed_roles'] = allowed_roles
    util.save_config(ctx.guild.id, config)


@commands.command(name='view_allowed_roles')
async def view_allowed_roles(ctx):
    allowed_roles = util.load_config(ctx.guild.id).get('allowed_roles', [])

    # If the user is not an administrator, check if they have an allowed role
    if not ctx.author.guild_permissions.administrator:
        if not has_required_role(ctx.author, allowed_roles):
            await ctx.send("You do not have the required role to use this command.")
            return

    if not allowed_roles:
        await ctx.send("No allowed roles have been set.")
    else:
        await ctx.send(f"Allowed roles: {', '.join(allowed_roles)}")

@commands.command(name='channel_stats')
async def voice_stats(ctx):
    allowed_roles = util.load_config(ctx.guild.id).get('allowed_roles', [])

    # If the user is not an administrator, check if they have an allowed role
    if not ctx.author.guild_permissions.administrator:
        if not has_required_role(ctx.author, allowed_roles):
            await ctx.send("You do not have the required role to use this command.")
            return

    file_path = f'guilds/{ctx.guild.id}/voice_activity.yaml'

    if not path.exists(file_path):
        await ctx.send("No voice activity data is available.")
        return

    with open(file_path, 'r') as file:
        voice_activity = safe_load(file)

    output = "Voice Channel Activity:\n\n"
    for channel_name, stats in voice_activity.items():
        output += f'{channel_name}:\n  Joins: {stats["joins"]}\n  Leaves: {stats["leaves"]}\n\n'

    await ctx.send(output)
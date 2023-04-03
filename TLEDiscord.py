import asyncio
import cmds

import config
import datetime
from datetime import time, timedelta
import pytz
import discord
import util
from discord.ext import commands, tasks

user_join_times = {}

tle_prefix = '!'

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=tle_prefix, intents=intents)

bot.add_command(cmds.move)
bot.add_command(cmds.set_log_channel)
bot.add_command(cmds.toggle_logging)
bot.add_command(cmds.modify_allowed_roles)
bot.add_command(cmds.view_allowed_roles)

# Initialize the bot


@bot.event
async def on_ready():
    print("----------------------")
    print("Logged in as")
    print("\tUsername: %s" % bot.user.name)
    print("\tID: %s" % bot.user.id)
    print(f"\tInvite URL: https://discordapp.com/oauth2/authorize?client_id={bot.user.id}&scope=bot&permissions=8")
    print("----------------------")

    print("Bot is running on the following servers:")
    for guild in bot.guilds:
        print(f"\tServer: {guild.name} (ID: {guild.id})")
        print(f"\t\tMember count: {len(guild.members)}")

    print("----------------------")

    print("Initializing and scheduling tasks...")

    heartbeat.start()
    daily_report.start()
    check_and_move_users.start()

    for guild in bot.guilds:
        util.clear_voice_activity(guild.id)
        for channel in guild.channels:
            if isinstance(channel, discord.VoiceChannel):
                for member in channel.members:
                    util.manage_voice_activity(guild.id, member.id, add_user=True)

    print('Voice activity data updated.')

    print("Bot Commands:")
    for command in sorted(bot.commands, key=lambda cmd: cmd.name):
        print(f"\t!{command.name}")

    # Prepare the message content
    message_content = f'{bot.user} is now online and connected to the following servers:\n'
    for guild in bot.guilds:
        message_content += f'\t{guild.name} (id: {guild.id})\n'

    title = "Bot Online"
    description = message_content
    color = discord.Color.green()
    await util.send_developer_message(bot, title, description, color)

    print("Ready...")
    heartbeat_proc()


@bot.event
async def on_guild_join(guild):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] [{guild.name}] The bot has been added to the server: {guild.name} (id: {guild.id}) with {guild.member_count} members.")

    # Prepare the message content
    message_content = f'{bot.user} has been added to the following server:\n'
    message_content += f'{guild.name} (id: {guild.id})\n'

    title = "Bot Added to Server"
    description = message_content
    color = discord.Color.green()
    await util.send_developer_message(bot, title, description, color)


@bot.event
async def on_guild_remove(guild):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] [{guild.name}] The bot has been removed from the server: {guild.name} (id: {guild.id}) with {guild.member_count} members.")

    # Prepare the message content
    message_content = f'{bot.user} has been removed from the following server:\n'
    message_content += f'{guild.name} (id: {guild.id})\n'

    title = "Bot Removed from Server"
    description = message_content
    color = discord.Color.red()
    await util.send_developer_message(bot, title, description, color)

# Loop section


@tasks.loop(minutes=30)
async def heartbeat():
    heartbeat_proc()


def heartbeat_proc():
    for guild in bot.guilds:
        total_users = len(guild.members)
        users_in_voice_chat = sum(
            1 for member in guild.members if member.voice)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] [{guild.name}] Total Users: {total_users}\t| Users in Voice Chat: {users_in_voice_chat}")


@tasks.loop(hours=24)
async def check_and_move_users():
    current_time = datetime.datetime.now(pytz.timezone(
        config.SERVER_TIMEZONE))  # Adjust the timezone if needed
    target_time = time(hour=18, minute=00)

    if current_time.time() > target_time:
        for guild in bot.guilds:
            source_channel = discord.utils.get(
                guild.voice_channels, name="Twerk")
            member_general_channel = discord.utils.get(
                guild.voice_channels, name="Member General")

            if source_channel and member_general_channel:
                moved_users_count = 0
                for member in source_channel.members:
                    try:
                        await member.move_to(member_general_channel)
                        moved_users_count += 1
                    except discord.errors.HTTPException as e:
                        print(f'Error moving {member.display_name}: {str(e)}')
                current_time = datetime.datetime.now(
                    pytz.timezone(config.SERVER_TIMEZONE))

                if moved_users_count > 0:
                    print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] [AutoMove] Moved {util.pluralize(moved_users_count, 'user', 'users')} from {source_channel.name} to {member_general_channel.name}")
                else:
                    print(
                        f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] [AutoMove] No users to move from {source_channel.name} to {member_general_channel.name}")


@tasks.loop(hours=24)
async def daily_report():
    current_time = datetime.datetime.now(pytz.timezone(config.SERVER_TIMEZONE))
    print(message_content)
    for guild in bot.guilds:
        for channel in guild.channels:
            if isinstance(channel, discord.VoiceChannel):
                for member in channel.members:
                    userlist = util.manage_voice_activity(guild.id, None, add_user=False)
                    message_content = f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] [Daily Report] [{guild.name}] {len(userlist)} unique users joined a voice channel since yesterday."
        util.clear_voice_activity(guild.id)

    # Send the message to the developer as an embed
    title = "Daily Report"
    description = message_content
    color = discord.Color.blue()
    await util.send_developer_message(bot, title, description, color)

# Before loop section


@heartbeat.before_loop
async def before_heartbeat():
    now = datetime.datetime.now(pytz.timezone(config.SERVER_TIMEZONE))

    if now.minute < 30:
        target_minute = 30
    else:
        target_minute = 0

    if target_minute == 0:
        next_run = now.replace(
            minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        next_run = now.replace(minute=30, second=0, microsecond=0)

    # print(f"Next heartbeat: {(next_run - now).total_seconds()}")
    await asyncio.sleep((next_run - now).total_seconds())


@check_and_move_users.before_loop
async def before_check_and_move_users():
    now = datetime.datetime.now(pytz.timezone(config.SERVER_TIMEZONE))
    target_time = datetime.time(hour=18, minute=00)
    tomorrow = now.date() + timedelta(days=1)
    next_run = datetime.datetime.combine(
        tomorrow, target_time, tzinfo=now.tzinfo)
    # print(f"Next twerk move run:{(next_run - now).total_seconds()}")
    await asyncio.sleep((next_run - now).total_seconds())


@daily_report.before_loop
async def before_daily_report():
    now = datetime.datetime.now(pytz.timezone(config.SERVER_TIMEZONE))
    target_time = datetime.time(hour=6, minute=00)
    tomorrow = now.date() + timedelta(days=1)
    next_run = datetime.datetime.combine(
        tomorrow, target_time, tzinfo=now.tzinfo)
    # print(f"Next daily report run:{(next_run - now).total_seconds()}")
    await asyncio.sleep((next_run - now).total_seconds())

# Event section


async def log_event(guild, log_channel_name, title, description, color, timestamp=None):
    config = util.load_config(guild.id)
    if not config.get('logging_enabled', True):
        return

    log_channel = discord.utils.get(guild.text_channels, name=log_channel_name)

    if not log_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False)
        }
        log_channel = await guild.create_text_channel(log_channel_name, overwrites=overwrites)

    embed = discord.Embed(title=title, description=description,
                          color=color, timestamp=timestamp)
    await log_channel.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Error: Missing required argument: {error.param.name}')
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'Error: Bad argument: {error.param.name}')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f'Error: Missing permissions: {error.missing_perms}')
    else:
        await ctx.send(f'Error: {error}')


@bot.event
async def on_member_remove(member):
    await log_event(member.guild, config['log_channel_name'], f'{member.display_name} left the server', '', discord.Color.red(), timestamp=datetime.datetime.now())


@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        await log_event(after.guild, config['log_channel_name'], f'{after.display_name} changed their nickname', f'Before: {before.nick}\nAfter: {after.nick}', discord.Color.blue())


@bot.event
async def on_message_delete(message):
    await log_event(message.guild, config['log_channel_name'], f'{message.author.display_name} deleted a message', message.content, discord.Color.red(), timestamp=message.created_at)


@bot.event
async def on_message_edit(before, after):
    if before.content != after.content:
        await log_event(after.guild, config['log_channel_name'], f'{after.author.display_name} edited a message', f'Before: {before.content}\nAfter: {after.content}', discord.Color.blue(), timestamp=after.edited_at)

# @bot.event
# async def on_message(message):
#     if message.author.bot:
#         return

#     if not message.guild:  # Check if the message is a private message
#         user_id = message.author.id
#         associated_guilds = await util.find_user_guild(bot, user_id)
        
#         if associated_guilds:
#             response = "You are associated with the following server(s):\n"
#             for guild in associated_guilds:
#                 response += f"{guild.name}\n"
#         else:
#             response = "You are not associated with any servers the bot is connected to."
        
#         await message.channel.send(response)


@bot.event
async def on_voice_state_update(member, before, after):
    # Store the user ID in joined_users set when they join a voice channel
    if before.channel is None and after.channel is not None:
        util.manage_voice_activity(member.guild.id, member.id, add_user=True)

    # Track channel join/leave
    # if before.channel != after.channel:
        # if before.channel is not None:
        #     await util.update_voice_activity(member.guild.id, before.channel.name, join=False)

        # if after.channel is not None:
        #     await util.update_voice_activity(member.guild.id, after.channel.name, join=True)

    if before.channel != after.channel:
        config = util.load_config(member.guild.id)
        if not config.get('logging_enabled', True):
            return

        log_channel_name = config['log_channel_name']
        log_channel = discord.utils.get(
            member.guild.text_channels, name=log_channel_name)

        if not log_channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False)
            }
            log_channel = await member.guild.create_text_channel(log_channel_name, overwrites=overwrites)

        user_id = member.id
        now = datetime.datetime.utcnow()

        if before.channel is None:
            user_join_times[user_id] = now
            title = f'{member.name} joined a voice channel'
            description = f'> {member.mention} joined `{after.channel.name}`'
            color = discord.Color.green()
            fields = [(f'Users in {after.channel.name}',
                       util.user_list(after.channel))]
            await util.send_embed(log_channel, title, description, color, None, fields)
        elif after.channel is None:
            duration = round(
                (now - user_join_times.pop(user_id, now)).total_seconds())
            formatted_duration = util.format_duration(duration)
            title = f'{member.name} left a voice channel'
            description = f'> {member.mention} left from `{before.channel.name}`'
            color = discord.Color.red()
            fields = [
                (f'Duration', f'{formatted_duration}'),
                (f'Users in {before.channel.name}',
                 util.user_list(before.channel))
            ]
            await util.send_embed(log_channel, title, description, color, None, fields)
        else:
            duration = round(
                (now - user_join_times.pop(user_id, now)).total_seconds())
            formatted_duration = util.format_duration(duration)
            user_join_times[user_id] = now
            title = f'{member.name} switched voice channels'
            description = f'> {member.mention} moved from `{before.channel.name}` ➦ `{after.channel.name}`'
            color = discord.Color.blue()
            fields = [
                (f'Duration in {before.channel.name}',
                 f'{formatted_duration}'),
                (f'Users in {before.channel.name}',
                 util.user_list(before.channel)),
                (f'Users in {after.channel.name}',
                 util.user_list(after.channel))
            ]
            await util.send_embed(log_channel, title, description, color, None, fields)

bot.run(config.TOKEN)

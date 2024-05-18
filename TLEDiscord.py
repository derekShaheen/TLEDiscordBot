# Standard library imports
import asyncio
from datetime import time, timedelta, datetime
import math
import sys
from os import execv

# Third-party imports
import discord
from discord.ext import commands, tasks
from io import StringIO
# from rich import print
from rich.table import Table
from rich.live import Live
from rich.traceback import install
from rich.console import Console
import re


# Local imports
import cmds
import config
import util

install()
heartbeat_counter = 0
user_join_times = {}
initial_run_sha = 0
max_auto_channels = 9
daily_voice_minutes = {}

tle_prefix = '!'

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=tle_prefix, intents=intents, reconnect=True)

bot.add_command(cmds.move)
bot.add_command(cmds.set_log_channel)
bot.add_command(cmds.toggle_logging)
bot.add_command(cmds.allowed_roles)
bot_start_time = datetime.now() + timedelta(seconds=2)

# Initialize the bot


@bot.event
async def on_ready():
    global initial_run_sha
    initial_run_sha = util.get_latest_commit_sha()

    print("----------------------")
    print("Logged in at: %s" % util.get_current_time())
    print("\tUsername: %s" % bot.user.name)
    print("\tID: %s" % bot.user.id)
    print(
        f"\tInvite URL: https://discordapp.com/oauth2/authorize?client_id={bot.user.id}&scope=bot&permissions=8")
    # print(f"Connection latency: {bot.latency * 1000:.0f}ms")
    print("----------------------")

    print("Bot is running on the following servers:")
    for guild in bot.guilds:
        print(f"\tServer: {guild.name} (ID: {guild.id})")
        #print(f"\t\tMember count: {len(guild.members)}")

    print("----------------------")
    util.populate_userlist(bot)

    print('Voice activity data updated.')

    print("Bot Commands:")
    for command in sorted(bot.commands, key=lambda cmd: cmd.name):
        print(f"\t!{command.name}")

    print("\nInitializing and scheduling tasks...")

    daily_report.start()
    check_and_move_users.start()
    check_version.start()
    restart_bot_loop.start()
    #heartbeat_loop.start()

    # Prepare the message content
    message_content = f'{bot.user} is now online and connected to the following servers:\n'
    for guild in bot.guilds:
        message_content += f'{guild.name} (id: {guild.id})\n'

    title = f"Bot Online [{initial_run_sha}]"
    description = message_content
    color = discord.Color.green()
    #await util.send_developer_message(bot, title, description, color)
    #await daily_report()
    # print("Ready...")


@bot.event
async def on_guild_join(guild):
    current_time = util.get_current_time()
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
    current_time = util.get_current_time()
    print(f"[{current_time}] [{guild.name}] The bot has been removed from the server: {guild.name} (id: {guild.id}) with {guild.member_count} members.")

    # Prepare the message content
    message_content = f'{bot.user} has been removed from the following server:\n'
    message_content += f'{guild.name} (id: {guild.id})\n'

    title = "Bot Removed from Server"
    description = message_content
    color = discord.Color.red()
    await util.send_developer_message(bot, title, description, color)


@bot.command()
async def exit(ctx):
    if ctx.author.id == config.DEVELOPER_ID:
        title = "Bot Exiting..."
        description = 'Bot is exiting. Restart will be attempted...'
        color = discord.Color.red()
        await util.send_developer_message(bot, title, description, color)
        await bot.close()

# Loop section


# @tasks.loop(seconds=1)
# async def heartbeat_loop():
#     # heartbeat_proc()
#     await live_heartbeat()

@bot.command()
async def heartbeat(ctx):
    if ctx.author.id == config.DEVELOPER_ID:
        #await ctx.send('Running heartbeat...')
        table = generate_table()
        await send_table_as_code_block(ctx, table)

def strip_control_characters(s):
    return re.sub(r'\x1b[^m]*m', '', s)

async def send_table_as_code_block(ctx, table):
    # Capture the output of the Rich table into a string
    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True)
    console.print(table)

    # Get the contents of the string buffer and strip control characters
    table_contents = buffer.getvalue()
    stripped_contents = strip_control_characters(table_contents)

    # Send the stripped contents as a code block in a message
    await ctx.send(f"```\n{stripped_contents}\n```")


def generate_table() -> Table:
    table = Table()
    table.add_column("Uptime", justify="center")
    # table.add_column(f"Heartbeat", justify="center")
    table.add_column("Ping", justify="center")
    table.add_column("Guild", justify="center")
    table.add_column("Total Users", justify="center")
    table.add_column("In Voice", justify="center")
    table.add_column("Unique Today", justify="center")
    uptime = datetime.now() - bot_start_time
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    latency_ms = bot.latency * 1000  # Convert to milliseconds
    # current_time = util.get_current_time()

    for guild in bot.guilds:
        total_users = len(guild.members)
        users_in_voice_chat = sum(
            1 for member in guild.members if member.voice)
        unique_users_in_voice_chat = util.manage_voice_activity(
            guild.id, 0, add_user=False)

        # Truncate the guild name to 17 characters
        truncated_guild_name = guild.name[:20]

        # Set latency color based on the value
        latency_color = "green" if latency_ms < 100 else (
            "yellow" if latency_ms <= 200 else "red")
        if (latency_ms >= 1000):
            latency_text = f"[{latency_color}]{latency_ms:.0f}ms[/{latency_color}]"
        elif (latency_ms >= 100):
            latency_text = f"[{latency_color}]{latency_ms:.1f}ms[/{latency_color}]"
        else:
            latency_text = f"[{latency_color}]{latency_ms:.2f}ms[/{latency_color}]"
        if unique_users_in_voice_chat is not None:
            table.add_row(
                uptime_str,
                # current_time,
                latency_text,
                f"{truncated_guild_name}",
                str(total_users),
                str(users_in_voice_chat),
                str(len(unique_users_in_voice_chat))
            )
        else:
            table.add_row(
                uptime_str,
                # current_time,
                latency_text,
                f"{truncated_guild_name}",
                str(total_users),
                str(users_in_voice_chat),
                "0"
            )

    return table

@tasks.loop(hours=24)
async def check_and_move_users():
    for guild in bot.guilds:
        source_channel = discord.utils.get(
            guild.voice_channels, name="Twerk")
        
        if source_channel is None:
            source_channel = discord.utils.get(
                guild.voice_channels, name="Work")

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
            current_time = util.get_current_time()

            if moved_users_count > 0:
                print(f"[{current_time}] [AutoMove] Moved {util.pluralize(moved_users_count, 'user', 'users')} from {source_channel.name} to {member_general_channel.name}")
            else:
                print(
                    f"[{current_time}] [AutoMove] No users to move from {source_channel.name} to {member_general_channel.name}")


@tasks.loop(hours=24)
async def daily_report():
    config = util.load_config('262726474967023619') # Hardcoding for TLE
    current_time = util.get_current_time(False)
    # Create the message embed
    title = f"{current_time} Daily Report for {util.pluralize(len(bot.guilds), 'Guild', 'All Guilds')}"
    description = "Plot displays the number of unique users who joined a voice channel since the prior day by guild."
    color = discord.Color.magenta()

    # Update the voice activity data
    for guild in bot.guilds:
        userlist = util.manage_voice_activity(guild.id, 0, add_user=False)
        if userlist is None:
            unique_users = 0
        else:
            unique_users = len(userlist)

        # Get the total voice minutes for the guild
        total_voice_minutes = daily_voice_minutes.get(guild.id, 0)

        # Save the daily report data to a file
        util.save_daily_report(guild.id, current_time, unique_users, total_voice_minutes)
        if (guild.id == 262726474967023619) and config.get('logging_enabled', True) == True: # Hardcoding for TLE
            log_channel_name = config['log_channel_name']
            log_channel = discord.utils.get(
                guild.text_channels, name=log_channel_name)

            if not log_channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=False)
                }
                log_channel = await guild.create_text_channel(log_channel_name, overwrites=overwrites)

            # Find or create the "Daily Reports" thread under the log_channel
            daily_reports_thread = discord.utils.get(
                log_channel.threads, name="Daily Reports")

            if not daily_reports_thread:
                daily_reports_thread = await log_channel.create_thread(name="Daily Reports", type=discord.ChannelType.public_thread, auto_archive_duration=10080)

            plot_image_file = util.generate_plot(bot.guilds)
            with open(plot_image_file, 'rb') as file:
                await util.send_embed(daily_reports_thread, title, description, color, None, None, file=discord.File(file))

    if not config.get('logging_enabled', True) or len(bot.guilds) > 1:
        # Generate the plot and get the image file path
        plot_image_file = util.generate_plot(bot.guilds)

        # Send the embed with the image to the developer
        with open(plot_image_file, 'rb') as file:
            await util.send_developer_message(bot, title, description, color, file=discord.File(file))
        
    # Reset daily voice minutes
    daily_voice_minutes = {}

    for guild in bot.guilds:
        util.clear_voice_activity(guild.id)

    util.populate_userlist(bot)

@tasks.loop(seconds=30)
async def check_version():
    global initial_run_sha
    check_sha = util.get_latest_commit_sha()

    if not check_sha.startswith('Error') and initial_run_sha != check_sha:
        title = "New bot version has been detected."
        description = f'Initiating the update and restart process...\n[{initial_run_sha}] -> [{check_sha}]'
        color = discord.Color.blurple()
        await util.send_developer_message(bot, title, description, color)
        await bot.close()

@tasks.loop(hours=24)
async def restart_bot_loop():
    now = datetime.now()
    weekday = now.weekday()  # Monday is 0 and Sunday is 6

    # Schedule the bot to restart at 0400 on Tuesday (weekday 1)
    if weekday == 1:
        print("Restarting bot...")
        await bot.close()

# Before loop section


def get_initial_delay(target_time: time = None, interval: timedelta = None) -> float:
    now = util.get_current_time(False, True)

    if target_time:
        # Schedule task at the target time
        if now.time() >= target_time:
            tomorrow = now.date() + timedelta(days=1)
        else:
            tomorrow = now.date()
        next_run = datetime.combine(
            tomorrow, target_time, tzinfo=now.tzinfo)
    elif interval:
        # Schedule task at the next interval
        interval_seconds = interval.total_seconds()
        elapsed_time = (now - now.replace(hour=0, minute=0,
                        second=0, microsecond=0)).total_seconds()
        next_run_seconds = math.ceil(
            elapsed_time / interval_seconds) * interval_seconds
        next_run = now.replace(hour=0, minute=0, second=0,
                               microsecond=0) + timedelta(seconds=next_run_seconds)

    return (next_run - now).total_seconds()


# @heartbeat_loop.before_loop
# async def before_heartbeat_loop():
#     heartbeat_proc()
#     initial_delay = get_initial_delay(interval=timedelta(minutes=30))
#     #print('Heartbeat loop scheduled for: {}'.format(initial_delay))
#     await asyncio.sleep(initial_delay)


@check_and_move_users.before_loop
async def before_check_and_move_users():
    target_time = time(hour=18, minute=00)
    initial_delay = get_initial_delay(target_time=target_time)
    print('First Check/Move scheduled for: \t{}'.format(target_time))
    await asyncio.sleep(initial_delay)


@daily_report.before_loop
async def before_daily_report():
    target_time = time(hour=6, minute=00)
    initial_delay = get_initial_delay(target_time=target_time)
    print('Daily Report loop scheduled for:\t{}'.format(target_time))
    await asyncio.sleep(initial_delay)

@check_version.before_loop
async def before_check_version():
    initial_delay = get_initial_delay(interval=timedelta(seconds=30))
    print('Version Check loop scheduled for: {}'.format(initial_delay))
    await asyncio.sleep(initial_delay)

@restart_bot_loop.before_loop
async def before_restart_bot():
    target_time = time(hour=4, minute=1)
    initial_delay = get_initial_delay(target_time=target_time)
    print('Restart bot loop scheduled for: {}'.format(initial_delay))
    await asyncio.sleep(initial_delay)


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
    elif isinstance(error, (discord.HTTPException, discord.GatewayNotFound, discord.ConnectionClosed)):
        await ctx.send(f'Error: Discord API error: {error}')
        pass
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
async def on_voice_state_update(member, before, after):
    # Handle Game Room voice channel creation / deletion
    categories_to_monitor = ["Member Game Rooms", "Public Game Rooms"]

    if before.channel != after.channel:
        for category_name in categories_to_monitor:
            game_room_category = discord.utils.get(member.guild.categories, name=category_name)

            if game_room_category:
                # Check if the user has joined or left a channel in the specified category
                if (before.channel and before.channel.category == game_room_category) or (after.channel and after.channel.category == game_room_category):
                    # Retrieve and sort the game rooms in the category
                    game_rooms = sorted([channel for channel in member.guild.voice_channels if util.is_game_room_channel(channel, category_name)],
                                        key=lambda x: int(x.name.split()[-1]))

                    # Delete empty game rooms except Game Room 1
                    for i, game_room in enumerate(game_rooms):
                        if i != 0 and len(game_room.members) == 0:
                            await game_room.delete()

                    # Refresh the list of game rooms
                    game_rooms = sorted([channel for channel in member.guild.voice_channels if util.is_game_room_channel(channel, category_name)],
                                        key=lambda x: int(x.name.split()[-1]))

                    # Determine the next available integer for Game Room
                    next_game_room_number = None
                    for i, game_room in enumerate(game_rooms):
                        game_room_number = i + 1

                        if game_room_number != int(game_room.name.split()[-1]):
                            next_game_room_number = game_room_number
                            break

                    # Assign the next available integer if not found
                    if next_game_room_number is None:
                        next_game_room_number = int(game_rooms[-1].name.split()[-1]) + 1

                    # Create the next Game Room if needed
                    if len(game_rooms[-1].members) > 0 and len(game_rooms[0].members) > 0 and len(game_rooms) < max_auto_channels:
                        await util.create_game_room(member.guild, game_room_category, f"{next_game_room_number}")

    # ====================================================================================================

    # Store the user ID in joined_users set when they join a voice channel
    if before.channel is None and after.channel is not None:
        util.manage_voice_activity(member.guild.id, member.id, add_user=True)

    # Track channel join/leave
    if before.channel != after.channel:
        config = util.load_config(member.guild.id)
        
        # Check if logging is enabled
        if not config.get('logging_enabled', True):
            return

        log_channel_name = config['log_channel_name']
        log_channel = discord.utils.get(
            member.guild.text_channels, name=log_channel_name)

        # Create the log channel if it doesn't exist
        if not log_channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False)
            }
            log_channel = await member.guild.create_text_channel(log_channel_name, overwrites=overwrites)

        user_id = member.id
        avatar_url = str(member.avatar.url) if member.avatar else str(member.default_avatar.url)
        now = util.get_current_time(False, True)

        # If the user joined a voice channel
        if before.channel is None:
            user_join_times[user_id] = now
            title = 'Connected to a voice channel'
            last_seen = util.load_last_seen(member.guild.id, member.id)
            if last_seen != 'Never':
                time_difference = util.compute_time_difference(last_seen)
            description = f'> {member.mention} joined `{after.channel.category}.{after.channel.name}`'
            color = discord.Color.green()
            if last_seen != 'Never':
                fields = [
                    (f'Last Seen on Server', f'{time_difference} on {last_seen}'),
                    (f'Users in {after.channel.name}', util.user_list(after.channel))
                ]
            else:
                fields = [
                    (f'Last Seen on Server', f'{last_seen}'),
                    (f'Users in {after.channel.name}', util.user_list(after.channel))
                ]
            await util.send_embed(log_channel, title, description, color, None, fields, None, thumbnail_url=avatar_url)
        # If the user left a voice channel
        elif after.channel is None:
            duration = round(
                (now - user_join_times.pop(user_id, now)).total_seconds())
            formatted_duration = util.format_duration(duration)

            # Update daily voice minutes
            if member.guild.id not in daily_voice_minutes:
                daily_voice_minutes[member.guild.id] = 0
            daily_voice_minutes[member.guild.id] += duration // 60

            title = 'Disconnected from a voice channel'
            description = f'> {member.mention} left from `{before.channel.category}.{before.channel.name}`'
            color = discord.Color.red()
            fields = [
                (f'Duration', f'{formatted_duration}'),
                (f'Users in {before.channel.name}',
                util.user_list(before.channel))
            ]
            await util.send_embed(log_channel, title, description, color, None, fields, None, thumbnail_url=avatar_url)
        # If the user switched voice channels
        else:
            duration = round(
                (now - user_join_times.pop(user_id, now)).total_seconds())
            formatted_duration = util.format_duration(duration)

            # Update daily voice minutes
            if member.guild.id not in daily_voice_minutes:
                daily_voice_minutes[member.guild.id] = 0
            daily_voice_minutes[member.guild.id] += duration // 60

            user_join_times[user_id] = now
            title = f'{member.display_name}#{member.discriminator} switched voice channels'
            description = f'> User {member.mention} moved from \n`{before.channel.category}.{before.channel.name}` ➦ `{after.channel.category}.{after.channel.name}`'
            color = discord.Color.blue()
            fields = [
                (f'Duration in {before.channel.name}',
                f'{formatted_duration}'),
                (f'Users in {before.channel.name}',
                util.user_list(before.channel)),
                (f'Users in {after.channel.name}',
                util.user_list(after.channel))
            ]
            await util.send_embed(log_channel, title, description, color, None, fields, None, thumbnail_url=avatar_url)
        util.store_last_seen(member.guild.id, member.id)



async def run_bot():
    while True:
        try:
            await bot.start(config.DISCORD_TOKEN)  # Replace TOKEN with your bot token
        except (discord.ConnectionClosed, discord.GatewayNotFound, discord.HTTPException) as exc:
            print(f"Connection error occurred: {exc}, trying to reconnect...")

            # Wait for bot to be ready with a timeout
            try:
                await asyncio.wait_for(bot.wait_until_ready(), timeout=60)
            except asyncio.TimeoutError:
                print("Reconnect failed, restarting the bot...")
                await bot.close()
        except discord.errors.LoginFailure:
            print(
                "An improper token was provided. Please check your token and try again.")
            await bot.close()
        except KeyboardInterrupt:
            await bot.close()
            break
        except Exception as exc:
            print(f"An unexpected error occurred: {exc}")
            await bot.close()
            break

if __name__ == "__main__":
    asyncio.run(run_bot())

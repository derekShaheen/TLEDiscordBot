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
user_joined = set()

tle_prefix = '!'

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=tle_prefix, intents=intents)

# bot.add_command(cmds.move)
# bot.add_command(cmds.set_log_channel)
# bot.add_command(cmds.toggle_logging)

# Initialize the bot
@bot.event
async def on_ready():
    config = util.load_config(bot.guilds[0].id)
    print("----------------------")
    print("Logged in as")
    print("\tUsername: %s"%bot.user.name)
    print("\tID: %s"%bot.user.id)
    print("\tLog channel:%s"%config['log_channel_name'])
    print("----------------------")

    print("Bot is running on the following servers:")
    for guild in bot.guilds:
        config = util.load_config(guild.id)
        print(f"\tServer: {guild.name} (ID: {guild.id})")
        print(f"\t\tMember count: {len(guild.members)}")

    print("----------------------")

    print("Initializing and scheduling tasks...")
    
    print("Bot Commands:")
    for command in bot.commands:
        print(f"\t!{command.name}")
    

    heartbeat.start()
    daily_report.start()
    check_and_move_users.start()
    print("Ready...")

# Loop section

@tasks.loop(minutes=30)
async def heartbeat():
    for guild in bot.guilds:
        total_users = len(guild.members)
        users_in_voice_chat = sum(1 for member in guild.members if member.voice)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time}\t{guild.name}\tTotal Users: {total_users}\t| Users in Voice Chat: {users_in_voice_chat}")

@tasks.loop(hours=24)
async def check_and_move_users():
    current_time = datetime.datetime.now(pytz.timezone('America/Chicago'))  # Adjust the timezone if needed
    target_time = time(hour=18, minute=00)

    if current_time.time() > target_time:
        for guild in bot.guilds:
            twerk_channel = discord.utils.get(guild.voice_channels, name="Twerk")
            member_general_channel = discord.utils.get(guild.voice_channels, name="Member General")

            if twerk_channel and member_general_channel:
                moved_users_count = 0
                for member in twerk_channel.members:
                    try:
                        await member.move_to(member_general_channel)
                        moved_users_count += 1
                    except discord.errors.HTTPException as e:
                        print(f'Error moving {member.display_name}: {str(e)}')

                if moved_users_count > 0:
                    print(f'\tMoved {util.pluralize(moved_users_count, "user", "users")} from {twerk_channel.name} to {member_general_channel.name}')

@tasks.loop(hours=24)
async def daily_report():
    current_time = datetime.datetime.now(pytz.timezone('America/Chicago'))
    print(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}\tDaily Report: {len(user_joined)} unique users joined a voice channel since yesterday.")
    user_joined.clear()

# Before loop section

@check_and_move_users.before_loop
async def before_check_and_move_users():
    now = datetime.datetime.now(pytz.timezone('America/Chicago'))
    target_time = datetime.time(hour=18, minute=00)
    tomorrow = now.date() + timedelta(days=1)
    next_run = datetime.datetime.combine(tomorrow, target_time, tzinfo=now.tzinfo)
    #print(f"Next twerk move run:{(next_run - now).total_seconds()}")
    await asyncio.sleep((next_run - now).total_seconds())

@daily_report.before_loop
async def before_daily_report():
    now = datetime.datetime.now(pytz.timezone('America/Chicago'))
    target_time = datetime.time(hour=6, minute=00)
    tomorrow = now.date() + timedelta(days=1)
    next_run = datetime.datetime.combine(tomorrow, target_time, tzinfo=now.tzinfo)
    #print(f"Next daily report run:{(next_run - now).total_seconds()}")
    await asyncio.sleep((next_run - now).total_seconds())

# Event section

async def log_event(guild, log_channel_name, title, description, color, timestamp=None):
    config = util.load_config(guild.id)
    if not config.get('logging_enabled', True):
        return

    log_channel = discord.utils.get(guild.text_channels, name=log_channel_name)

    if not log_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        log_channel = await guild.create_text_channel(log_channel_name, overwrites=overwrites)

    embed = discord.Embed(title=title, description=description, color=color, timestamp=timestamp)
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


@bot.event
async def on_voice_state_update(member, before, after):
    # Store the user ID in joined_users set when they join a voice channel
    if before.channel is None and after.channel is not None:
        user_joined.add(member.id)
#     if before.channel != after.channel:
#         config = util.load_config(member.guild.id)
#         log_channel_name = config['log_channel_name']
#         log_channel = discord.utils.get(member.guild.text_channels, name=log_channel_name)

#         if not log_channel:
#             overwrites = {
#                 member.guild.default_role: discord.PermissionOverwrite(read_messages=False)
#             }
#             log_channel = await member.guild.create_text_channel(log_channel_name, overwrites=overwrites)

#         user_id = member.id
#         now = datetime.datetime.utcnow()

#         if before.channel is None:
#             user_join_times[user_id] = now
#             title = f'{member.name} joined a voice channel'
#             description = f'> {member.mention} joined `{after.channel.name}`'
#             color = discord.Color.green()
#             fields = [(f'Users in {after.channel.name}', util.user_list(after.channel))]
#             await util.send_embed(log_channel, title, description, color, fields, now)
#         elif after.channel is None:
#             duration = round((now - user_join_times.pop(user_id, now)).total_seconds())
#             formatted_duration = util.format_duration(duration)
#             title = f'{member.name} left a voice channel'
#             description = f'> {member.mention} left from `{before.channel.name}`'
#             color = discord.Color.red()
#             fields = [
#                 (f'Duration', f'{formatted_duration}'),
#                 (f'Users in {before.channel.name}', util.user_list(before.channel))
#             ]
#             await util.send_embed(log_channel, title, description, color, fields, now)
#         else:
#             duration = round((now - user_join_times.pop(user_id, now)).total_seconds())
#             formatted_duration = util.format_duration(duration)
#             user_join_times[user_id] = now
#             title = f'{member.name} switched voice channels'
#             description = f'> {member.mention} moved from `{before.channel.name}` ➦ `{after.channel.name}`'
#             color = discord.Color.blue()
#             fields = [
#                 (f'Duration in {before.channel.name}', f'{formatted_duration}'),
#                 (f'Users in {before.channel.name}', util.user_list(before.channel)),
#                 (f'Users in {after.channel.name}', util.user_list(after.channel))
#             ]
#             await util.send_embed(log_channel, title, description, color, fields, now)

bot.run(config.TOKEN)
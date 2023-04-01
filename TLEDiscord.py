import config
import datetime
import discord
import util
from discord.ext import commands, tasks

user_join_times = {}

tle_prefix = '!'

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=tle_prefix, intents=intents)

@bot.event
async def on_ready():
    print("----------------------")
    print("Logged In As")
    print("Username: %s"%bot.user.name)
    print("ID: %s"%bot.user.id)
    print("----------------------")

    print("Bot Commands:")
    for command in bot.commands:
        print(f"!{command.name}")

    heartbeat.start()

@tasks.loop(minutes=30)
async def heartbeat():
    for guild in bot.guilds:
        total_users = len(guild.members)
        users_in_voice_chat = sum(1 for member in guild.members if member.voice)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} - {guild.name} - Total Users: {total_users}, Users in Voice Chat: {users_in_voice_chat}")

@bot.command(
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
        await ctx.send('Error: This command can only be used in a server.')
        return

    # Make sure the user has the required role
    allowed_roles = ["Administrator", "Senior Mod"]

    if not any(role.name in allowed_roles for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.")
        return

    # Set source voice channel
    if source_name:
        source_channel = discord.utils.get(ctx.guild.voice_channels, name=source_name)
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
    destination_channel = discord.utils.get(ctx.guild.voice_channels, name=destination_name)
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

@bot.before_invoke
async def log_command(ctx):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'{current_time}\t{ctx.guild.name}\t{ctx.author} used {ctx.message.content}')

async def send_embed(log_channel, title, description, color, fields=None, timestamp=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
    if timestamp:
        embed.timestamp = timestamp
    await log_channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        log_channel_name = 'voice_logs'
        log_channel = discord.utils.get(member.guild.text_channels, name=log_channel_name)

        if not log_channel:
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(read_messages=False)
            }
            log_channel = await member.guild.create_text_channel(log_channel_name, overwrites=overwrites)

        user_id = member.id
        now = datetime.datetime.utcnow()

        if before.channel is None:
            user_join_times[user_id] = now
            title = f'{member.name} joined a voice channel'
            description = f'> {member.mention} joined `{after.channel.name}`'
            color = discord.Color.green()
            fields = [(f'Users in {after.channel.name}', util.user_list(after.channel))]
            await send_embed(log_channel, title, description, color, fields, now)
        elif after.channel is None:
            duration = round((now - user_join_times.pop(user_id, now)).total_seconds())
            formatted_duration = util.format_duration(duration)
            title = f'{member.name} left a voice channel'
            description = f'> {member.mention} left from `{before.channel.name}`'
            color = discord.Color.red()
            fields = [
                (f'Duration', f'{formatted_duration}'),
                (f'Users in {before.channel.name}', util.user_list(before.channel))
            ]
            await send_embed(log_channel, title, description, color, fields, now)
        else:
            duration = round((now - user_join_times.pop(user_id, now)).total_seconds())
            formatted_duration = util.format_duration(duration)
            user_join_times[user_id] = now
            title = f'{member.name} switched voice channels'
            description = f'> {member.mention} moved from `{before.channel.name}` ➦ `{after.channel.name}`'
            color = discord.Color.blue()
            fields = [
                (f'Duration in {before.channel.name}', f'{formatted_duration}'),
                (f'Users in {before.channel.name}', util.user_list(before.channel)),
                (f'Users in {after.channel.name}', util.user_list(after.channel))
            ]
            await send_embed(log_channel, title, description, color, fields, now)

bot.run(config.TOKEN)
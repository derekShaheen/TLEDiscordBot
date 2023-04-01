import config
import datetime
import discord
from discord.ext import commands, tasks

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!', intents=intents)
 
@bot.event
async def on_ready():
    print("----------------------")
    print("Logged In As")
    print("Username: %s"%bot.user.name)
    print("ID: %s"%bot.user.id)
    print("----------------------")
    heartbeat.start()

@tasks.loop(minutes=30)
async def heartbeat():
    for guild in bot.guilds:
        total_users = len(guild.members)
        users_in_voice_chat = sum(1 for member in guild.members if member.voice)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time} - {guild.name} - Total Users: {total_users}, Users in Voice Chat: {users_in_voice_chat}")

@bot.command()
async def move(ctx, source_name: str, destination_name: str):
    # check if user is admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send('You do not have permission to use this command.')
        return
    # get source voice channel
    source_channel = discord.utils.get(ctx.guild.voice_channels, name=source_name)
    if not source_channel:
        await ctx.send(f'Error: could not find source voice channel "{source_name}"')
        return
    # get destination voice channel
    destination_channel = discord.utils.get(ctx.guild.voice_channels, name=destination_name)
    if not destination_channel:
        await ctx.send(f'Error: could not find destination voice channel "{destination_name}"')
        return
    # move all users in source channel to destination channel
    for member in source_channel.members:
        await member.move_to(destination_channel)
    # send confirmation message
    await ctx.send(f'Moved all users from {source_channel.name} to {destination_channel.name}')

@bot.command()
async def moveus(ctx, destination_name: str):
    # check if user is admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send('You do not have permission to use this command.')
        return
    # check if user is in a voice channel
    if not ctx.author.voice:
        await ctx.send('Error: you are not currently in a voice channel.')
        return
    # get source voice channel (user's current voice channel)
    source_channel = ctx.author.voice.channel
    # get destination voice channel
    destination_channel = discord.utils.get(ctx.guild.voice_channels, name=destination_name)
    if not destination_channel:
        await ctx.send(f'Error: could not find destination voice channel "{destination_name}"')
        return
    # move all users in source channel to destination channel
    for member in source_channel.members:
        await member.move_to(destination_channel)
    # send confirmation message
    await ctx.send(f'Moved all users from {source_channel.name} to {destination_channel.name}')


bot.run(config.TOKEN)
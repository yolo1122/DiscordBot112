import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import sys
import subprocess
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

# Fetch the Discord token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Get the YouTube API Key from the .env file
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)  # Disable default help command

# Track bot uptime
bot.start_time = None

# Define the custom help command
@bot.command(name='help', aliases=['h'])
async def help_command(ctx):
    help_text = (
        "**Beschikbare commando's:**\n\n"
        "**!play <url>** - Speelt een nummer af van de opgegeven YouTube URL.\n"
        "**!queue** - Toon de huidige wachtrij van nummers.\n"
        "**!skip** - Slaat het huidige nummer over.\n"
        "**!stop** - Stopt de muziek en verbreekt de verbinding met het spraakkanaal.\n"
        "**!secret** - Dit is een geheim. Of misschien niet.\n"
    )

    try:
        # Send help message to user's DM
        await ctx.author.send(help_text)
        # Send a public message to the channel confirming the DM
        bot_message_1 = await ctx.send("Ik heb je de lijst met commando's in een DM gestuurd!")
        # Delete both the user's command and bot's response after 30 seconds
        await delete_messages(ctx, ctx.message, bot_message_1)
    except discord.Forbidden:
        # If the bot can't send DMs, notify the user in the channel
        bot_message_1 = await ctx.send("Ik kan je geen privébericht sturen. Zorg ervoor dat je DMs van deze server accepteert.")
        # Delete both the user's command and bot's response after 30 seconds
        await delete_messages(ctx, ctx.message, bot_message_1)

# Function to handle deletion of messages after 30 seconds
async def delete_messages(ctx, *messages):
    """Delete all provided messages after 30 seconds."""
    await asyncio.sleep(30)  # Wait for 30 seconds before deleting
    for msg in messages:
        if msg:
            try:
                # Log message content for debugging
                print(f"Attempting to delete message: {msg.content}")

                # Check if the bot can manage messages
                if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                    await msg.delete()
                    print(f"Deleted message ID: {msg.id}, Content: '{msg.content}'")
                else:
                    print("Bot lacks permission to delete messages.")
            except discord.NotFound:
                print(f"Message {msg.id if msg else 'unknown'} was already deleted.")
            except discord.Forbidden:
                print("The bot does not have permission to delete messages.")
            except Exception as e:
                print(f"Error deleting message {msg.id if msg else 'unknown'}: {e}")
        else:
            print("No message to delete.")

# Add the info command
@bot.command(name='info')
async def info(ctx):
    """Info command to provide bot details and contact information."""
    info_message = (
        "**Bot Informatie**\n\n"
        "Deze bot is gemaakt door **jef112**.\n"
        "Het is momenteel in de testfase.\n"
        "Voor problemen of vragen, neem contact op met **jef112**.\n"
    )

    bot_message_1 = await ctx.send(info_message)
    
    # Delete both the user's command and the bot's response after 30 seconds
    await delete_messages(ctx, ctx.message, bot_message_1)

# Load cogs asynchronously inside the on_ready event
@bot.event
async def on_ready():
    global bot
    bot.start_time = datetime.now(timezone.utc)  # Set uptime when the bot is ready
    print(f"{bot.user} is connected and ready to play music!")

    try:
        # Check if the music_commands cog is loaded
        if "cogs.music_commands" not in bot.extensions:
            await bot.load_extension("cogs.music_commands")
            print("Loaded 'music_commands' cog.")

        # Check if the secret_commands cog is loaded
        if "cogs.secret_commands" not in bot.extensions:
            await bot.load_extension("cogs.secret_commands")
            print("Loaded 'secret_commands' cog.")

    except Exception as e:
        print(f"Error loading extension: {e}")

# Debugging for commands that fail message deletion
@bot.event
async def on_command_error(ctx, error):
    print(f"Command error: {error}")
    if isinstance(error, commands.CommandInvokeError):
        print(f"Failed command invoke: {ctx.command}")
    elif isinstance(error, discord.Forbidden):
        print("Bot does not have the required permissions.")
    else:
        print(f"Unhandled error: {type(error).__name__}: {error}")

# Channel lock feature
locked_channel = None  # Variable to store the locked channel

@bot.command(name='channel')
async def set_channel(ctx, channel_id: int = None):
    """Set the channel where the bot will only listen to commands."""
    global locked_channel
    if ctx.author.id == 166575659982782466:  # Check if it's the master
        if channel_id:
            locked_channel = discord.utils.get(ctx.guild.text_channels, id=channel_id)
            if locked_channel:
                bot_message = await ctx.send(f"Bot zal nu alleen commando's accepteren in het kanaal: {locked_channel.mention}")
            else:
                bot_message = await ctx.send("Ongeldig kanaal ID opgegeven.")
        else:
            locked_channel = None
            bot_message = await ctx.send("De bot accepteert nu commando's van elk kanaal.")
        # Delete both the user's command and bot's response after 30 seconds
        await delete_messages(ctx, ctx.message, bot_message)
    else:
        bot_message = await ctx.send("Je hebt geen toestemming om dit commando uit te voeren.")
        # Delete both the user's command and bot's response after 30 seconds
        await delete_messages(ctx, ctx.message, bot_message)

@bot.event
async def on_message(message):
    """Ensure the bot doesn't process its own messages twice."""
    if message.author == bot.user:
        return  # Ignore messages from the bot
    
    global locked_channel
    if locked_channel and message.channel != locked_channel and message.author != bot.user:
        return  # Ignore messages if the locked channel is set
    
    # Process commands after checking the above conditions
    await bot.process_commands(message)

# Define the restart command
@bot.command(name='restart')
async def restart(ctx):
    """Restart the bot."""
    if ctx.author.id == 166575659982782466:  # Check if it's the master
        bot_message = await ctx.send("De bot wordt opnieuw opgestart...")
        await ctx.bot.close()  # Close the bot

        # Get the absolute path of the script
        bot_path = os.path.abspath(__file__)  # Absolute path of the script
        python_executable = sys.executable  # Get the path of the Python interpreter
        print(f"Restarting bot using the path: {bot_path}")

        # Use subprocess to restart the bot
        subprocess.Popen([python_executable, bot_path])  # Use subprocess to launch the bot again
        # Delete both the user's command and bot's response after 30 seconds
        await delete_messages(ctx, ctx.message, bot_message)
    else:
        bot_message = await ctx.send("Je hebt geen toestemming om de bot opnieuw te starten.")
        # Delete both the user's command and bot's response after 30 seconds
        await delete_messages(ctx, ctx.message, bot_message)

# Run the bot
bot.run(DISCORD_TOKEN)
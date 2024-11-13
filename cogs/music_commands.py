import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import psutil  # Importing psutil to manage process termination
from utils import delete_messages  # Import the delete_messages function from utils.py
import logging  # Import the logging module
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("bot_log.log"),  # Logs to file
    logging.StreamHandler()  # Also logs to the console
])

# Create a logger instance
logger = logging.getLogger()

# Set up YouTube download options for yt-dlp
ytdl_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'quiet': False,
    'noplaylist': True,
    'source_address': '0.0.0.0',
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'extractor_args': {
        'youtube': {
            'noplaylist': True,
            'compat-options': 'no-youtube-unavailable-videos',
        }
    },
}

ytdl = youtube_dl.YoutubeDL(ytdl_options)

# Define the YTDLSource class to use yt-dlp and FFmpeg
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, loop=None, download=False):
        loop = loop or asyncio.get_event_loop()

        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None

        if 'entries' in data:
            data = data['entries'][0]  # Get the first song in the playlist
        if 'is_live' in data and data['is_live']:
            filename = data['url']  # Use stream URL for live stream
        else:
            filename = data['url']

        return cls(discord.FFmpegPCMAudio(filename, options="-vn -loglevel debug -report"), data=data)

    # Function to handle FFmpeg process termination gracefully
    async def terminate_ffmpeg_process(self, process):
        try:
            # Check if process is still running and attempt to terminate it
            if psutil.pid_exists(process.pid):
                process.terminate()  # Try to terminate the process
                await asyncio.sleep(2)  # Wait for termination
                if psutil.pid_exists(process.pid):
                    process.kill()  # Force kill if still running
                    logger.error(f"FFmpeg process {process.pid} forcefully killed.")
                else:
                    logger.info(f"FFmpeg process {process.pid} terminated successfully.")
            else:
                logger.warning(f"FFmpeg process {process.pid} was already terminated.")
        except Exception as e:
            logger.error(f"Error while terminating FFmpeg process: {e}")

# Music Commands Cog
class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []

    @commands.command(name="play")
    async def play(self, ctx, url: str):
        """Speel een nummer af van de gegeven URL."""
        try:
            # Controleer of de gebruiker in een spraakkanaal zit
            if not ctx.author.voice:
                bot_message = await ctx.send("Je moet eerst in een spraakkanaal zitten.")
                await delete_messages(ctx, ctx.message, bot_message)  # Deleting both command and bot's response
                logger.info(f"User {ctx.author} tried to play music but was not in a voice channel.")
                return

            # Reageer op basis van de gebruiker
            if ctx.author.id == 166575659982782466:  # Vervang door je master ID
                bot_message = await ctx.send("Yes, master. Het gevraagde nummer wordt afgespeeld.")
            else:
                bot_message = await ctx.send("Het gevraagde nummer wordt afgespeeld.")

            # Sluit aan bij het spraakkanaal van de gebruiker
            voice_channel = ctx.author.voice.channel
            if not ctx.voice_client:
                await voice_channel.connect()

            voice_client = ctx.voice_client

            # Speel het nummer af
            async with ctx.typing():
                player = await YTDLSource.from_url(url, download=False)
                if player:
                    self.song_queue.append(player)
                    if not voice_client.is_playing():
                        voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.song_finished(ctx, e)))
                        bot_message = await ctx.send(f"Nu aan het afspelen: {player.title}")
                    else:
                        bot_message = await ctx.send(f"Toegevoegd aan de wachtrij: {player.title}")
                else:
                    bot_message = await ctx.send("Het nummer ophalen is mislukt.")
                    logger.error(f"Failed to fetch the song at {url}.")

            # Plan de verwijdering van het antwoord en de opdracht
            await delete_messages(ctx, ctx.message, bot_message)  # Deleting both command and bot's response

        except Exception as e:
            bot_message = await ctx.send(f"Er is een fout opgetreden: {e}")
            await delete_messages(ctx, ctx.message, bot_message)  # Deleting both command and bot's response
            logger.error(f"Error in play command: {e}")

    @commands.command(name="queue")
    async def queue(self, ctx):
        """Toon de huidige wachtrij."""
        bot_message = None
        await asyncio.sleep(1)  # 1-seconde vertraging
        if not self.song_queue:
            bot_message = await ctx.send("De wachtrij is leeg!")
        else:
            queue_list = "\n".join([f"{index + 1}. {song.title}" for index, song in enumerate(self.song_queue)])
            bot_message = await ctx.send(f"Huidige wachtrij:\n{queue_list}")

        logger.info(f"Queue displayed for user {ctx.author}")
        await delete_messages(ctx, ctx.message, bot_message)  # Deleting both command and bot's response

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Sla het huidige nummer over."""
        bot_message = None
        voice_client = ctx.voice_client
        await asyncio.sleep(1)  # 1-seconde vertraging
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            bot_message = await ctx.send("Het huidige nummer is overgeslagen!")
        else:
            bot_message = await ctx.send("Er speelt momenteel geen nummer.")

        logger.info(f"Skip command executed by user {ctx.author}")
        await delete_messages(ctx, ctx.message, bot_message)  # Deleting both command and bot's response

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop met afspelen en verbreek de verbinding met het spraakkanaal."""
        bot_message = None
        await asyncio.sleep(1)  # 1-seconde vertraging
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            bot_message = await ctx.send("Verbonden met het spraakkanaal verbroken.")
            self.song_queue.clear()  # Clear the queue when stopping the music
        else:
            bot_message = await ctx.send("De bot is niet verbonden met een spraakkanaal.")

        logger.info(f"Stop command executed by user {ctx.author}")
        await delete_messages(ctx, ctx.message, bot_message)  # Deleting both command and bot's response

    async def song_finished(self, ctx, error):
        """Behandel het afspelen van het volgende nummer."""
        if self.song_queue:
            self.song_queue.pop(0)  # Verwijder het nummer uit de wachtrij nadat het is afgelopen
            if self.song_queue:
                next_song = self.song_queue[0]
                ctx.voice_client.play(next_song, after=lambda e: self.bot.loop.create_task(self.song_finished(ctx, e)))
                bot_message = await ctx.send(f"Nu aan het afspelen: {next_song.title}")
                logger.info(f"Now playing next song: {next_song.title}")
                await delete_messages(ctx, bot_message)  # Deleting the bot's response after 30 seconds

# Add the setup function at the bottom of the file
async def setup(bot):
    await bot.add_cog(MusicCommands(bot))

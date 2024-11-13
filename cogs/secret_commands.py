import discord
from discord.ext import commands
import random
import asyncio
from utils import delete_messages  # Import the delete_messages function from utils.py
import logging  # Import the logging module

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("bot_log.log"),  # Logs to file
    logging.StreamHandler()  # Also logs to the console
])

# Create a logger instance
logger = logging.getLogger()

# Define compliments and insults
compliments = [
    "Je bent geweldig!", "Je doet het geweldig!", "Blijf doorgaan, je bent fantastisch!"
]
insults = [
    "Je kunt het beter doen.", "Dit is niet je beste zet.", "Probeer het volgende keer harder."
]

class SecretCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def secret(self, ctx):
        """Behandelt het geheime commando.""" 
        # Controleer of de auteur de master is (ID 166575659982782466)
        if ctx.author.id == 166575659982782466:
            compliment = random.choice(compliments)
            try:
                target_user = await ctx.bot.fetch_user(852208731814887434)
                insult = random.choice(insults)
                if target_user:
                    message = await ctx.send(f"{compliment} En wat betreft {target_user.mention}, {insult}")
                    logger.info(f"Secret command: Compliment given to master with insult directed at {target_user.mention}")
                else:
                    message = await ctx.send(f"{compliment} En wat betreft die gebruiker, {insult}")
                    logger.warning(f"Failed to fetch target user for insult, sending generic message.")
            except Exception as e:
                message = await ctx.send(f"Er is een fout opgetreden: {e}")
                logger.error(f"Error in secret command: {e}")

            # Verwijder het commando bericht en de bot reactie na 30 seconden
            await delete_messages(ctx, ctx.message, message)

        else:
            insult = random.choice(insults)
            try:
                master = await ctx.bot.fetch_user(166575659982782466)
                if master:
                    message = await ctx.send(f"{ctx.author.mention}, {insult} Maar master {master.mention}, {random.choice(compliments)}")
                    logger.info(f"Secret command: Insult sent to user with compliment for master {master.mention}")
                else:
                    message = await ctx.send(f"{ctx.author.mention}, {insult} Maar master, {random.choice(compliments)}")
                    logger.warning(f"Failed to fetch master user for compliment.")
            except Exception as e:
                message = await ctx.send(f"Er is een fout opgetreden: {e}")
                logger.error(f"Error in secret command for master: {e}")

            # Verwijder het commando bericht en de bot reactie na 30 seconden
            await delete_messages(ctx, ctx.message, message)

# Add the setup function at the bottom of the file
async def setup(bot):
    await bot.add_cog(SecretCommands(bot))

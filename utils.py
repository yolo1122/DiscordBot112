import discord
import asyncio
import logging

# Create a logger instance for utility functions
logger = logging.getLogger()

async def delete_messages(ctx, command_message, bot_message=None):
    """
    Delete the provided messages after 30 seconds.
    - command_message: the command message to delete
    - bot_message: the bot's response message to delete
    """
    try:
        # Delete the command message
        await asyncio.sleep(30)
        await command_message.delete()
        logger.info(f"Deleted command message from {ctx.author}.")

        # If bot_message exists, delete it after 30 seconds
        if bot_message:
            await bot_message.delete()
            logger.info(f"Deleted bot response message for {ctx.author}.")
    except discord.DiscordException as e:
        logger.error(f"Error deleting message: {e}")

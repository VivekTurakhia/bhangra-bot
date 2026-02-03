import discord
from discord.ext import commands
import asyncio
import logging
import config
from keep_alive import keep_alive

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Validate configuration
try:
    bot_config = config.validate_config()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    logger.error("Please update your .env file with the correct values:")
    logger.error("  - GUILD_ID: Your Discord server ID (right-click server name -> Copy ID)")
    logger.error("  - ANNOUNCEMENT_CHANNEL_ID: Channel where announcements should be sent")
    exit(1)

# Configure bot intents
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True  # For future message listening features

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('------')

    # Sync slash commands with the guild
    try:
        guild = discord.Object(id=bot_config['guild_id'])
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        logger.info(f'Synced slash commands to guild {bot_config["guild_id"]}')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f'Error: {error}')


async def load_extensions():
    """Load all cogs."""
    cogs = [
        'cogs.basic',
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f'Loaded extension: {cog}')
        except Exception as e:
            logger.error(f'Failed to load extension {cog}: {e}')


async def main():
    """Main function to start the bot."""
    # Start Flask keep-alive server for Repl.it
    keep_alive()
    logger.info('Keep-alive server started on port 8080')

    # Load extensions
    await load_extensions()

    # Start the bot
    try:
        await bot.start(bot_config['token'])
    except KeyboardInterrupt:
        logger.info('Bot shutting down...')
        await bot.close()


if __name__ == '__main__':
    asyncio.run(main())

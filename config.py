import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
ANNOUNCEMENT_CHANNEL_ID = os.getenv('ANNOUNCEMENT_CHANNEL_ID')

# Validate required environment variables
def validate_config():
    """Validate that all required environment variables are set."""
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env file")
    if not GUILD_ID:
        raise ValueError("GUILD_ID is not set in .env file")
    if not ANNOUNCEMENT_CHANNEL_ID:
        raise ValueError("ANNOUNCEMENT_CHANNEL_ID is not set in .env file")

    # Convert IDs to integers
    try:
        return {
            'token': DISCORD_TOKEN,
            'guild_id': int(GUILD_ID),
            'announcement_channel_id': int(ANNOUNCEMENT_CHANNEL_ID)
        }
    except ValueError as e:
        raise ValueError(f"Invalid ID format in .env file: {e}")

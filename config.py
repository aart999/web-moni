"""
Configuration module for NetInspect Bot.

Loads and validates environment variables required by the application.
All config values are accessed through this module for consistency.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_bot_token() -> str:
    """Return the Telegram bot token from environment variables.

    Raises:
        ValueError: If BOT_TOKEN is not set or is empty.

    Returns:
        The bot token string.
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError(
            "BOT_TOKEN is not set. "
            "Create a .env file or set the environment variable."
        )
    return token

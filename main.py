"""
NetInspect Bot — real-time website diagnostics and network analysis.

Entry point.  Registers handlers, configures logging, and starts
long-polling via the python-telegram-bot library.

Usage
-----
    python main.py
"""

import sys

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)

from config import get_bot_token
from handlers import (
    analyze,
    check,
    dns,
    error_handler,
    headers,
    help_command,
    history,
    ping,
    report,
    ssl,
    start,
)
from utils.logger import logger


def main() -> None:
    """Initialise and run the NetInspect Bot."""
    logger.info("=" * 50)
    logger.info("NetInspect Bot starting up ...")

    try:
        token = get_bot_token()
    except ValueError as exc:
        logger.critical("Startup failed: %s", exc)
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()

    # ---- Register commands ------------------------------------------------
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("dns", dns))
    app.add_handler(CommandHandler("ssl", ssl))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("headers", headers))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("history", history))

    # ---- Global error handler --------------------------------------------
    app.add_error_handler(error_handler)

    logger.info("Bot is ready — polling for updates ...")
    app.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()

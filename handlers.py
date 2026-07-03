"""
Command handlers for NetInspect Bot.

Implements every Telegram bot command, applies rate limiting, logs
results to the in-memory history store, and returns formatted messages.
"""

import json
from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

from services.analyzer import analyze_website
from services.dns_checker import check_dns
from services.http_checker import check_http
from services.history_store import history_store
from services.ping_checker import check_ping
from services.security_analyzer import analyze_security_headers
from services.ssl_checker import check_ssl
from utils.helpers import bytes_to_kb
from utils.logger import logger
from utils.rate_limiter import RateLimiter

# Singleton rate limiter for all handlers
_rate_limiter = RateLimiter(cooldown=5.0)


# ---------------------------------------------------------------------------
# Decorator-like helper
# ---------------------------------------------------------------------------

async def _rate_limited(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check rate limit and inform the user if they need to wait.

    Args:
        update: The Telegram update.
        context: The callback context.

    Returns:
        True if the request is allowed, False otherwise.
    """
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    if not _rate_limiter.is_allowed(chat_id):
        remaining = _rate_limiter.remaining_seconds(chat_id)
        msg = (
            f"⏳ Please wait {remaining:.0f} seconds before your next request."
        )
        await update.message.reply_text(msg)  # type: ignore[union-attr]
        return False
    return True


def _store(chat_id: int, command: str, url: str, data: Dict[str, Any]) -> None:
    """Record a command result in the user's history.

    Args:
        chat_id: Telegram chat identifier.
        command: The command that was invoked (e.g. ``/check``).
        url: The target URL or hostname.
        data: The result data dict.
    """
    history_store.add(chat_id, {
        "command": command,
        "url": url,
        "data": data,
    })


async def _typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a typing indicator while processing."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,  # type: ignore[union-attr]
        action="typing",
    )


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command — welcome message."""
    user = update.effective_user  # type: ignore[union-attr]
    logger.info("User %s started the bot.", user.id)
    msg = (
        f"👋 *Welcome, {user.first_name}!*\n\n"  # type: ignore[union-attr]
        "I am *NetInspect Bot* — your real-time website diagnostics and "
        "network analysis tool.\n\n"
        "Send /help to see available commands."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command — show available commands."""
    logger.info("Help command invoked.")
    msg = (
        "🤖 *NetInspect Bot — Help*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "`/start` — Welcome message\n\n"
        "`/check <url>` — HTTP status, response time, page title, server, size\n\n"
        "`/dns <url>` — DNS resolution & lookup time\n\n"
        "`/ssl <url>` — TLS certificate details & expiry\n\n"
        "`/ping <url>` — ICMP latency statistics\n\n"
        "`/headers <url>` — Useful HTTP response headers\n\n"
        "`/analyze <url>` — Full diagnostic report (all checks)\n\n"
        "`/report <url>` — JSON-formatted diagnostic report\n\n"
        "`/history` — Your last 10 queries\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📌 *Example:* `/check example.com`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /check
# ---------------------------------------------------------------------------

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /check — basic HTTP diagnostic."""
    if not await _rate_limited(update, context):
        return
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    url = _get_url(context)
    if not url:
        await update.message.reply_text(  # type: ignore[union-attr]
            "⚠️ Usage: `/check <url>`\nExample: `/check example.com`",
            parse_mode="Markdown",
        )
        return

    await _typing(update, context)
    logger.info("/check %s by user %s", url, chat_id)
    http = check_http(url)
    _store(chat_id, "/check", url, {"http_status": http.status_code})

    if http.error:
        await update.message.reply_text(  # type: ignore[union-attr]
            f"🔴 *Check failed*\n{http.error}", parse_mode="Markdown"
        )
        return

    status_icon = "🟢" if http.status_code < 400 else "🟡"
    msg = (
        f"{status_icon} *HTTP Check — {url}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Status:* {http.status_code} {http.reason}\n"
        f"⚡ *Response Time:* {http.response_time_ms} ms\n"
        f"📑 *Title:* {http.title}\n"
        f"🖥 *Server:* {http.server}\n"
        f"📦 *Content-Type:* {http.content_type}\n"
        f"🔗 *Final URL:* {http.final_url}\n"
        f"📏 *Size:* {bytes_to_kb(http.content_length)}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /dns
# ---------------------------------------------------------------------------

async def dns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dns — DNS resolution."""
    if not await _rate_limited(update, context):
        return
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    url = _get_url(context)
    if not url:
        await update.message.reply_text(  # type: ignore[union-attr]
            "⚠️ Usage: `/dns <url>`\nExample: `/dns example.com`",
            parse_mode="Markdown",
        )
        return

    await _typing(update, context)
    logger.info("/dns %s by user %s", url, chat_id)
    result = check_dns(url)
    _store(chat_id, "/dns", url, {"ips": result.ip_addresses})

    if result.error:
        await update.message.reply_text(  # type: ignore[union-attr]
            f"🔴 *DNS Lookup Failed*\n{result.error}", parse_mode="Markdown"
        )
        return

    ips = ", ".join(result.ip_addresses) if result.ip_addresses else "N/A"
    msg = (
        f"🌍 *DNS Lookup — {result.hostname}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Hostname:* {result.hostname}\n"
        f"🌐 *IP Address(es):* {ips}\n"
        f"⏱ *Lookup Time:* {result.lookup_time_ms} ms"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /ssl
# ---------------------------------------------------------------------------

async def ssl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ssl — TLS certificate inspection."""
    if not await _rate_limited(update, context):
        return
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    url = _get_url(context)
    if not url:
        await update.message.reply_text(  # type: ignore[union-attr]
            "⚠️ Usage: `/ssl <url>`\nExample: `/ssl example.com`",
            parse_mode="Markdown",
        )
        return

    await _typing(update, context)
    logger.info("/ssl %s by user %s", url, chat_id)
    result = check_ssl(url)
    _store(chat_id, "/ssl", url, {"ssl_days_remaining": result.days_remaining})

    if result.error:
        await update.message.reply_text(  # type: ignore[union-attr]
            f"🔴 *SSL Check Failed*\n{result.error}", parse_mode="Markdown"
        )
        return

    msg = (
        f"🔒 *SSL/TLS Certificate — {result.common_name}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📛 *Common Name:* {result.common_name}\n"
        f"🏛 *Issuer:* {result.issuer}\n"
        f"📅 *Expires:* {result.not_after.strftime('%Y-%m-%d')}\n"
        f"⏳ *Days Remaining:* {result.days_remaining}\n"
        f"🔐 *TLS Version:* {result.tls_version}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /ping
# ---------------------------------------------------------------------------

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ping — ICMP latency statistics."""
    if not await _rate_limited(update, context):
        return
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    url = _get_url(context)
    if not url:
        await update.message.reply_text(  # type: ignore[union-attr]
            "⚠️ Usage: `/ping <url>`\nExample: `/ping example.com`",
            parse_mode="Markdown",
        )
        return

    await _typing(update, context)
    logger.info("/ping %s by user %s", url, chat_id)
    result = check_ping(url)
    _store(chat_id, "/ping", url, {"avg_latency_ms": result.avg_latency_ms})

    if result.error:
        await update.message.reply_text(  # type: ignore[union-attr]
            f"🔴 *Ping Failed*\n{result.error}", parse_mode="Markdown"
        )
        return

    msg = (
        f"📡 *Ping Statistics — {result.hostname}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Average:* {result.avg_latency_ms} ms\n"
        f"⬆ *Minimum:* {result.min_latency_ms} ms\n"
        f"⬇ *Maximum:* {result.max_latency_ms} ms\n"
        f"📦 *Packet Loss:* {result.packet_loss}/4"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /headers
# ---------------------------------------------------------------------------

async def headers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /headers — display useful HTTP headers."""
    if not await _rate_limited(update, context):
        return
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    url = _get_url(context)
    if not url:
        await update.message.reply_text(  # type: ignore[union-attr]
            "⚠️ Usage: `/headers <url>`\nExample: `/headers example.com`",
            parse_mode="Markdown",
        )
        return

    await _typing(update, context)
    logger.info("/headers %s by user %s", url, chat_id)
    http = check_http(url)
    _store(chat_id, "/headers", url, {"headers": http.headers})

    if http.error:
        await update.message.reply_text(  # type: ignore[union-attr]
            f"🔴 *Headers Failed*\n{http.error}", parse_mode="Markdown"
        )
        return

    # Show only security-relevant + common headers
    interesting = [
        "server",
        "content-type",
        "strict-transport-security",
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
        "cache-control",
        "set-cookie",
    ]
    header_lines = []
    for key in interesting:
        value = http.headers.get(key, http.headers.get(key.capitalize(), None))
        if value:
            header_lines.append(f"`{key}`: {value[:200]}")

    if not header_lines:
        header_lines.append("No common headers found.")

    msg = (
        f"📋 *HTTP Headers — {url}*\n"
        "━━━━━━━━━━━━━━━━━━\n" + "\n".join(header_lines)
    )
    await update.message.reply_text(msg, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /analyze
# ---------------------------------------------------------------------------

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /analyze — full diagnostic report."""
    if not await _rate_limited(update, context):
        return
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    url = _get_url(context)
    if not url:
        await update.message.reply_text(  # type: ignore[union-attr]
            "⚠️ Usage: `/analyze <url>`\nExample: `/analyze example.com`",
            parse_mode="Markdown",
        )
        return

    await _typing(update, context)
    logger.info("/analyze %s by user %s", url, chat_id)
    message, data = analyze_website(url)
    _store(chat_id, "/analyze", url, data)
    await update.message.reply_text(message, parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /report
# ---------------------------------------------------------------------------

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /report — JSON-formatted report."""
    if not await _rate_limited(update, context):
        return
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    url = _get_url(context)
    if not url:
        await update.message.reply_text(  # type: ignore[union-attr]
            "⚠️ Usage: `/report <url>`\nExample: `/report example.com`",
            parse_mode="Markdown",
        )
        return

    await _typing(update, context)
    logger.info("/report %s by user %s", url, chat_id)
    _, data = analyze_website(url)
    _store(chat_id, "/report", url, data)
    json_str = json.dumps(data, indent=2, default=str)

    # Telegram has a 4096 character message limit; truncate if needed
    if len(json_str) > 4000:
        json_str = json_str[:4000] + "\n... (truncated)"

    await update.message.reply_text(  # type: ignore[union-attr]
        f"```json\n{json_str}\n```", parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# /history
# ---------------------------------------------------------------------------

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history — show last 10 queries."""
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    entries = history_store.get(chat_id)

    if not entries:
        await update.message.reply_text(  # type: ignore[union-attr]
            "📭 No history yet. Run a command like `/check example.com` to get started.",
            parse_mode="Markdown",
        )
        return

    lines = ["📜 *Your Recent Queries*\n━━━━━━━━━━━━━━━━━━"]
    for i, entry in enumerate(entries[:10], 1):
        lines.append(f"{i}. `{entry['command']}` — {entry['url']}")
    lines.append("━━━━━━━━━━━━━━━━━━")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# /error handler
# ---------------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log and suppress exceptions without exposing stack traces."""
    logger.error("Unhandled exception: %s", context.error, exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An unexpected error occurred. Please try again."
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_url(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    """Extract the URL argument from the command context.

    Args:
        context: The callback context.

    Returns:
        The URL string or None if no argument was provided.
    """
    if context.args:
        return " ".join(context.args)
    return None

<div align="center">

# 🌐 NetInspect Bot

**Real-time website diagnostics & network analysis — right from Telegram.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.10-green)](https://github.com/python-telegram-bot/python-telegram-bot)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 Overview

NetInspect Bot is a **production-quality Telegram bot** that performs live network diagnostics on-demand. Send a URL and instantly get back HTTP status, DNS resolution, TLS certificate details, ICMP latency, security header analysis, and more.

> **⚠️ This is NOT an uptime monitor.**  
> Every check is triggered manually by the user. There are no scheduled scans, no databases, and no persistent state.

Built with clean architecture, comprehensive error handling, and a modular service layer — this is a project a junior engineer would be proud to showcase on GitHub or during an interview.

---

## 🏗 Architecture

```
netinspect-bot/
├── main.py                  # Entry point — registers handlers & starts polling
├── config.py                # Environment variable loading & validation
├── handlers.py              # All Telegram command handlers
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── LICENSE                  # MIT License
├── .gitignore               # Git exclusion rules
├── .env.example             # Environment template
├── services/
│   ├── __init__.py
│   ├── http_checker.py      # HTTP GET — status, headers, title, size
│   ├── dns_checker.py       # Hostname resolution & lookup time
│   ├── ssl_checker.py       # TLS certificate inspection
│   ├── ping_checker.py      # ICMP round-trip latency
│   ├── security_analyzer.py # Security header scoring engine
│   ├── analyzer.py          # Orchestrates all services for /analyze
│   ├── history_store.py     # In-memory per-user history (last 10)
│   └── report_builder.py    # JSON report assembly
└── utils/
    ├── __init__.py
    ├── logger.py            # File + console logging (bot.log)
    ├── rate_limiter.py      # 5-second per-user cooldown
    └── helpers.py           # URL normalisation, domain extraction, formatting
```

### Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility** | Each file does one thing (e.g. `dns_checker.py` only resolves DNS). |
| **Clean Architecture** | Services are independent; handlers only coordinate. |
| **No Side Effects** | Services accept input and return dataclasses — no shared state. |
| **Graceful Degradation** | Every service returns a result object even on failure. |

---

## ✨ Features

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Command reference |
| `/check <url>` | HTTP status, response time, page title, server, content type, size |
| `/dns <url>` | DNS lookup — IP addresses & resolution time |
| `/ssl <url>` | TLS certificate — common name, issuer, expiry, protocol version |
| `/ping <url>` | ICMP latency — average, min, max, packet loss |
| `/headers <url>` | Security-relevant HTTP response headers |
| `/analyze <url>` | **Full diagnostic report** — runs every service at once |
| `/report <url>` | Structured JSON report of all diagnostics |
| `/history` | Last 10 queries per user (in-memory) |

### 🔒 Security Scoring Engine

Every `/analyze` report includes a **0–100 security score** based on:

| Header | Weight |
|--------|--------|
| `Strict-Transport-Security` | 30 pts |
| `Content-Security-Policy` | 25 pts |
| `X-Frame-Options` | 15 pts |
| `X-Content-Type-Options` | 15 pts |
| `Referrer-Policy` | 10 pts |
| `Permissions-Policy` | 5 pts |

Scoring comes with actionable recommendations for improvement.

### ⏱ Rate Limiting

Users can send **one request every 5 seconds**. Exceeding the limit returns a friendly cooldown message.

### 📝 Logging

All events (startup, commands, errors, successful requests) are logged to `bot.log` with timestamps and severity levels.

---

## 📦 Installation

### Prerequisites

- Python **3.12+**
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/netinspect-bot.git
cd netinspect-bot

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # Linux / macOS
venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

---

## 🤖 BotFather Setup

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts.
3. Copy the API token you receive.
4. Paste it into your `.env` file:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklmNOPqrstUVwxyz
```

5. (Optional) Set your bot's commands with `/setcommands`:

```
start - Welcome message
help - Show available commands
check - HTTP diagnostic for a website
dns - DNS lookup for a domain
ssl - TLS certificate inspection
ping - ICMP ping statistics
headers - Show HTTP headers
analyze - Full diagnostic report
report - JSON diagnostic report
history - Your recent queries
```

---

## 🚀 Running Locally

```bash
python main.py
```

You should see:

```
2026-07-03 12:00:00 | INFO     | netinspect | ==================================================
2026-07-03 12:00:00 | INFO     | netinspect | NetInspect Bot starting up ...
2026-07-03 12:00:00 | INFO     | netinspect | Bot is ready — polling for updates ...
```

Now open Telegram, find your bot, and send `/start`!

---

## ☁️ Oracle Cloud Deployment

### Option 1: Direct (tmux / screen)

```bash
# SSH into your Oracle Cloud instance
ssh ubuntu@<your-instance-ip>

# Install Python & dependencies
sudo apt update && sudo apt install -y python3 python3-pip git
git clone https://github.com/your-username/netinspect-bot.git
cd netinspect-bot
pip3 install -r requirements.txt

# Create .env with your BOT_TOKEN
nano .env

# Run in a persistent tmux session
tmux new -s netinspect
python3 main.py
# Detach: Ctrl+B, D
# Reattach: tmux attach -t netinspect
```

### Option 2: Systemd Service (auto-restart)

Create `/etc/systemd/system/netinspect-bot.service`:

```ini
[Unit]
Description=NetInspect Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/netinspect-bot
ExecStart=/usr/bin/python3 /home/ubuntu/netinspect-bot/main.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/netinspect-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable netinspect-bot
sudo systemctl start netinspect-bot
sudo systemctl status netinspect-bot
```

---

## 📸 Screenshots

<!-- Add screenshots here after deployment -->

| Command | Preview |
|---------|---------|
| `/check example.com` | |
| `/ssl example.com` | |
| `/analyze example.com` | |

---

## 🔧 Future Improvements

- [ ] **Async DNS resolver** — Replace `socket.getaddrinfo` with `aiodns` for non-blocking lookups.
- [ ] **WHOIS lookup** — Domain registration information.
- [ ] **Traceroute** — Network path analysis.
- [ ] **HTTP/2 & HTTP/3 detection** — Protocol negotiation check.
- [ ] **Port scanner** — Common open ports.
- [ ] **Customisable rate limit** — Per-user configurable cooldown.
- [ ] **Exportable reports** — Shareable HTML/PDF summaries.
- [ ] **Docker support** — Containerised deployment.

---

## 🤝 Contributing

Contributions are welcome! Open an issue or submit a pull request.

1. Fork the repository.
2. Create a feature branch (`git checkout -b feat/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feat/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">
Made with ❤️ for the Telegram community
</div>

# Quant Telegram Bot

A minimal, reusable Telegram bot library for quantitative trading notifications.

## Features

- **Async-first**: Non-blocking integration with trading loops
- **Smart throttling**: Intelligent rate limiting by message type
- **Template-based**: Pre-built message formats for common scenarios
- **Minimal dependencies**: Only `python-telegram-bot` + standard library
- **Context-aware**: Emergency alerts bypass throttling

## Quick Start

```python
from quant_telegram import TelegramBot

bot = TelegramBot()

# Price alerts
await bot.price_alert("BTCUSDT", 45000, "spike", change_pct=5.2)

# Position updates
await bot.position_update("hyperliquid", "ETHUSDT", 1.5, 250.0, action="opened")

# Emergency notifications (no throttling)
await bot.emergency_alert("Funding arbitrage opportunity: 15bps spread!")
```

## Configuration

Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

## Installation

```bash
pip install -e .
```
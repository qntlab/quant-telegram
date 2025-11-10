"""Basic usage examples for quant-telegram."""

import asyncio
import os
from quant_telegram import TelegramBot


async def main():
    """Demonstrate basic bot usage."""
    
    # Initialize bot (reads from environment variables)
    # Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first
    bot = TelegramBot()
    
    print("Sending example notifications...")
    
    # Price alert examples
    await bot.price_alert("BTCUSDT", 45000, "spike", change_pct=5.2)
    await bot.price_alert("ETHUSDT", 3200, "breakout", change_pct=3.1, volume=15000)
    
    # Position update examples
    await bot.position_update("hyperliquid", "BTCUSDT", 1.5, 250.0, action="opened", 
                             entry_price=44800)
    await bot.position_update("paradex", "ETHUSDT", -2.0, -120.0, action="closed", 
                             exit_price=3180, fees=15.50)
    
    # System alerts
    await bot.system_alert("warning", "High latency detected", exchange="paradex")
    await bot.system_alert("error", "Failed to connect to exchange API", 
                          component="market_data")
    
    # Emergency alert (bypasses throttling)
    await bot.emergency_alert("Funding arbitrage opportunity: 15bps spread!", 
                             action_required="Check funding rates immediately")
    
    # Custom message
    await bot.custom_message("🤖 Trading bot started successfully", throttle_seconds=0)
    
    # Wait a bit for messages to process
    await asyncio.sleep(2)
    
    # Cleanup
    await bot.cleanup()
    print("Example completed!")


if __name__ == "__main__":
    # Make sure to set your environment variables:
    # export TELEGRAM_BOT_TOKEN="your_bot_token"
    # export TELEGRAM_CHAT_ID="your_chat_id"
    
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("Please set TELEGRAM_BOT_TOKEN environment variable")
        print("Get your bot token from @BotFather on Telegram")
        exit(1)
        
    if not os.getenv("TELEGRAM_CHAT_ID"):
        print("Please set TELEGRAM_CHAT_ID environment variable")
        print("Send a message to your bot, then check:")
        print("https://api.telegram.org/bot<YourBOTToken>/getUpdates")
        exit(1)
    
    asyncio.run(main())
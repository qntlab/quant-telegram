"""Main TelegramBot class for quant-telegram."""

import asyncio
import logging
from typing import Optional, Union, Dict, Any

try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    Bot = None
    TelegramError = Exception

from ..utils.config import Config
from .formatter import MessageFormatter
from .throttle import MessageThrottle


class TelegramBot:
    """Main Telegram bot class for trading notifications."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the bot with configuration."""
        self.config = config or Config.from_env()
        self.formatter = MessageFormatter()
        self.throttle = MessageThrottle()
        self._bot: Optional[Bot] = None
        self._logger = logging.getLogger(__name__)
        
        # Initialize bot if telegram library is available
        if Bot is not None:
            self._bot = Bot(token=self.config.bot_token)
        else:
            self._logger.warning("python-telegram-bot not installed. Bot will log messages instead.")
    
    async def _send_message(self, message: str) -> bool:
        """Send message to Telegram chat."""
        try:
            if self._bot is not None:
                await self._bot.send_message(
                    chat_id=self.config.chat_id,
                    text=message,
                    parse_mode=self.config.parse_mode,
                    disable_web_page_preview=self.config.disable_web_page_preview
                )
                self._logger.debug(f"Message sent: {message[:100]}...")
                return True
            else:
                # Fallback: log the message
                self._logger.info(f"TELEGRAM: {message}")
                return True
                
        except TelegramError as e:
            self._logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            self._logger.error(f"Unexpected error sending message: {e}")
            return False
    
    async def price_alert(self, symbol: str, price: float, trigger_type: str, 
                         change_pct: Optional[float] = None, **kwargs) -> bool:
        """Send price alert notification."""
        message = self.formatter.price_alert(
            symbol=symbol,
            price=price,
            trigger_type=trigger_type,
            change_pct=change_pct,
            **kwargs
        )
        
        # Use symbol as throttle key for per-symbol rate limiting
        throttle_key = symbol
        
        if await self.throttle.should_send_immediately(
            "price_alert", self.config.throttle.price_alert, throttle_key
        ):
            return await self._send_message(message)
        else:
            # Queue for batched sending
            await self.throttle.queue_message(
                "price_alert", self.config.throttle.price_alert, 
                message, self._send_message, throttle_key
            )
            return True
    
    async def position_update(self, exchange: str, symbol: str, size: float, 
                            pnl: float, action: str = "update", **kwargs) -> bool:
        """Send position update notification."""
        message = self.formatter.position_update(
            exchange=exchange,
            symbol=symbol,
            size=size,
            pnl=pnl,
            action=action,
            **kwargs
        )
        
        # Use exchange as throttle key for batching by exchange
        throttle_key = exchange
        
        if await self.throttle.should_send_immediately(
            "position_update", self.config.throttle.position_update, throttle_key
        ):
            return await self._send_message(message)
        else:
            await self.throttle.queue_message(
                "position_update", self.config.throttle.position_update,
                message, self._send_message, throttle_key
            )
            return True
    
    async def system_alert(self, level: str, message: str, **kwargs) -> bool:
        """Send system alert notification."""
        formatted_message = self.formatter.system_alert(level, message, **kwargs)
        
        # Use level as throttle key
        throttle_key = level
        
        if await self.throttle.should_send_immediately(
            "system_alert", self.config.throttle.system_alert, throttle_key
        ):
            return await self._send_message(formatted_message)
        else:
            await self.throttle.queue_message(
                "system_alert", self.config.throttle.system_alert,
                formatted_message, self._send_message, throttle_key
            )
            return True
    
    async def emergency_alert(self, message: str, **kwargs) -> bool:
        """Send emergency alert (bypasses all throttling)."""
        formatted_message = self.formatter.emergency_alert(message, **kwargs)
        return await self._send_message(formatted_message)
    
    async def custom_message(self, message: str, throttle_seconds: int = 0, 
                           throttle_key: str = "custom", **kwargs) -> bool:
        """Send custom formatted message."""
        if throttle_seconds == 0:
            return await self._send_message(message)
        
        if await self.throttle.should_send_immediately(
            "custom", throttle_seconds, throttle_key
        ):
            return await self._send_message(message)
        else:
            await self.throttle.queue_message(
                "custom", throttle_seconds, message, self._send_message, throttle_key
            )
            return True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.throttle.cleanup()
        self._logger.info("TelegramBot cleanup completed")
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        try:
            if hasattr(self, 'throttle'):
                # Try to run cleanup if event loop is available
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.cleanup())
        except:
            pass  # Ignore cleanup errors during deletion
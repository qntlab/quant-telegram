"""Main TelegramBot class for quant-telegram."""

import asyncio
import logging
from typing import Optional, Union, Dict, Any, Callable, List, Tuple

try:
    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.error import TelegramError
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler
except ImportError:
    Bot = None
    TelegramError = Exception
    InlineKeyboardButton = None
    InlineKeyboardMarkup = None
    Application = None

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
        
        # Interactive features
        self.application = None
        self.callbacks_registry: Dict[str, Callable] = {}
        self.commands_registry: Dict[str, Callable] = {}
        self.button_configs: Dict[str, Dict] = {}
        
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
    
    def register_callback(self, name: str, callback: Callable, description: str = ""):
        """Register a data callback function."""
        self.callbacks_registry[name] = callback
        self._logger.debug(f"Registered callback: {name} - {description}")
    
    def register_command(self, command: str, callback: Callable, description: str = ""):
        """Register a command handler."""
        self.commands_registry[command] = callback
        self._logger.debug(f"Registered command: /{command} - {description}")
    
    def configure_buttons(self, message_type: str, buttons: List[Tuple[str, str, str]]):
        """Configure buttons for a message type.
        
        Args:
            message_type: Type of message (e.g., 'positions', 'portfolio')
            buttons: List of (button_text, callback_data, callback_name) tuples
        """
        self.button_configs[message_type] = {
            'buttons': buttons
        }
        self._logger.debug(f"Configured {len(buttons)} buttons for {message_type}")
    
    def enable_interactive_features(self):
        """Enable interactive features with registered callbacks and commands."""
        if Application is None:
            self._logger.warning("telegram.ext not available. Interactive features disabled.")
            return False
        
        self.application = Application.builder().token(self.config.bot_token).build()
        
        # Add dynamic command handlers
        for command, handler in self.commands_registry.items():
            self.application.add_handler(CommandHandler(command, self._wrap_command_handler(handler)))
            self._logger.debug(f"Added command handler: /{command}")
        
        # Add callback query handler
        self.application.add_handler(CallbackQueryHandler(self._handle_dynamic_callback))
        
        self._logger.info(f"Interactive features enabled with {len(self.commands_registry)} commands")
        return True
    
    async def send_message_with_buttons(self, message_type: str, data_callback_name: str, 
                                      formatter_method: str, chat_id=None, **kwargs):
        """Send a message with configured buttons."""
        try:
            # Get data from callback
            if data_callback_name in self.callbacks_registry:
                data = await self.callbacks_registry[data_callback_name]()
            else:
                data = []
            
            # Format message using specified formatter method
            if hasattr(self.formatter, formatter_method):
                message = getattr(self.formatter, formatter_method)(data, **kwargs)
            else:
                message = str(data)
            
            # Build buttons if configured
            reply_markup = None
            if message_type in self.button_configs and InlineKeyboardMarkup:
                buttons = []
                for button_text, callback_data, callback_name in self.button_configs[message_type]['buttons']:
                    buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                reply_markup = InlineKeyboardMarkup(buttons)
            
            target_chat_id = chat_id or self.config.chat_id
            
            if reply_markup:
                await self._bot.send_message(target_chat_id, message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await self._send_message(message)
                
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to send {message_type} message: {e}")
            await self._send_message(f"ERROR: {e}")
            return False
    
    def _wrap_command_handler(self, handler: Callable):
        """Wrap user command handler to provide consistent interface."""
        async def wrapper(update, _context):
            try:
                # Call user handler with update object
                await handler(update, self)
            except Exception as e:
                self._logger.error(f"Command handler error: {e}")
                await update.message.reply_text(f"ERROR: {e}")
        return wrapper
    
    async def _handle_dynamic_callback(self, update, _context):
        """Handle dynamic callback queries based on configuration."""
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data to find the right handler
            callback_data = query.data
            
            # Find matching button configuration
            for message_type, config in self.button_configs.items():
                for button_text, data, callback_name in config['buttons']:
                    if data == callback_data and callback_name in self.callbacks_registry:
                        # Execute the callback and update message
                        fresh_data = await self.callbacks_registry[callback_name]()
                        
                        # Use appropriate formatter
                        formatter_method = getattr(self.formatter, f"{message_type}_summary", None)
                        if formatter_method:
                            new_message = formatter_method(fresh_data)
                        else:
                            new_message = str(fresh_data)
                        
                        # Rebuild buttons
                        buttons = []
                        for btn_text, btn_data, _ in config['buttons']:
                            buttons.append([InlineKeyboardButton(btn_text, callback_data=btn_data)])
                        reply_markup = InlineKeyboardMarkup(buttons)
                        
                        await query.edit_message_text(new_message, reply_markup=reply_markup, parse_mode='HTML')
                        return
            
            await query.edit_message_text("ERROR: Unknown action")
            
        except Exception as e:
            self._logger.error(f"Callback handler error: {e}")
            await query.edit_message_text(f"ERROR: {e}")
    
    # Legacy methods for backward compatibility
    async def show_positions(self, chat_id=None):
        """Show positions (legacy method)."""
        return await self.send_message_with_buttons(
            "positions", "get_positions", "positions_summary", chat_id
        )
    
    
    async def start_interactive_mode(self):
        """Start interactive bot (polling mode)."""
        if not self.application:
            self._logger.error("Interactive features not enabled. Call enable_interactive_features() first.")
            return False
        
        self._logger.info("Starting interactive bot in polling mode")
        await self.application.run_polling()
        return True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.throttle.cleanup()
        if self.application:
            await self.application.shutdown()
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
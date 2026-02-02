"""Configuration management for quant-telegram."""

import os
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class ThrottleSettings:
    """Throttling configuration for different message types."""
    emergency: int = 0          # No throttling for emergencies
    price_alert: int = 60       # 1 minute between price alerts per symbol
    position_update: int = 30   # 30 seconds batch window for positions
    system_alert: int = 120     # 2 minutes between system alerts


@dataclass
class Config:
    """Main configuration class for quant-telegram."""

    bot_token: str
    chat_id: str
    throttle: ThrottleSettings
    parse_mode: str = "HTML"
    disable_web_page_preview: bool = True
    message_thread_id: Optional[int] = None
    
    @classmethod
    def from_env(cls, **overrides) -> "Config":
        """Create config from environment variables."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")
        
        # Allow throttle overrides from environment
        throttle_settings = ThrottleSettings(
            emergency=int(os.getenv("THROTTLE_EMERGENCY", 0)),
            price_alert=int(os.getenv("THROTTLE_PRICE_ALERT", 60)),
            position_update=int(os.getenv("THROTTLE_POSITION_UPDATE", 30)),
            system_alert=int(os.getenv("THROTTLE_SYSTEM_ALERT", 120)),
        )
        
        thread_id_str = os.getenv("TELEGRAM_MESSAGE_THREAD_ID")
        message_thread_id = int(thread_id_str) if thread_id_str else None

        config = cls(
            bot_token=bot_token,
            chat_id=chat_id,
            throttle=throttle_settings,
            message_thread_id=message_thread_id,
            **overrides
        )

        return config
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        throttle_dict = config_dict.get("throttle", {})
        throttle_settings = ThrottleSettings(**throttle_dict)
        
        return cls(
            bot_token=config_dict["bot_token"],
            chat_id=config_dict["chat_id"],
            throttle=throttle_settings,
            parse_mode=config_dict.get("parse_mode", "HTML"),
            disable_web_page_preview=config_dict.get("disable_web_page_preview", True),
            message_thread_id=config_dict.get("message_thread_id"),
        )
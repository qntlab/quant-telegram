"""Message formatting utilities for quant-telegram."""

from datetime import datetime
from typing import Optional, Union


class MessageFormatter:
    """Handles message formatting and templating."""
    
    @staticmethod
    def timestamp() -> str:
        """Get current timestamp in UTC format."""
        return datetime.utcnow().strftime("%H:%M UTC")
    
    @staticmethod
    def format_price(price: Union[float, int], decimals: int = 2) -> str:
        """Format price with appropriate decimals."""
        if price >= 1000:
            return f"{price:,.{decimals}f}"
        elif price >= 1:
            return f"{price:.{decimals}f}"
        else:
            # For small prices, show more decimals
            return f"{price:.6f}".rstrip('0').rstrip('.')
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """Format percentage with + or - sign."""
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.{decimals}f}%"
    
    @staticmethod
    def format_pnl(pnl: float, currency: str = "USD") -> str:
        """Format PnL with appropriate color and currency."""
        emoji = "🟢" if pnl >= 0 else "🔴"
        sign = "+" if pnl >= 0 else ""
        return f"{emoji} {sign}${pnl:,.2f}"
    
    @classmethod
    def price_alert(cls, symbol: str, price: float, trigger_type: str, 
                   change_pct: Optional[float] = None, **kwargs) -> str:
        """Format price alert message."""
        timestamp = cls.timestamp()
        formatted_price = cls.format_price(price)
        
        # Determine emoji based on trigger type
        emoji_map = {
            "spike": "🚨",
            "drop": "📉", 
            "breakout": "🚀",
            "breakdown": "⬇️",
            "target": "🎯",
            "alert": "🔔"
        }
        emoji = emoji_map.get(trigger_type.lower(), "📊")
        
        message = f"{emoji} <b>{symbol}</b> ${formatted_price}"
        
        if change_pct is not None:
            pct_str = cls.format_percentage(change_pct)
            message += f" ({pct_str})"
        
        message += f" - {trigger_type.title()} at {timestamp}"
        
        # Add any additional context
        if "volume" in kwargs:
            message += f"\n📈 Volume: {kwargs['volume']:,.0f}"
        if "context" in kwargs:
            message += f"\n💬 {kwargs['context']}"
            
        return message
    
    @classmethod
    def position_update(cls, exchange: str, symbol: str, size: float, pnl: float, 
                       action: str = "update", **kwargs) -> str:
        """Format position update message."""
        timestamp = cls.timestamp()
        
        # Action emojis
        action_emojis = {
            "opened": "📈",
            "closed": "📊", 
            "increased": "⬆️",
            "decreased": "⬇️",
            "update": "🔄"
        }
        emoji = action_emojis.get(action.lower(), "📊")
        
        # Format size
        size_str = f"{abs(size):.4f}".rstrip('0').rstrip('.')
        side = "Long" if size > 0 else "Short"
        
        # Format PnL
        pnl_str = cls.format_pnl(pnl)
        
        message = f"{emoji} <b>{action.title()}</b> {size_str} {symbol} on {exchange.title()}"
        message += f"\n💰 PnL: {pnl_str}"
        message += f"\n📍 {side} | {timestamp}"
        
        # Add optional details
        if "entry_price" in kwargs:
            message += f"\n💵 Entry: ${cls.format_price(kwargs['entry_price'])}"
        if "exit_price" in kwargs:
            message += f"\n💸 Exit: ${cls.format_price(kwargs['exit_price'])}"
        if "fees" in kwargs:
            message += f"\n💸 Fees: ${kwargs['fees']:.2f}"
            
        return message
    
    @classmethod
    def system_alert(cls, level: str, message: str, **kwargs) -> str:
        """Format system alert message."""
        timestamp = cls.timestamp()
        
        # Level emojis and formatting
        level_map = {
            "info": ("ℹ️", "Info"),
            "warning": ("⚠️", "Warning"), 
            "error": ("❌", "Error"),
            "critical": ("🚨", "CRITICAL")
        }
        emoji, level_text = level_map.get(level.lower(), ("📝", level.title()))
        
        formatted_message = f"{emoji} <b>{level_text}</b> | {timestamp}\n{message}"
        
        # Add context if provided
        if "component" in kwargs:
            formatted_message += f"\n🔧 Component: {kwargs['component']}"
        if "exchange" in kwargs:
            formatted_message += f"\n🏦 Exchange: {kwargs['exchange']}"
            
        return formatted_message
    
    @classmethod
    def emergency_alert(cls, message: str, **kwargs) -> str:
        """Format emergency alert (highest priority)."""
        timestamp = cls.timestamp()
        formatted_message = f"⚡ <b>URGENT</b> | {timestamp}\n{message}"
        
        if "action_required" in kwargs:
            formatted_message += f"\n🎯 Action: {kwargs['action_required']}"
            
        return formatted_message
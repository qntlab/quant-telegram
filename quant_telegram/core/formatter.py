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
        """Format PnL with appropriate sign and currency."""
        sign = "+" if pnl >= 0 else ""
        return f"{sign}${pnl:,.2f}"
    
    @classmethod
    def price_alert(cls, symbol: str, price: float, trigger_type: str, 
                   change_pct: Optional[float] = None, **kwargs) -> str:
        """Format price alert message."""
        timestamp = cls.timestamp()
        formatted_price = cls.format_price(price)
        
        message = f"ALERT: <b>{symbol}</b> ${formatted_price}"
        
        if change_pct is not None:
            pct_str = cls.format_percentage(change_pct)
            message += f" ({pct_str})"
        
        message += f" - {trigger_type.title()} at {timestamp}"
        
        # Add any additional context
        if "volume" in kwargs:
            message += f"\nVolume: {kwargs['volume']:,.0f}"
        if "context" in kwargs:
            message += f"\nContext: {kwargs['context']}"
            
        return message
    
    @classmethod
    def position_update(cls, exchange: str, symbol: str, size: float, pnl: float, 
                       action: str = "update", **kwargs) -> str:
        """Format position update message."""
        timestamp = cls.timestamp()
        
        # Format size
        size_str = f"{abs(size):.4f}".rstrip('0').rstrip('.')
        side = "Long" if size > 0 else "Short"
        
        # Format PnL
        pnl_str = cls.format_pnl(pnl)
        
        message = f"POSITION: <b>{action.title()}</b> {size_str} {symbol} on {exchange.title()}"
        message += f"\nPnL: {pnl_str}"
        message += f"\nSide: {side} | {timestamp}"
        
        # Add optional details
        if "entry_price" in kwargs:
            message += f"\nEntry: ${cls.format_price(kwargs['entry_price'])}"
        if "exit_price" in kwargs:
            message += f"\nExit: ${cls.format_price(kwargs['exit_price'])}"
        if "fees" in kwargs:
            message += f"\nFees: ${kwargs['fees']:.2f}"
            
        return message
    
    @classmethod
    def system_alert(cls, level: str, message: str, **kwargs) -> str:
        """Format system alert message."""
        timestamp = cls.timestamp()
        
        # Level formatting
        level_map = {
            "info": "INFO",
            "warning": "WARNING", 
            "error": "ERROR",
            "critical": "CRITICAL"
        }
        level_text = level_map.get(level.lower(), level.title())
        
        formatted_message = f"<b>{level_text}</b> | {timestamp}\n{message}"
        
        # Add context if provided
        if "component" in kwargs:
            formatted_message += f"\nComponent: {kwargs['component']}"
        if "exchange" in kwargs:
            formatted_message += f"\nExchange: {kwargs['exchange']}"
            
        return formatted_message
    
    @classmethod
    def emergency_alert(cls, message: str, **kwargs) -> str:
        """Format emergency alert (highest priority)."""
        timestamp = cls.timestamp()
        formatted_message = f"<b>URGENT</b> | {timestamp}\n{message}"
        
        if "action_required" in kwargs:
            formatted_message += f"\nAction Required: {kwargs['action_required']}"
            
        return formatted_message
    
    @classmethod
    def positions_summary(cls, positions) -> str:
        """Format positions summary with PnL."""
        if not positions:
            return "<b>POSITIONS</b>\nNo open positions"
        
        if isinstance(positions[0], dict) and 'error' in positions[0]:
            return f"<b>ERROR</b>: {positions[0]['error']}"
        
        lines = ["<b>OPEN POSITIONS</b>\n"]
        total_pnl = 0
        
        for pos in positions:
            pnl = pos.get('pnl', 0)
            
            symbol = pos.get('symbol', 'Unknown')
            size = pos.get('size', 0)
            entry_price = pos.get('entry_price', 0)
            side = pos.get('side', 'Long' if size > 0 else 'Short')
            
            # Format position line
            size_abs = abs(size)
            entry_str = cls.format_price(entry_price)
            pnl_str = cls.format_pnl(pnl)
            
            lines.append(f"<b>{symbol}</b> | {side}")
            lines.append(f"  Size: {size_abs:.4f} @ ${entry_str}")
            lines.append(f"  PnL: {pnl_str}")
            lines.append("")  # Empty line for spacing
            
            total_pnl += pnl
        
        # Remove last empty line and add total
        if lines and lines[-1] == "":
            lines.pop()
        
        lines.append(f"\n<b>Total PnL: {cls.format_pnl(total_pnl)}</b>")
        
        return "\n".join(lines)
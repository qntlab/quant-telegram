"""Example of configurable TelegramBot with QuantPyLib integration."""

import asyncio
from quant_telegram import TelegramBot
# from quantpylib.wrappers.binance import BinanceWrapper


class ConfigurableTradingBot:
    def __init__(self):
        self.bot = TelegramBot()
        # self.binance = BinanceWrapper()  # Your QuantPyLib wrapper
        
        self.setup_bot_configuration()
    
    def setup_bot_configuration(self):
        """Configure the bot with callbacks, commands, and buttons."""
        
        # 1. Register data callbacks
        self.bot.register_callback("get_positions", self.get_positions_data, "Fetch current positions")
        self.bot.register_callback("get_portfolio", self.get_portfolio_data, "Fetch portfolio summary")
        self.bot.register_callback("get_pnl", self.get_pnl_data, "Fetch daily P&L")
        self.bot.register_callback("get_alerts", self.get_active_alerts, "Fetch active alerts")
        
        # 2. Register command handlers
        self.bot.register_command("positions", self.handle_positions_command, "Show positions")
        self.bot.register_command("portfolio", self.handle_portfolio_command, "Show portfolio")
        self.bot.register_command("pnl", self.handle_pnl_command, "Show P&L")
        self.bot.register_command("status", self.handle_status_command, "Show system status")
        
        # 3. Configure buttons for different message types
        self.bot.configure_buttons("positions", [
            ("Refresh", "refresh_positions", "get_positions"),
            ("P&L", "show_pnl", "get_pnl"),
            ("Portfolio", "show_portfolio", "get_portfolio")
        ])
        
        self.bot.configure_buttons("portfolio", [
            ("Refresh", "refresh_portfolio", "get_portfolio"),
            ("Positions", "show_positions", "get_positions"),
            ("Alerts", "show_alerts", "get_alerts")
        ])
        
        self.bot.configure_buttons("pnl", [
            ("Refresh", "refresh_pnl", "get_pnl"),
            ("Details", "show_positions", "get_positions")
        ])
        
        # 4. Enable interactive features
        self.bot.enable_interactive_features()
    
    # Data callback implementations
    async def get_positions_data(self):
        """Fetch positions from QuantPyLib."""
        try:
            # Example: Replace with actual QuantPyLib call
            # positions = await self.binance.get_positions()
            # return [{'symbol': p.symbol, 'size': p.size, 'pnl': p.unrealized_pnl, ...} for p in positions]
            
            # Mock data for example
            return [
                {
                    'symbol': 'BTCUSDT',
                    'size': 0.1,
                    'entry_price': 45000,
                    'pnl': 120.50,
                    'side': 'LONG'
                },
                {
                    'symbol': 'ETHUSDT', 
                    'size': -1.5,
                    'entry_price': 2800,
                    'pnl': -45.20,
                    'side': 'SHORT'
                }
            ]
        except Exception as e:
            return [{'error': f"Failed to fetch positions: {e}"}]
    
    async def get_portfolio_data(self):
        """Fetch portfolio summary."""
        try:
            # Mock data - replace with actual API calls
            return {
                'total_balance': 10250.75,
                'available_balance': 8500.30,
                'total_pnl': 75.30,
                'open_positions': 2,
                'daily_volume': 15000.0
            }
        except Exception as e:
            return {'error': f"Failed to fetch portfolio: {e}"}
    
    async def get_pnl_data(self):
        """Fetch P&L data."""
        try:
            return {
                'daily_pnl': 75.30,
                'weekly_pnl': 420.15,
                'monthly_pnl': 1250.80,
                'total_realized': 5600.25,
                'total_unrealized': 75.30
            }
        except Exception as e:
            return {'error': f"Failed to fetch P&L: {e}"}
    
    async def get_active_alerts(self):
        """Fetch active alerts."""
        return [
            {'type': 'price', 'symbol': 'BTCUSDT', 'trigger': 46000, 'message': 'Resistance level'},
            {'type': 'system', 'level': 'warning', 'message': 'High API latency detected'}
        ]
    
    # Command handlers
    async def handle_positions_command(self, update, _):
        """Handle /positions command."""
        await self.bot.send_message_with_buttons("positions", "get_positions", "positions_summary")
        await update.message.reply_text("Positions sent.")
    
    async def handle_portfolio_command(self, update, _):
        """Handle /portfolio command."""
        await self.bot.send_message_with_buttons("portfolio", "get_portfolio", "portfolio_summary")
        await update.message.reply_text("Portfolio sent.")
    
    async def handle_pnl_command(self, update, _):
        """Handle /pnl command."""
        await self.bot.send_message_with_buttons("pnl", "get_pnl", "pnl_summary")
        await update.message.reply_text("P&L sent.")
    
    async def handle_status_command(self, update, _):
        """Handle /status command."""
        status_msg = "SYSTEM STATUS: Healthy\\n" + \
                    "Last update: 30 seconds ago\\n" + \
                    "Active strategies: 3"
        await update.message.reply_text(status_msg)
    
    # Trading integration methods
    async def send_trade_alert(self, symbol, action, size, price):
        """Send trade execution alert."""
        await self.bot.position_update(
            exchange="binance",
            symbol=symbol,
            size=size,
            pnl=0,  # Calculate based on your logic
            action=action,
            entry_price=price
        )
    
    async def send_positions_update(self):
        """Send positions update with refresh button."""
        await self.bot.send_message_with_buttons("positions", "get_positions", "positions_summary")
    
    async def run_trading_strategy(self):
        """Example trading strategy that sends updates."""
        while True:
            # Your trading logic here
            await asyncio.sleep(60)  # Check every minute
            
            # Send periodic updates
            await self.send_positions_update()
    
    async def start(self):
        """Start both trading and telegram bot."""
        # Start interactive telegram bot in the background
        bot_task = asyncio.create_task(self.bot.start_interactive_mode())
        
        # Start your trading strategy
        strategy_task = asyncio.create_task(self.run_trading_strategy())
        
        # Wait for either to complete (they should run forever)
        await asyncio.gather(bot_task, strategy_task)


# Add formatters to handle new message types
def add_custom_formatters():
    """Add custom formatters for portfolio and P&L."""
    from quant_telegram.core.formatter import MessageFormatter
    
    @classmethod
    def portfolio_summary(cls, data):
        if isinstance(data, dict) and 'error' in data:
            return f"<b>ERROR</b>: {data['error']}"
        
        lines = ["<b>PORTFOLIO SUMMARY</b>\\n"]
        lines.append(f"Total Balance: ${data.get('total_balance', 0):,.2f}")
        lines.append(f"Available: ${data.get('available_balance', 0):,.2f}")
        lines.append(f"Total P&L: ${data.get('total_pnl', 0):+,.2f}")
        lines.append(f"Open Positions: {data.get('open_positions', 0)}")
        lines.append(f"Daily Volume: ${data.get('daily_volume', 0):,.0f}")
        return "\\n".join(lines)
    
    @classmethod
    def pnl_summary(cls, data):
        if isinstance(data, dict) and 'error' in data:
            return f"<b>ERROR</b>: {data['error']}"
        
        lines = ["<b>P&L SUMMARY</b>\\n"]
        lines.append(f"Daily: ${data.get('daily_pnl', 0):+,.2f}")
        lines.append(f"Weekly: ${data.get('weekly_pnl', 0):+,.2f}")
        lines.append(f"Monthly: ${data.get('monthly_pnl', 0):+,.2f}")
        lines.append(f"Realized: ${data.get('total_realized', 0):+,.2f}")
        lines.append(f"Unrealized: ${data.get('total_unrealized', 0):+,.2f}")
        return "\\n".join(lines)
    
    # Dynamically add methods to MessageFormatter
    MessageFormatter.portfolio_summary = portfolio_summary
    MessageFormatter.pnl_summary = pnl_summary


async def main():
    """Main entry point."""
    # Add custom formatters
    add_custom_formatters()
    
    # Create and start bot
    trading_bot = ConfigurableTradingBot()
    await trading_bot.start()


if __name__ == "__main__":
    asyncio.run(main())
"""Example integration with a trading system."""

import asyncio
import random
from datetime import datetime
from quant_telegram import TelegramBot


class MockTradingSystem:
    """Mock trading system to demonstrate integration."""
    
    def __init__(self):
        self.bot = TelegramBot()
        self.positions = {}
        self.last_prices = {"BTCUSDT": 45000, "ETHUSDT": 3200}
    
    async def monitor_prices(self):
        """Simulate price monitoring with alerts."""
        while True:
            for symbol, last_price in self.last_prices.items():
                # Simulate price movement
                change = random.uniform(-0.05, 0.05)  # -5% to +5%
                new_price = last_price * (1 + change)
                self.last_prices[symbol] = new_price
                
                # Alert on significant moves
                change_pct = change * 100
                if abs(change_pct) > 2.0:  # Alert on >2% moves
                    trigger_type = "spike" if change_pct > 0 else "drop"
                    await self.bot.price_alert(
                        symbol, new_price, trigger_type, 
                        change_pct=change_pct,
                        context="Automated price monitoring"
                    )
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def simulate_trading(self):
        """Simulate trading activity with notifications."""
        exchanges = ["hyperliquid", "paradex", "binance"]
        symbols = ["BTCUSDT", "ETHUSDT"]
        
        while True:
            # Random trade
            exchange = random.choice(exchanges)
            symbol = random.choice(symbols)
            size = random.uniform(0.1, 2.0) * random.choice([1, -1])  # Long or short
            entry_price = self.last_prices[symbol]
            
            # Open position
            position_key = f"{exchange}:{symbol}"
            self.positions[position_key] = {
                "size": size,
                "entry_price": entry_price,
                "open_time": datetime.utcnow()
            }
            
            await self.bot.position_update(
                exchange, symbol, size, 0.0, "opened",
                entry_price=entry_price
            )
            
            # Wait and then close with random PnL
            await asyncio.sleep(random.uniform(60, 180))  # Hold 1-3 minutes
            
            exit_price = self.last_prices[symbol]
            pnl = (exit_price - entry_price) * abs(size) * (1 if size > 0 else -1)
            
            await self.bot.position_update(
                exchange, symbol, size, pnl, "closed",
                exit_price=exit_price,
                fees=random.uniform(5, 25)
            )
            
            del self.positions[position_key]
            
            await asyncio.sleep(random.uniform(30, 120))  # Wait before next trade
    
    async def system_monitoring(self):
        """Simulate system health monitoring."""
        while True:
            # Random system events
            if random.random() < 0.1:  # 10% chance per minute
                events = [
                    ("warning", "High latency detected", {"exchange": "paradex"}),
                    ("info", "Funding rate updated", {"context": "Next funding in 30 min"}),
                    ("warning", "Low account balance", {"exchange": "hyperliquid"}),
                ]
                
                level, message, kwargs = random.choice(events)
                await self.bot.system_alert(level, message, **kwargs)
            
            # Very rare critical alert
            if random.random() < 0.01:  # 1% chance
                await self.bot.emergency_alert(
                    "Unusual market volatility detected!",
                    action_required="Review open positions"
                )
            
            await asyncio.sleep(60)  # Check every minute
    
    async def run(self):
        """Run the mock trading system."""
        print("Starting mock trading system with Telegram notifications...")
        
        # Run all monitoring tasks concurrently
        await asyncio.gather(
            self.monitor_prices(),
            self.simulate_trading(),
            self.system_monitoring(),
        )
    
    async def cleanup(self):
        """Clean up resources."""
        await self.bot.cleanup()


async def main():
    """Run the trading system demo."""
    system = MockTradingSystem()
    
    try:
        await system.run()
    except KeyboardInterrupt:
        print("\nShutting down trading system...")
        await system.cleanup()


if __name__ == "__main__":
    print("Mock Trading System with Telegram Notifications")
    print("=" * 50)
    print("This demo will:")
    print("- Monitor price movements and send alerts")
    print("- Simulate trading with position notifications")
    print("- Send system health alerts")
    print("- Demonstrate emergency notifications")
    print("\nPress Ctrl+C to stop\n")
    
    asyncio.run(main())
import aiohttp
from typing import Dict, Optional
from datetime import datetime
from backend.config import Config

class MarketService:
    def __init__(self):
        self.api_key = Config.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"

    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time stock data"""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_stock_data(data)
                return None

    @classmethod
    def get_market_indicators(cls):
        """Class method to get market indicators"""
        return cls()._get_market_indicators_sync()

    def _get_market_indicators_sync(self):
        """Synchronous version of market indicators"""
        # Implement synchronous HTTP calls if needed
        return {
            "sp500": {"price": 4500, "change": +1.5},
            "nasdaq": {"price": 15000, "change": +2.1}
        }

    @classmethod
    def get_market_summary(cls):
        """Class method to get formatted market summary"""
        instance = cls()
        indicators = instance._get_market_indicators_sync()
        return f"Market Summary: S&P 500 at {indicators['sp500']['price']} (+{indicators['sp500']['change']}%)"

    async def _get_market_indicators(self) -> Dict:
        """Instance method for actual implementation"""
        indicators = {}
        sp500_data = await self.get_stock_data("SPY")
        if sp500_data:
            indicators["sp500"] = sp500_data
        return indicators

    def _parse_stock_data(self, raw_data: Dict) -> Dict:
        """Parse and format stock data"""
        quote = raw_data.get("Global Quote", {})
        return {
            "symbol": quote.get("01. symbol"),
            "price": float(quote.get("05. price", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%"),
            "volume": int(quote.get("06. volume", 0)),
            "timestamp": datetime.now().isoformat()
        } 
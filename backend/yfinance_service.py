"""
Yahoo Finance Integration Service
Provides real-time market data for stocks, ETFs, and cryptocurrency
"""

import yfinance as yf
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class YFinanceService:
    """Service for fetching financial data using yfinance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes cache
    
    def _get_cache_key(self, symbol: str) -> str:
        """Generate cache key for symbol"""
        return f"yfinance_{symbol.upper()}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_timeout
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """Set data in cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_asset_info(self, symbol: str, asset_type: str = "stocks") -> Optional[Dict]:
        """
        Get comprehensive asset information from Yahoo Finance
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
            asset_type: Type of asset ('stocks', 'etfs', 'crypto')
        
        Returns:
            Dictionary with asset information or None if not found
        """
        try:
            cache_key = self._get_cache_key(symbol)
            cached_data = self._get_from_cache(cache_key)
            
            if cached_data:
                logger.debug(f"Returning cached data for {symbol}")
                return cached_data
            
            logger.info(f"Fetching data for {symbol} ({asset_type})")
            
            # Handle crypto symbols - ensure they have the right suffix
            if asset_type == "crypto":
                if not symbol.upper().endswith("-USD"):
                    symbol = f"{symbol.upper()}-USD"
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get recent price data
            hist = ticker.history(period="5d", interval="1d")
            
            if hist.empty:
                logger.warning(f"No price data found for {symbol}")
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            
            # Calculate 24h change if we have at least 2 days of data
            change_24h = 0.0
            if len(hist) >= 2:
                previous_price = float(hist['Close'].iloc[-2])
                if previous_price > 0:
                    change_24h = ((current_price - previous_price) / previous_price) * 100
            
            # Extract relevant information based on asset type
            asset_data = {
                'symbol': symbol.upper(),
                'name': info.get('longName', info.get('shortName', symbol)),
                'current_price': current_price,
                'change_24h': change_24h,
                'last_updated': datetime.utcnow().isoformat(),
                'asset_type': asset_type
            }
            
            # Add type-specific fields
            if asset_type == "stocks":
                asset_data.update({
                    'company': info.get('longName', ''),
                    'sector': info.get('sector', ''),
                    'market': info.get('exchange', ''),
                    'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                })
            
            elif asset_type == "etfs":
                asset_data.update({
                    'fund_name': info.get('longName', ''),
                    'expense_ratio': info.get('annualReportExpenseRatio', 0) * 100 if info.get('annualReportExpenseRatio') else 0,
                    'category': info.get('category', ''),
                    'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                })
            
            elif asset_type == "crypto":
                asset_data.update({
                    'market_cap': info.get('marketCap', 0),
                    'volume_24h': info.get('volume', 0)
                })
            
            # Cache the result
            self._set_cache(cache_key, asset_data)
            
            logger.info(f"Successfully fetched data for {symbol}: ${current_price:.2f}")
            return asset_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_multiple_quotes(self, symbols: List[str], asset_type: str = "stocks") -> Dict[str, Dict]:
        """
        Get quotes for multiple symbols efficiently
        
        Args:
            symbols: List of ticker symbols
            asset_type: Type of assets
            
        Returns:
            Dictionary mapping symbols to their data
        """
        results = {}
        
        # Process symbols in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            for symbol in batch:
                data = self.get_asset_info(symbol, asset_type)
                if data:
                    results[symbol] = data
                else:
                    logger.warning(f"Failed to get data for {symbol}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
        
        return results
    
    def refresh_prices(self, assets: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Refresh current prices for a list of assets
        
        Args:
            assets: List of asset dictionaries with 'symbol' and 'asset_type' fields
            
        Returns:
            Tuple of (updated_assets, failed_assets)
        """
        updated = []
        failed = []
        
        for asset in assets:
            try:
                symbol = asset.get('symbol')
                asset_type = asset.get('asset_type', 'stocks')
                
                if not symbol:
                    failed.append({
                        'asset': asset,
                        'error': 'Missing symbol'
                    })
                    continue
                
                # Clear cache to force fresh data
                cache_key = self._get_cache_key(symbol)
                if cache_key in self.cache:
                    del self.cache[cache_key]
                
                fresh_data = self.get_asset_info(symbol, asset_type)
                
                if fresh_data:
                    asset.update({
                        'current_price': fresh_data['current_price'],
                        'change_24h': fresh_data['change_24h'],
                        'last_updated': fresh_data['last_updated']
                    })
                    updated.append(asset)
                else:
                    failed.append({
                        'asset': asset,
                        'error': 'Failed to fetch current price'
                    })
                    
            except Exception as e:
                logger.error(f"Error refreshing price for {asset.get('symbol', 'unknown')}: {e}")
                failed.append({
                    'asset': asset,
                    'error': str(e)
                })
        
        return updated, failed
    
    def validate_symbol(self, symbol: str, asset_type: str = "stocks") -> bool:
        """
        Validate if a symbol exists and can be fetched
        
        Args:
            symbol: Ticker symbol to validate
            asset_type: Type of asset
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            data = self.get_asset_info(symbol, asset_type)
            return data is not None and data.get('current_price', 0) > 0
        except Exception:
            return False
    
    def search_symbol(self, query: str, asset_type: str = "stocks") -> List[Dict]:
        """
        Search for symbols matching a query (basic implementation)
        
        Note: This is a simple implementation. For production use,
        consider integrating with Yahoo Finance search API or similar service.
        """
        # This is a placeholder implementation
        # In a real-world scenario, you'd want to integrate with a proper search API
        common_symbols = {
            "stocks": [
                {"symbol": "AAPL", "name": "Apple Inc."},
                {"symbol": "GOOGL", "name": "Alphabet Inc."},
                {"symbol": "MSFT", "name": "Microsoft Corporation"},
                {"symbol": "AMZN", "name": "Amazon.com Inc."},
                {"symbol": "TSLA", "name": "Tesla Inc."},
                {"symbol": "NVDA", "name": "NVIDIA Corporation"},
                {"symbol": "META", "name": "Meta Platforms Inc."},
                {"symbol": "NFLX", "name": "Netflix Inc."},
            ],
            "etfs": [
                {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust"},
                {"symbol": "QQQ", "name": "Invesco QQQ Trust"},
                {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF"},
                {"symbol": "IWM", "name": "iShares Russell 2000 ETF"},
            ],
            "crypto": [
                {"symbol": "BTC-USD", "name": "Bitcoin USD"},
                {"symbol": "ETH-USD", "name": "Ethereum USD"},
                {"symbol": "ADA-USD", "name": "Cardano USD"},
                {"symbol": "DOT-USD", "name": "Polkadot USD"},
            ]
        }
        
        query = query.upper()
        matches = []
        
        for item in common_symbols.get(asset_type, []):
            if query in item["symbol"] or query in item["name"].upper():
                matches.append(item)
        
        return matches[:10]  # Return max 10 matches

# Global service instance
yfinance_service = YFinanceService()

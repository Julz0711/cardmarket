#!/usr/bin/env python3
"""
Steam Market Pricing Service with Rate Limiting and Error Handling
"""

import requests
import time
import json
from typing import Optional, Dict, Any

class SteamMarketPricer:
    """Handle Steam Community Market pricing with proper rate limiting"""
    
    def __init__(self):
        self.base_url = 'https://steamcommunity.com/market/priceoverview'
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests
        self.currency_codes = {
            'USD': 1,
            'GBP': 2,
            'EUR': 3,
            'CHF': 4,
            'RUB': 5,
            'KRW': 16,
            'CAD': 20
        }
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_item_price(self, item_name: str, currency: str = 'USD', appid: int = 730) -> Optional[Dict[str, Any]]:
        """
        Get Steam Community Market price for an item
        
        Args:
            item_name: Market hash name of the item
            currency: Currency code (USD, EUR, etc.)
            appid: Steam app ID (730 for CS2)
            
        Returns:
            Dict with price info or None if failed
        """
        
        if currency not in self.currency_codes:
            print(f"Unsupported currency: {currency}")
            return None
        
        self._wait_for_rate_limit()
        
        params = {
            'appid': appid,
            'market_hash_name': item_name,
            'currency': self.currency_codes[currency]
        }
        
        try:
            print(f"Fetching price for: {item_name}")
            response = requests.get(
                self.base_url, 
                params=params,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        return {
                            'success': True,
                            'lowest_price': data.get('lowest_price', 'N/A'),
                            'median_price': data.get('median_price', 'N/A'),
                            'volume': data.get('volume', 'N/A'),
                            'currency': currency
                        }
                    else:
                        print(f"API returned success=false for {item_name}")
                        return None
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    return None
            
            elif response.status_code == 429:
                print(f"Rate limited by Steam API. Try again later.")
                return None
            
            else:
                print(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    def get_multiple_prices(self, items: list, currency: str = 'USD', appid: int = 730) -> Dict[str, Any]:
        """
        Get prices for multiple items with proper rate limiting
        
        Args:
            items: List of item names
            currency: Currency code
            appid: Steam app ID
            
        Returns:
            Dict mapping item names to price data
        """
        results = {}
        
        for item in items:
            price_data = self.get_item_price(item, currency, appid)
            results[item] = price_data
            
        return results

# Test the pricing service
if __name__ == "__main__":
    pricer = SteamMarketPricer()
    
    # Test with some CS2 items
    test_items = [
        'Operation Hydra Case',
        'Chroma Case',
        'AK-47 | Redline (Field-Tested)'
    ]
    
    print("Testing Steam Market Pricing Service...")
    print("=" * 50)
    
    for item in test_items:
        result = pricer.get_item_price(item, 'USD')
        print(f"Item: {item}")
        print(f"Result: {result}")
        print("-" * 30)

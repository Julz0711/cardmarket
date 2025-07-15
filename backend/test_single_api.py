#!/usr/bin/env python3
"""Simple test for Steam API with single item."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.steam_inventory_scraper import SteamMarketPricer
import requests

def test_single_item():
    """Test a single item with Steam API."""
    print("🔍 Testing Single Steam API Call")
    print("=" * 40)
    
    # Test direct API call first
    print("📡 Testing direct Steam API call...")
    url = "https://steamcommunity.com/market/priceoverview"
    params = {
        'appid': 730,
        'market_hash_name': 'AK-47 | Redline (Field-Tested)',
        'currency': 1  # USD
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"JSON Data: {data}")
            
            if data.get('success'):
                print(f"✅ Success! Price: {data.get('lowest_price', 'N/A')}")
            else:
                print("❌ API returned success=false")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("🔧 Testing with our SteamMarketPricer...")
    pricer = SteamMarketPricer()
    result = pricer.get_item_price("AK-47 | Redline (Field-Tested)", use_mock=False)
    
    if result:
        print(f"Result: {result}")
    else:
        print("No result from pricer")

if __name__ == "__main__":
    test_single_item()

#!/usr/bin/env python3
"""
Direct Steam Market API test
"""

import requests
import json

def test_steam_market_api():
    """Test Steam Market API directly"""
    
    # Test with Operation Hydra Case
    url = 'http://steamcommunity.com/market/priceoverview'
    
    params = {
        'appid': 730,
        'market_hash_name': 'Operation Hydra Case',
        'currency': 1  # USD
    }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"JSON Data: {json_data}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
        
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_steam_market_api()

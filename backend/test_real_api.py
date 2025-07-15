#!/usr/bin/env python3
"""
Test actual API request with pricing enabled
"""

import requests
import json

def test_real_api_request():
    """Test the actual API endpoint with pricing enabled"""
    
    api_url = "http://localhost:5000/api/scrape/steam"
    
    # Test data with pricing enabled
    test_data = {
        "steam_id": "76561198205836117",  # The Steam ID from your frontend
        "app_id": "730",  # CS2
        "include_floats": False,
        "include_prices": True,    # Enable pricing
        "enable_pricing": True,    # Enable pricing service
        "headless": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Real API Request with Pricing")
    print("=" * 50)
    print(f"URL: {api_url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        print("📡 Sending request...")
        response = requests.post(
            api_url, 
            json=test_data, 
            headers=headers, 
            timeout=120  # Longer timeout for inventory scraping
        )
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response Status: {data.get('status', 'unknown')}")
            print(f"✅ Message: {data.get('message', 'No message')}")
            
            if 'data' in data:
                scraped_items = data['data'].get('scraped_items', [])
                print(f"✅ Total Items Scraped: {len(scraped_items)}")
                
                # Check pricing on first few items
                print("\n💰 Pricing Analysis:")
                print("-" * 30)
                
                for i, item in enumerate(scraped_items[:3]):
                    print(f"Item {i+1}:")
                    print(f"  Name: {item.get('name', 'Unknown')}")
                    print(f"  Market Hash: {item.get('market_hash_name', 'N/A')}")
                    print(f"  Current Price: {item.get('current_price', 'N/A')}")
                    print(f"  Rarity: {item.get('rarity', 'N/A')}")
                    print(f"  Category: {item.get('item_category', 'N/A')}")
                    print()
                
                # Check if any items have non-zero prices
                priced_items = [item for item in scraped_items if item.get('current_price', 0) > 0]
                print(f"📊 Items with pricing: {len(priced_items)}/{len(scraped_items)}")
                
                if len(priced_items) == 0:
                    print("❌ NO ITEMS HAVE PRICING DATA!")
                    print("🔍 Let's check the first few items to see what's happening...")
                    for item in scraped_items[:2]:
                        print(f"Debug item: {json.dumps(item, indent=2)}")
                
        else:
            print(f"❌ Error {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - inventory scraping can take a while")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_real_api_request()

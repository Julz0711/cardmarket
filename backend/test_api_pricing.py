#!/usr/bin/env python3
"""
Test API endpoints for Steam scraping with pricing
"""

import requests
import json

def test_steam_api_with_pricing():
    """Test the Steam scraping API with pricing enabled"""
    
    api_url = "http://localhost:5000/api/scrape/steam"
    
    # Test data - you can replace with actual Steam ID
    test_data = {
        "steam_id": "76561198123456789",  # Replace with actual Steam ID
        "app_id": "730",  # CS2
        "include_floats": False,  # Keep it simple
        "include_prices": True,   # Enable pricing
        "enable_pricing": True,   # Enable pricing service
        "headless": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing Steam Inventory Scraping API with Pricing...")
    print(f"URL: {api_url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("=" * 60)
    
    try:
        response = requests.post(api_url, json=test_data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Success!")
            print(f"Status: {data.get('status', 'unknown')}")
            print(f"Message: {data.get('message', 'No message')}")
            
            if 'data' in data:
                scraped_items = data['data'].get('scraped_items', [])
                print(f"Scraped Items: {len(scraped_items)}")
                
                # Show first few items with pricing
                for i, item in enumerate(scraped_items[:3]):
                    print(f"\nItem {i+1}:")
                    print(f"  Name: {item.get('name', 'Unknown')}")
                    print(f"  Rarity: {item.get('rarity', 'Unknown')}")
                    print(f"  Condition: {item.get('condition', 'N/A')}")
                    print(f"  Price: ${item.get('current_price', 0.0):.2f}")
                    print(f"  Category: {item.get('item_category', 'Unknown')}")
        
        else:
            print(f"\n❌ Error {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_basic_steam_api():
    """Test the Steam scraping API without pricing (simpler test)"""
    
    api_url = "http://localhost:5000/api/scrape/steam"
    
    # Basic test data
    test_data = {
        "steam_id": "76561198123456789",  # Replace with actual Steam ID
        "app_id": "730",  # CS2
        "include_floats": False,
        "include_prices": False,  # No pricing
        "enable_pricing": False,  # No pricing service
        "headless": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\nTesting Basic Steam Inventory Scraping API...")
    print(f"URL: {api_url}")
    print("=" * 60)
    
    try:
        response = requests.post(api_url, json=test_data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Basic scraping successful!")
            print(f"Status: {data.get('status', 'unknown')}")
            
            if 'data' in data:
                scraped_items = data['data'].get('scraped_items', [])
                print(f"Scraped Items: {len(scraped_items)}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Steam Inventory API Testing")
    print("=" * 50)
    
    # Test basic functionality first
    test_basic_steam_api()
    
    # Then test with pricing
    test_steam_api_with_pricing()

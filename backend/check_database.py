#!/usr/bin/env python3
"""
Check database contents and test pricing
"""

import requests
import json

def check_database_items():
    """Check what items are in the database"""
    
    api_url = "http://localhost:5000/api/steam/items"
    
    print("🗄️ Checking Database Contents")
    print("=" * 40)
    
    try:
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            print(f"✅ Found {len(items)} items in database")
            print()
            
            # Check pricing on first few items
            print("💰 First 5 items with pricing info:")
            print("-" * 50)
            
            for i, item in enumerate(items[:5]):
                print(f"Item {i+1}:")
                print(f"  Name: {item.get('name', 'Unknown')}")
                print(f"  Current Price: ${item.get('current_price', 0):.2f}")
                print(f"  Rarity: {item.get('rarity', 'N/A')}")
                print(f"  Last Updated: {item.get('last_updated', 'N/A')}")
                print()
            
            # Check pricing statistics
            priced_items = [item for item in items if item.get('current_price', 0) > 0]
            zero_price_items = [item for item in items if item.get('current_price', 0) == 0]
            
            print(f"📊 Pricing Statistics:")
            print(f"  Items with pricing: {len(priced_items)}")
            print(f"  Items with $0.00: {len(zero_price_items)}")
            print(f"  Total items: {len(items)}")
            
            if len(zero_price_items) > 0:
                print(f"\n❌ Items with zero pricing (first 3):")
                for item in zero_price_items[:3]:
                    print(f"  - {item.get('name', 'Unknown')}: ${item.get('current_price', 0):.2f}")
        
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def force_update_pricing():
    """Test updating pricing for existing items"""
    
    print("\n🔄 Testing Force Re-scrape with Pricing")
    print("=" * 50)
    
    # First delete all steam items to force re-scraping
    delete_url = "http://localhost:5000/api/steam/items/delete-all"  # We need to create this endpoint
    
    # For now, let's try the scrape with different steam_id format
    api_url = "http://localhost:5000/api/scrape/steam"
    
    test_data = {
        "steam_id": "https://steamcommunity.com/profiles/76561198205836117/inventory/",  # Full URL format
        "app_id": "730",
        "include_floats": False,
        "include_prices": True,
        "enable_pricing": True,
        "headless": True
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        print("📡 Sending request with full URL format...")
        response = requests.post(api_url, json=test_data, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status', 'unknown')}")
            print(f"✅ Message: {data.get('message', 'No message')}")
            
            if 'data' in data:
                scraped = data['data'].get('scraped_items', [])
                skipped = data['data'].get('skipped_items', [])
                print(f"✅ New items: {len(scraped)}")
                print(f"ℹ️ Skipped items: {len(skipped)}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database_items()
    force_update_pricing()

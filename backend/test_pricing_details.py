#!/usr/bin/env python3
"""
Test pricing updates and check actual results
"""

import requests
import json

def test_pricing_with_details():
    """Test pricing and show detailed results"""
    
    api_url = "http://localhost:5000/api/scrape/steam"
    
    test_data = {
        "steam_id": "76561198205836117",
        "app_id": "730",
        "include_floats": False,
        "include_prices": True,
        "enable_pricing": True,
        "headless": True
    }
    
    headers = {"Content-Type": "application/json"}
    
    print("🧪 Testing Pricing Updates with Details")
    print("=" * 50)
    
    try:
        response = requests.post(api_url, json=test_data, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status', 'unknown')}")
            print(f"✅ Message: {data.get('message', 'No message')}")
            
            # Get detailed response data
            response_data = data.get('data', {})
            scraped_items = response_data.get('scraped_items', [])
            skipped_items = response_data.get('skipped_items', [])
            
            print(f"\n📊 Results Summary:")
            print(f"  Scraped/Updated: {len(scraped_items)}")
            print(f"  Skipped: {len(skipped_items)}")
            
            # Show pricing details for scraped items
            if scraped_items:
                print(f"\n💰 Items with Pricing Updates:")
                print("-" * 40)
                
                for i, item in enumerate(scraped_items[:5]):  # Show first 5
                    price = item.get('current_price', 0)
                    print(f"{i+1}. {item.get('name', 'Unknown')}")
                    print(f"   Price: ${price:.2f}")
                    print(f"   Rarity: {item.get('rarity', 'N/A')}")
                    print(f"   Category: {item.get('item_category', 'N/A')}")
                    print()
                
                # Check pricing statistics
                priced_items = [item for item in scraped_items if item.get('current_price', 0) > 0]
                zero_price_items = [item for item in scraped_items if item.get('current_price', 0) == 0]
                
                print(f"📈 Pricing Statistics:")
                print(f"  Items with pricing: {len(priced_items)}")
                print(f"  Items with $0.00: {len(zero_price_items)}")
                
                if len(priced_items) > 0:
                    total_value = sum(item.get('current_price', 0) for item in priced_items)
                    print(f"  Total inventory value: ${total_value:.2f}")
                    avg_value = total_value / len(priced_items)
                    print(f"  Average item value: ${avg_value:.2f}")
                
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pricing_with_details()

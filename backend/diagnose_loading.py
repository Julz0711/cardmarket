#!/usr/bin/env python3
"""Diagnose Steam inventory loading issues."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.steam_inventory_scraper import SteamInventoryScraper
import requests

def diagnose_loading_issue():
    """Diagnose why Steam inventory is infinitely loading."""
    print("🔍 DIAGNOSING STEAM INVENTORY LOADING ISSUE")
    print("=" * 60)
    
    # Test different Steam IDs
    test_steam_ids = [
        "76561198042721508",  # The one we've been using
        "76561198019682558",  # Another test ID
        "76561198005637123",  # Another test ID
    ]
    
    scraper = SteamInventoryScraper()
    
    for steam_id in test_steam_ids:
        print(f"\n🎮 Testing Steam ID: {steam_id}")
        print("-" * 40)
        
        # Test direct Steam inventory API call
        inventory_url = f"https://steamcommunity.com/inventory/{steam_id}/730/2"
        print(f"📡 Testing: {inventory_url}")
        
        try:
            response = requests.get(inventory_url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('assets'):
                        print(f"✅ SUCCESS: Found {len(data['assets'])} items")
                        break
                    else:
                        print("❌ No assets in inventory")
                except:
                    print("❌ Invalid JSON response")
            elif response.status_code == 403:
                print("❌ PRIVATE INVENTORY")
            elif response.status_code == 401:
                print("❌ UNAUTHORIZED (Private profile)")
            elif response.status_code == 429:
                print("❌ RATE LIMITED")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("💡 LIKELY CAUSES OF INFINITE LOADING:")
    print("1. Steam inventories are private (most common)")
    print("2. Steam API is rate limiting requests")
    print("3. Steam IDs don't exist or have no CS2 items")
    print("4. Network connectivity issues")
    print("\n🚀 SOLUTIONS:")
    print("1. Use a public Steam inventory")
    print("2. Use alternative free pricing APIs")
    print("3. Use enhanced mock data (already implemented)")

if __name__ == "__main__":
    diagnose_loading_issue()

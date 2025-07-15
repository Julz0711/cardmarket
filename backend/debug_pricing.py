#!/usr/bin/env python3
"""
Debug pricing issues in Steam scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.steam_inventory_scraper import SteamInventoryScraper, SteamMarketPricer

def debug_pricing():
    """Debug pricing functionality step by step"""
    
    print("🔍 Debugging Steam Pricing Issues")
    print("=" * 50)
    
    # Test 1: Pricing service alone
    print("1️⃣ Testing SteamMarketPricer directly...")
    pricer = SteamMarketPricer()
    
    test_items = [
        'Operation Hydra Case',
        'Chroma Case',
        'AK-47 | Redline (Field-Tested)'
    ]
    
    for item in test_items:
        print(f"  Testing: {item}")
        # Force mock pricing to test basic functionality
        result = pricer.get_item_price(item, use_mock=True)
        print(f"  Mock Result: {result}")
        print()
    
    # Test 2: Scraper initialization
    print("2️⃣ Testing SteamInventoryScraper initialization...")
    scraper = SteamInventoryScraper(headless=True, enable_pricing=True)
    print(f"  Scraper.enable_pricing: {scraper.enable_pricing}")
    print(f"  Scraper.pricer: {scraper.pricer}")
    print(f"  Pricer type: {type(scraper.pricer)}")
    print()
    
    # Test 3: Mock a single item processing
    print("3️⃣ Testing single item processing with pricing...")
    
    # Mock CS2 item data
    mock_item_data = {
        'market_hash_name': 'Operation Hydra Case',
        'type': 'Base Grade Container',
        'amount': '1',
        'assetid': '123456789',
        'icon_url': 'test_icon',
        'tags': [
            {'category': 'Type', 'internal_name': 'CSGO_Type_WeaponCase'},
            {'category': 'Quality', 'internal_name': 'normal'},
        ]
    }
    
    try:
        processed_item = scraper._process_cs2_item(
            mock_item_data, 
            steam_id="test", 
            include_floats=False, 
            include_prices=True  # This should enable pricing
        )
        
        print(f"  Processed item: {processed_item}")
        print(f"  Item name: {processed_item.get('name', 'N/A')}")
        print(f"  Current price: {processed_item.get('current_price', 'N/A')}")
        
    except Exception as e:
        print(f"  ❌ Error processing item: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🔧 Cleanup...")
    scraper._cleanup()

if __name__ == "__main__":
    debug_pricing()

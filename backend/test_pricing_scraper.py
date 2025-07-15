#!/usr/bin/env python3
"""
Test Steam Inventory Scraper with Pricing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.steam_inventory_scraper import SteamInventoryScraper

def test_steam_scraper_with_pricing():
    """Test the enhanced Steam scraper with pricing"""
    
    print("Testing Steam Inventory Scraper with Pricing...")
    print("=" * 60)
    
    # Initialize scraper with pricing enabled
    scraper = SteamInventoryScraper(headless=True, enable_pricing=True)
    
    # Test with a known Steam ID (you can replace this with your own)
    test_steam_id = "76561198123456789"  # Replace with actual Steam ID
    
    try:
        # Scrape inventory with pricing
        items = scraper.scrape(
            steam_id=test_steam_id,
            app_id="730",  # CS2
            include_floats=False,  # Keep it simple
            include_prices=True    # Enable pricing
        )
        
        print(f"Found {len(items)} CS2 items")
        print("-" * 40)
        
        # Display first few items with pricing
        for i, item in enumerate(items[:5]):  # Show first 5 items
            print(f"Item {i+1}:")
            print(f"  Name: {item.get('name', 'Unknown')}")
            print(f"  Rarity: {item.get('rarity', 'Unknown')}")
            print(f"  Condition: {item.get('condition', 'N/A')}")
            print(f"  Category: {item.get('item_category', 'Unknown')}")
            print(f"  Price: ${item.get('current_price', 0.0):.2f}")
            print(f"  Quantity: {item.get('quantity', 1)}")
            print("-" * 30)
        
        if len(items) > 5:
            print(f"... and {len(items) - 5} more items")
            
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()

def test_pricing_service():
    """Test just the pricing service"""
    
    print("\nTesting Pricing Service Separately...")
    print("=" * 40)
    
    from scrapers.steam_inventory_scraper import SteamMarketPricer
    
    pricer = SteamMarketPricer()
    
    test_items = [
        'Operation Hydra Case',
        'Chroma Case',
        'AK-47 | Redline (Field-Tested)'
    ]
    
    for item in test_items:
        print(f"Testing: {item}")
        # Use mock data for testing
        price_info = pricer.get_item_price(item, use_mock=True)
        print(f"  Result: {price_info}")
        print()

if __name__ == "__main__":
    # Test pricing service first
    test_pricing_service()
    
    # Uncomment to test full scraper (requires valid Steam ID)
    # test_steam_scraper_with_pricing()

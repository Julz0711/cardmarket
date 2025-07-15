#!/usr/bin/env python3
"""Test script to verify Steam inventory pricing integration."""

from scrapers.steam_inventory_scraper import SteamInventoryScraper

def test_inventory_with_pricing():
    """Test the Steam inventory scraper with pricing enabled."""
    print("🎮 Testing Steam Inventory with Pricing")
    print("=" * 50)
    
    scraper = SteamInventoryScraper()
    
    # Test with a Steam ID that has items
    steam_id = "76561198042721508"
    
    try:
        # Get inventory with pricing
        result = scraper.scrape(steam_id=steam_id, include_prices=True)
        
        print(f"✅ Items found: {len(result)}")
        print()
        
        if result:
            print("Sample pricing results:")
            print("-" * 30)
            
            for i, item in enumerate(result[:10]):  # Show first 10 items
                price = item.get('current_price', 0)
                name = item.get('name', 'Unknown Item')
                print(f"{i+1:2d}. {name[:50]:<50} ${price:.2f}")
            
            # Show statistics
            prices = [item.get('current_price', 0) for item in result if item.get('current_price', 0) > 0]
            if prices:
                print()
                print("Pricing Statistics:")
                print(f"  Items with prices: {len(prices)}/{len(result)}")
                print(f"  Average price: ${sum(prices)/len(prices):.2f}")
                print(f"  Total value: ${sum(prices):.2f}")
                print(f"  Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            
        else:
            print("❌ No items found in inventory")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_inventory_with_pricing()

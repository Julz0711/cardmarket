#!/usr/bin/env python3
"""Test script to compare mock pricing vs real Steam API pricing."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.steam_inventory_scraper import SteamMarketPricer

def test_real_vs_mock_pricing():
    """Compare mock pricing vs real Steam API pricing."""
    print("🔄 Testing Real Steam API vs Mock Pricing")
    print("=" * 60)
    
    pricer = SteamMarketPricer()
    
    # Test a few items with both systems
    test_items = [
        "AK-47 | Redline (Field-Tested)",
        "Operation Hydra Case",
        "CS:GO Case Key",
        "AWP | Dragon Lore (Field-Tested)",
    ]
    
    for item_name in test_items:
        print(f"\n🔍 Testing: {item_name}")
        print("-" * 40)
        
        # Test with mock pricing (current default)
        mock_result = pricer.get_item_price(item_name, use_mock=True)
        if mock_result:
            mock_price = mock_result.get('lowest_price', 'N/A')
            mock_source = mock_result.get('source', 'unknown')
            print(f"Mock Pricing:  {mock_price} (source: {mock_source})")
        else:
            print("Mock Pricing:  Failed")
        
        # Test with real Steam API (if you want real prices)
        print("Fetching real Steam API price... (this may take a few seconds)")
        real_result = pricer.get_item_price(item_name, use_mock=False)
        if real_result:
            real_price = real_result.get('lowest_price', 'N/A')
            real_source = real_result.get('source', 'unknown')
            print(f"Real API:      {real_price} (source: {real_source})")
        else:
            print("Real API:      Failed (rate limited or not available)")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("• Mock pricing: Fast, reliable, realistic values")
    print("• Real API: Current market prices, but slow and rate-limited")
    print("\nTo enable real pricing in your app:")
    print("• Change 'use_mock=True' to 'use_mock=False' in the scraper")

if __name__ == "__main__":
    test_real_vs_mock_pricing()

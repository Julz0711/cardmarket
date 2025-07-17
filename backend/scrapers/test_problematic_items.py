#!/usr/bin/env python3
"""
Test the complete scraper flow with problematic items like Global Offensive Badge
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from skinsnipe_scraper import SkinSnipeScraper
import time

def test_problematic_items():
    """Test the scraper with items that were causing issues"""
    
    # Test items that should be skipped immediately
    test_items = [
        {"name": "Global Offensive Badge (N/A)", "condition": None},
        {"name": "Service Medal", "condition": None},
        {"name": "AK-47", "condition": None},  # Stock weapon
        {"name": "AK-47 | Redline", "condition": "Minimal Wear"},  # Should work
    ]
    
    print("🧪 Testing Complete Scraper Flow with Problematic Items")
    print("=" * 60)
    
    with SkinSnipeScraper(headless=True) as scraper:
        start_time = time.time()
        
        for i, item_data in enumerate(test_items):
            item_name = item_data['name']
            condition = item_data['condition']
            
            print(f"\n📋 Test {i+1}/4: {item_name}")
            print("-" * 40)
            
            item_start = time.time()
            result = scraper.search_item(item_name, condition)
            item_end = time.time()
            
            if result:
                if result.get('skipped', False):
                    print(f"⏭️  SKIPPED: {result.get('error', 'Unknown reason')}")
                    print(f"⏱️  Time: {item_end - item_start:.2f}s (instant skip)")
                else:
                    print(f"✅ FOUND: ${result['price']} ({result.get('currency', 'USD')})")
                    print(f"⏱️  Time: {item_end - item_start:.2f}s")
            else:
                print(f"❌ FAILED: No result returned")
                print(f"⏱️  Time: {item_end - item_start:.2f}s")
        
        total_time = time.time() - start_time
        print(f"\n📊 Total Test Results:")
        print(f"  • Total time: {total_time:.2f}s")
        print(f"  • Items tested: {len(test_items)}")
        print(f"  • Expected: Global Offensive Badge should be skipped instantly")

if __name__ == "__main__":
    test_problematic_items()

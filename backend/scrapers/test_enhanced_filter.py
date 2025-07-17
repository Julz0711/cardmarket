#!/usr/bin/env python3
"""
Test script to verify enhanced non-tradeable item filtering
Specifically tests the Global Offensive Badge issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from skinsnipe_scraper import SkinSnipeScraper

def test_enhanced_filtering():
    """Test the enhanced filtering with problematic items"""
    
    scraper = SkinSnipeScraper(headless=True)
    
    # Test items that should be filtered out
    non_tradeable_items = [
        "Global Offensive Badge (N/A)",
        "Service Medal",
        "5 Year Veteran Coin",
        "Operation Hydra Coin",
        "Loyalty Badge",
        "Rank Badge",
        "Commemorative Item (N/A)",
        "AK-47",  # Stock weapon
        "M4A4",  # Stock weapon
    ]
    
    # Test items that should be tradeable
    tradeable_items = [
        "AK-47 | Redline",
        "AWP | Dragon Lore", 
        "Spectrum Case",
        "StatTrak™ AK-47 | Redline",
        "Sticker | Hello"
    ]
    
    print("🧪 Testing Enhanced Non-Tradeable Item Filtering")
    print("=" * 60)
    
    print("\n📋 Testing Non-Tradeable Items (should be SKIPPED):")
    all_correct = True
    
    for item in non_tradeable_items:
        is_tradeable = scraper.is_tradeable_item(item)
        status = "❌ PASS (Skipped)" if not is_tradeable else "⚠️  FAIL (Not Skipped)"
        print(f"  {status} - {item}")
        if is_tradeable:
            all_correct = False
    
    print(f"\n📋 Testing Tradeable Items (should be PROCESSED):")
    
    for item in tradeable_items:
        is_tradeable = scraper.is_tradeable_item(item)
        status = "✅ PASS (Processed)" if is_tradeable else "⚠️  FAIL (Skipped)"
        print(f"  {status} - {item}")
        if not is_tradeable:
            all_correct = False
    
    print(f"\n📊 Enhanced Filtering Test Results:")
    print(f"  • Non-tradeable items: {len(non_tradeable_items)} tested")
    print(f"  • Tradeable items: {len(tradeable_items)} tested")
    print(f"  • Overall result: {'✅ ALL CORRECT' if all_correct else '⚠️  SOME ISSUES FOUND'}")
    
    if all_correct:
        print(f"\n🎉 Enhanced filtering is working perfectly!")
        print(f"   Global Offensive Badge and similar items will be skipped.")
    else:
        print(f"\n⚠️  Some items are not being classified correctly.")
        print(f"   Review the patterns in non_tradeable_patterns list.")
    
    return all_correct

if __name__ == "__main__":
    test_enhanced_filtering()

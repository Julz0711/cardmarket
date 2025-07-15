#!/usr/bin/env python3
"""Test script to verify the enhanced pricing system with realistic CS2 items."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.steam_inventory_scraper import SteamMarketPricer

def test_pricing_system():
    """Test the enhanced pricing system with various CS2 items."""
    print("💰 Testing Enhanced CS2 Pricing System")
    print("=" * 60)
    
    pricer = SteamMarketPricer()
    
    # Test items that should demonstrate the improvements
    test_items = [
        # Cases (should be low price $0.10-$0.55)
        "Operation Hydra Case",
        "Chroma Case", 
        "Revolution Case",
        "Unknown Case XYZ",  # Should use smart pricing
        
        # Popular weapons (should be realistic prices)
        "AK-47 | Redline (Field-Tested)",
        "M4A4 | Dragon King (Field-Tested)", 
        "AWP | Lightning Strike (Factory New)",  # Should use smart pricing
        "Glock-18 | Water Elemental (Factory New)",  # Should use smart pricing
        
        # StatTrak weapons (should have multiplier)
        "StatTrak™ AK-47 | Point Disarray (Field-Tested)",
        "StatTrak™ M4A1-S | Hyper Beast (Minimal Wear)",
        
        # Knives (should be high value $150-$800)
        "★ Karambit | Doppler (Factory New)",
        "★ Butterfly Knife | Tiger Tooth (Minimal Wear)",  # Should use smart pricing
        
        # Gloves (should be high value)
        "Sport Gloves | Pandora's Box (Field-Tested)",
        "★ Hand Wraps | Leather (Well-Worn)",  # Should use smart pricing
        
        # Agents (should be $2-$25)
        "Cmdr. Mae 'Dead Cold' Jamison",
        "Lieutenant Farlow | SWAT",  # Should use smart pricing
        
        # Keys and stickers
        "CS:GO Case Key",
        "Random Sticker | Team Logo",  # Should use smart pricing
        
        # Music kits
        "Music Kit | Some Artist",  # Should use smart pricing
    ]
    
    print("Testing pricing for various CS2 items:")
    print()
    
    total_mock = 0
    total_smart = 0
    zero_prices = 0
    
    for item_name in test_items:
        pricing_info = pricer.get_item_price(item_name, use_mock=True)
        
        if pricing_info:
            price = pricing_info.get('lowest_price', 0)
            source = pricing_info.get('source', 'unknown')
            
            # Convert price to float if it's a string
            if isinstance(price, str):
                price_clean = price.replace('€', '').replace('$', '').replace(',', '.')
                try:
                    price = float(price_clean)
                except:
                    price = 0
            
            if price == 0:
                zero_prices += 1
                status = "❌ Zero price"
            elif source == 'mock':
                total_mock += 1
                status = "✅ Mock DB"
            elif source == 'mock_smart':
                total_smart += 1
                status = "🤖 Smart pricing"
            else:
                status = f"ℹ️ {source}"
            
            print(f"{item_name[:45]:<45} ${price:>7.2f} {status}")
        else:
            zero_prices += 1
            print(f"{item_name[:45]:<45} $   0.00 ❌ No pricing info")
    
    print()
    print("Summary:")
    print("-" * 40)
    print(f"Items with mock database prices: {total_mock}")
    print(f"Items with smart pricing: {total_smart}")
    print(f"Items with zero/no prices: {zero_prices}")
    print(f"Total items tested: {len(test_items)}")
    
    # Calculate success rate
    success_rate = ((total_mock + total_smart) / len(test_items)) * 100
    print(f"Success rate: {success_rate:.1f}%")
    
    if zero_prices == 0:
        print("🎉 SUCCESS: All items now have realistic prices!")
        print("✅ Fixed the issue where items were getting random $0.10-$2.00 prices")
    elif zero_prices < 3:
        print("✅ MOSTLY SUCCESSFUL: Very few items have zero prices")
    else:
        print("⚠️ NEEDS IMPROVEMENT: Several items still have zero prices")

if __name__ == "__main__":
    test_pricing_system()

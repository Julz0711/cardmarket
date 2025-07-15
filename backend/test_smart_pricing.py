#!/usr/bin/env python3
"""
Test the new smart pricing system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.steam_inventory_scraper import SteamMarketPricer

def test_smart_pricing():
    """Test the smart pricing system with various item types"""
    
    pricer = SteamMarketPricer()
    
    # Test items from different categories
    test_items = [
        # Cases
        'Operation Hydra Case',
        'Chroma Case',
        'Revolution Case',
        'Random Case XYZ',  # Not in database
        
        # Weapons
        'AK-47 | Redline (Field-Tested)',
        'M4A4 | Dragon King (Field-Tested)',  # Not in database
        'AWP | Neo-Noir (Minimal Wear)',  # Not in database
        'Glock-18 | Water Elemental (Factory New)',  # Not in database
        
        # StatTrak weapons
        'StatTrak™ AK-47 | Point Disarray (Field-Tested)',  # Not in database
        'StatTrak™ M4A1-S | Hyper Beast (Minimal Wear)',  # Not in database
        
        # Special items
        '★ Karambit | Doppler (Factory New)',  # Not in database
        'Sport Gloves | Pandora\'s Box (Field-Tested)',  # Not in database
        
        # Agents
        'Cmdr. Mae \'Dead Cold\' Jamison',
        'Lieutenant Farlow | SWAT',  # Not in database
        
        # Other items
        'CS:GO Case Key',
        'Random Sticker | Team Logo',  # Not in database
        'Music Kit | Some Artist',  # Not in database
    ]
    
    print("🧪 Testing Smart Pricing System")
    print("=" * 60)
    
    for item in test_items:
        print(f"\nTesting: {item}")
        
        # Test with mock pricing
        result = pricer.get_item_price(item, use_mock=True)
        
        if result and result.get('success'):
            price = result.get('lowest_price', 'N/A')
            source = result.get('source', 'unknown')
            print(f"  Price: {price}")
            print(f"  Source: {source}")
            
            # Show if it's from database or smart generation
            if source == 'mock':
                print(f"  ✅ Found in mock database")
            elif source == 'mock_smart':
                print(f"  🤖 Generated using smart pricing")
            else:
                print(f"  ❓ Unknown source")
        else:
            print(f"  ❌ No price found")
        
        print("-" * 40)

if __name__ == "__main__":
    test_smart_pricing()

#!/usr/bin/env python3
"""Test script to demonstrate real Steam API pricing with rate limiting."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.steam_inventory_scraper import SteamMarketPricer
import time

def test_real_steam_api_pricing():
    """Test the real Steam API pricing with actual market data."""
    print("🔥 Testing Real Steam API Pricing")
    print("=" * 60)
    print("⚠️ This will make real API calls to Steam with 5-second delays")
    print("⚠️ Each item will take ~5-10 seconds to fetch")
    print()
    
    pricer = SteamMarketPricer()
    
    # Test items that should have real market data
    test_items = [
        "AK-47 | Redline (Field-Tested)",
        "Operation Hydra Case", 
        "CS:GO Case Key",
        "M4A4 | Dragon King (Field-Tested)",
        "AWP | Dragon Lore (Field-Tested)",
    ]
    
    print(f"Testing {len(test_items)} items with real Steam API...")
    print()
    
    results = []
    total_start_time = time.time()
    
    for i, item_name in enumerate(test_items, 1):
        print(f"[{i}/{len(test_items)}] Testing: {item_name}")
        print("-" * 50)
        
        start_time = time.time()
        
        # Test with real Steam API
        real_result = pricer.get_item_price(item_name, use_mock=False)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if real_result and real_result.get('success'):
            price = real_result.get('lowest_price', 'N/A')
            volume = real_result.get('volume', 'N/A')
            source = real_result.get('source', 'unknown')
            
            print(f"✅ Success!")
            print(f"   Price: {price}")
            print(f"   Volume: {volume}")
            print(f"   Source: {source}")
            print(f"   Duration: {duration:.1f}s")
            
            results.append({
                'item': item_name,
                'price': price,
                'volume': volume,
                'source': source,
                'success': True,
                'duration': duration
            })
        else:
            print(f"❌ Failed to get real price")
            print(f"   Duration: {duration:.1f}s")
            print(f"   Trying mock fallback...")
            
            # Try mock fallback
            mock_result = pricer.get_item_price(item_name, use_mock=True)
            if mock_result:
                mock_price = mock_result.get('lowest_price', 'N/A')
                print(f"   Mock price: {mock_price}")
                
                results.append({
                    'item': item_name,
                    'price': mock_price,
                    'volume': 'Mock',
                    'source': 'mock_fallback',
                    'success': False,
                    'duration': duration
                })
            else:
                results.append({
                    'item': item_name,
                    'price': 'N/A',
                    'volume': 'N/A',
                    'source': 'failed',
                    'success': False,
                    'duration': duration
                })
        
        print()
    
    total_duration = time.time() - total_start_time
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    successful_real = sum(1 for r in results if r['success'] and r['source'] == 'steam_api')
    failed_real = len(results) - successful_real
    
    print(f"Total items tested: {len(results)}")
    print(f"Real Steam API success: {successful_real}")
    print(f"Failed/fallback: {failed_real}")
    print(f"Total time: {total_duration:.1f}s")
    print(f"Average time per item: {total_duration/len(results):.1f}s")
    print()
    
    print("Results:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['item'][:35]:<35} {r['price']:<12} ({r['source']})")
    
    print()
    if successful_real > 0:
        print("🎉 SUCCESS! Real Steam API pricing is working!")
        print("✅ You're now getting live market prices from Steam")
        print("⚠️ Remember: Rate limited to prevent blocking (5+ seconds per item)")
    else:
        print("⚠️ No real Steam API prices were fetched")
        print("💡 This could be due to rate limiting, network issues, or item availability")
        print("🔄 Fallback system is working with mock prices")

if __name__ == "__main__":
    test_real_steam_api_pricing()

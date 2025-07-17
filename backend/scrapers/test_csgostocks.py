#!/usr/bin/env python3
"""
Test script for CSGOStocks.de scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from csgostocks_scraper import CSGOStocksScraper
import time

def test_csgostocks_scraper():
    print("CSGOStocks Scraper Test Suite")
    print("=" * 50)
    
    # Test items as specified by user
    test_items = [
        {
            'name': 'Lt. Commander Ricksaw | NSWC SEAL',
            'condition': None,
            'description': 'Agent skin'
        },
        {
            'name': 'StatTrak AK-47 | Redline',
            'condition': 'Minimal Wear',
            'description': 'StatTrak weapon with condition'
        },
        {
            'name': 'AK-47 | Redline',
            'condition': 'Battle Scarred',
            'description': 'Regular weapon with condition'
        },
        {
            'name': 'Spectrum Case',
            'condition': None,
            'description': 'Case item'
        }
    ]
    
    print("=" * 50)
    print("TESTING SINGLE ITEM SEARCH")
    print("=" * 50)
    
    with CSGOStocksScraper(headless=False) as scraper:
        for i, item in enumerate(test_items, 1):
            print(f"\n--- Test {i}: {item['description']} ---")
            print(f"Testing search for: {item['name']}")
            if item['condition']:
                print(f"Condition: {item['condition']}")
            
            try:
                result = scraper.search_item(item['name'], item['condition'])
                
                if result:
                    print(f"✅ SUCCESS: Found price €{result['price']}")
                    print(f"   Source: {result['source']}")
                    print(f"   Found name: {result['found_name']}")
                    print(f"   Condition: {result['condition']}")
                    print(f"   Currency: {result['currency']}")
                else:
                    print(f"❌ FAILED: No price found")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
            
            # Small delay between searches
            if i < len(test_items):
                print("Waiting 2 seconds before next search...")
                time.sleep(2)
    
    print("\n" + "=" * 50)
    print("TESTING BATCH PROCESSING")
    print("=" * 50)
    
    # Test batch processing
    batch_items = [
        {'name': 'AK-47 | Redline', 'condition': 'Field-Tested'},
        {'name': 'AWP | Dragon Lore', 'condition': 'Factory New'}
    ]
    
    scraper = CSGOStocksScraper(headless=False)
    try:
        batch_results = scraper.scrape_item_prices(batch_items)
        
        print(f"Batch processed {len(batch_results)} items:")
        for result in batch_results:
            if result.get('error'):
                print(f"❌ {result['item_name']}: {result['error']}")
            else:
                print(f"✅ {result['item_name']}: €{result['price']}")
                
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
    finally:
        scraper.cleanup()
    
    print("\nTesting complete!")

if __name__ == "__main__":
    test_csgostocks_scraper()

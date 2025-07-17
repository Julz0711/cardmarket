#!/usr/bin/env python3
"""
Test script for PriceEmpire.com scraper
"""

import time
from priceempire_scraper import PriceEmpireScraper

def test_single_item():
    """Test single item search"""
    print("=" * 50)
    print("TESTING SINGLE ITEM SEARCH")
    print("=" * 50)
    
    with PriceEmpireScraper(headless=False) as scraper:
        test_item = "AK-47 | Redline"
        print(f"Testing search for: {test_item}")
        
        result = scraper.search_item(test_item)
        
        if result:
            print(f"✅ Success! Found price: ${result['price']}")
            print(f"Found name: {result['found_name']}")
            print(f"Condition: {result.get('condition', 'Unknown')}")
            print(f"Source: {result['source']}")
            return True
        else:
            print("❌ Failed to find price")
            return False

def test_condition_specific():
    """Test condition-specific search"""
    print("\n" + "=" * 50)
    print("TESTING CONDITION-SPECIFIC SEARCH")
    print("=" * 50)
    
    with PriceEmpireScraper(headless=False) as scraper:
        test_item = "AK-47 | Redline"
        condition = "FT"
        print(f"Testing search for: {test_item} ({condition})")
        
        result = scraper.search_item(test_item, condition)
        
        if result:
            print(f"✅ Success! Found price: ${result['price']}")
            print(f"Found name: {result['found_name']}")
            print(f"Condition: {result.get('condition', 'Unknown')}")
            print(f"Source: {result['source']}")
            return True
        else:
            print("❌ Failed to find price")
            return False

def test_multiple_items():
    """Test multiple item search"""
    print("\n" + "=" * 50)
    print("TESTING MULTIPLE ITEMS")
    print("=" * 50)
    
    test_items = [
        {"name": "AK-47 | Redline", "condition": "FT"},
        {"name": "AWP | Dragon Lore", "condition": "FN"},
        {"name": "M4A4 | Howl", "condition": "MW"}
    ]
    
    scraper = PriceEmpireScraper(headless=False)
    results = scraper.scrape_item_prices(test_items)
    
    print(f"Processed {len(results)} items:")
    for i, result in enumerate(results, 1):
        if result.get('price', 0) > 0:
            print(f"{i}. ✅ {result['item_name']}: ${result['price']}")
        else:
            print(f"{i}. ❌ {result['item_name']}: Failed ({result.get('error', 'Unknown error')})")
    
    return len([r for r in results if r.get('price', 0) > 0]) > 0

def test_interactive():
    """Interactive testing"""
    print("\n" + "=" * 50)
    print("INTERACTIVE TESTING")
    print("=" * 50)
    
    with PriceEmpireScraper(headless=False) as scraper:
        while True:
            try:
                item_name = input("\nEnter item name (or 'quit' to exit): ").strip()
                if item_name.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not item_name:
                    continue
                
                condition = input("Enter condition (FN/MW/FT/WW/BS or press Enter for any): ").strip().upper()
                if not condition:
                    condition = None
                
                print(f"\nSearching for: {item_name}" + (f" ({condition})" if condition else ""))
                
                start_time = time.time()
                result = scraper.search_item(item_name, condition)
                end_time = time.time()
                
                if result:
                    print(f"✅ Found in {end_time - start_time:.2f}s:")
                    print(f"   Price: ${result['price']}")
                    print(f"   Name: {result['found_name']}")
                    print(f"   Condition: {result.get('condition', 'Unknown')}")
                else:
                    print(f"❌ Not found ({end_time - start_time:.2f}s)")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("PriceEmpire Scraper Test Suite")
    print("=" * 50)
    
    try:
        # Test single item
        success1 = test_single_item()
        
        if success1:
            # Test condition-specific if first test passed
            success2 = test_condition_specific()
            
            if success2:
                # Test multiple items if condition test passed
                success3 = test_multiple_items()
                
                if success3:
                    # Interactive testing
                    test_interactive()
        
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
    
    print("\nTesting complete!")

#!/usr/bin/env python3
"""
Test script for steammarket library
"""

import steammarket
import traceback

def test_steammarket():
    """Test steammarket functionality"""
    
    print("Testing steammarket library...")
    print(f"Available methods: {[method for method in dir(steammarket) if not method.startswith('_')]}")
    
    # Test 1: get_csgo_item
    try:
        print("\n=== Test 1: get_csgo_item ===")
        result = steammarket.get_csgo_item('Operation Hydra Case')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error in get_csgo_item: {e}")
        traceback.print_exc()
    
    # Test 2: get_item with CS2 app ID
    try:
        print("\n=== Test 2: get_item with CS2 ===")
        result = steammarket.get_item(730, 'Operation Hydra Case')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error in get_item: {e}")
        traceback.print_exc()
    
    # Test 3: get_item with currency
    try:
        print("\n=== Test 3: get_item with USD ===")
        result = steammarket.get_item(730, 'Operation Hydra Case', 'USD')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error in get_item with USD: {e}")
        traceback.print_exc()
    
    # Test 4: Test with a simple case
    try:
        print("\n=== Test 4: Simple case test ===")
        result = steammarket.get_csgo_item('Chroma Case')
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error with Chroma Case: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_steammarket()

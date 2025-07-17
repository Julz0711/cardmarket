#!/usr/bin/env python3
"""
Test script for CSGOSkins scraper with enhanced visibility and pattern delays
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scrapers.csgoskins_scraper import CSGOSkinsGGScraper
import time

def test_visibility_and_patterns():
    """Test scraper with visible browser and pattern-based delays"""
    print("🧪 Testing CSGOSkins scraper with visible browser and pattern delays...")
    
    # Initialize scraper with visible browser
    scraper = CSGOSkinsGGScraper(headless=False)
    
    try:
        # Test items that should trigger the "5th item" pattern
        test_items = [
            "AK-47 | Redline",           # 1st item
            "AWP | Dragon Lore",         # 2nd item  
            "M4A4 | Howl",              # 3rd item (medium delay)
            "Karambit | Fade",          # 4th item
            "AK-47 | Fire Serpent",     # 5th item (long delay)
            "AWP | Medusa",             # 6th item (medium delay)
            "M4A1-S | Knight",          # 7th item
            "Glock-18 | Fade",          # 8th item
            "Desert Eagle | Blaze",     # 9th item (medium delay)
            "AK-47 | Case Hardened"     # 10th item (long delay)
        ]
        
        print(f"\n🎯 Testing {len(test_items)} items to observe pattern delays...")
        print("📊 Expected pattern:")
        print("   - Items 1,2,4,7,8: Normal human-like delays (0.5-3s)")
        print("   - Items 3,6,9: Medium delays (3-5s)")  
        print("   - Items 5,10: Long delays (5-10s)")
        print("\n" + "="*60 + "\n")
        
        results = []
        for i, item in enumerate(test_items, 1):
            print(f"\n🔍 Item {i}: {item}")
            start_time = time.time()
            
            try:
                result = scraper.search_item(item)
                end_time = time.time()
                
                processing_time = end_time - start_time
                results.append({
                    'item': item,
                    'time': processing_time,
                    'success': result is not None,
                    'request_number': i
                })
                
                if result:
                    print(f"✅ Success in {processing_time:.2f}s - Price data found")
                    if 'factory_new' in result:
                        print(f"   💰 Factory New: €{result['factory_new']}")
                else:
                    print(f"❌ Failed in {processing_time:.2f}s - No data found")
                
            except Exception as e:
                end_time = time.time()
                processing_time = end_time - start_time
                print(f"💥 Error in {processing_time:.2f}s: {e}")
                results.append({
                    'item': item,
                    'time': processing_time,
                    'success': False,
                    'error': str(e),
                    'request_number': i
                })
        
        # Summary
        print("\n" + "="*60)
        print("📈 PERFORMANCE SUMMARY")
        print("="*60)
        
        total_time = sum(r['time'] for r in results)
        successful = sum(1 for r in results if r['success'])
        
        print(f"📊 Total items processed: {len(results)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {len(results) - successful}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"📈 Average per item: {total_time/len(results):.2f}s")
        
        print("\n🕐 Pattern Analysis:")
        for result in results:
            req_num = result['request_number']
            time_taken = result['time']
            status = "✅" if result['success'] else "❌"
            
            # Determine expected delay category
            if req_num % 5 == 0:
                category = "LONG (5-10s)"
            elif req_num % 3 == 0:
                category = "MEDIUM (3-5s)"
            else:
                category = "Normal (0.5-3s)"
                
            print(f"   Item {req_num:2d}: {time_taken:5.2f}s {status} - Expected: {category}")
        
        print(f"\n🏆 Browser visibility test: {'PASS' if not scraper.headless else 'FAIL'}")
        print(f"🔢 Request counter working: {'PASS' if scraper.request_count == len(test_items) else 'FAIL'}")
        
        return results
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        return None
    finally:
        scraper.close()
        print("\n🧹 Scraper closed")

if __name__ == "__main__":
    print("Starting comprehensive visibility and pattern delay test...")
    results = test_visibility_and_patterns()
    
    if results:
        print("\n🎉 Test completed! Check the timing patterns above.")
        print("👀 You should have seen a browser window during the test.")
        print("⚡ Pattern delays should prevent rate limiting after the 5th item.")
    else:
        print("\n💥 Test failed completely")

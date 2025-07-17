#!/usr/bin/env python3
"""
Ultra-aggressive performance test for the CSGOSkins scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scrapers.csgoskins_scraper import CSGOSkinsGGScraper
import time

def test_ultra_aggressive():
    """Test scraper with ultra-aggressive timeouts"""
    print("⚡ Testing ULTRA-AGGRESSIVE CSGOSkins scraper...")
    
    # Initialize scraper
    scraper = CSGOSkinsGGScraper(headless=True)  # Use headless for speed
    
    try:
        # Test with simple items that should be fast
        test_items = [
            "AK-47 | Vulcan",
            "AWP | Hyper Beast", 
            "M4A1-S | Cyrex"
        ]
        
        print(f"\n⚡ Testing {len(test_items)} items with ULTRA-AGGRESSIVE settings...")
        print("🔧 Ultra-aggressive changes:")
        print("   - Search timeout: 5s → 3s")
        print("   - Page load timeout: 3s → 2s") 
        print("   - Agent timeout: 3s → 2s")
        print("   - Page load threshold: 2s → 1.5s")
        print("   - Headless mode for maximum speed")
        print("\n" + "="*50 + "\n")
        
        total_start_time = time.time()
        results = []
        
        for i, item in enumerate(test_items, 1):
            print(f"\n⚡ Item {i}/{len(test_items)}: {item}")
            start_time = time.time()
            
            try:
                result = scraper.search_item(item)
                end_time = time.time()
                
                processing_time = end_time - start_time
                results.append({
                    'item': item,
                    'time': processing_time,
                    'success': result is not None
                })
                
                if result:
                    print(f"✅ Success in {processing_time:.2f}s")
                    if 'prices' in result and 'FN' in result['prices']:
                        print(f"   💰 Factory New: ${result['prices']['FN']}")
                else:
                    print(f"❌ Failed in {processing_time:.2f}s")
                
                # Performance feedback
                if processing_time < 3:
                    print(f"   🚀 EXCELLENT! (under 3s)")
                elif processing_time < 8:
                    print(f"   ⚡ GOOD (under 8s)")
                else:
                    print(f"   🐌 Still needs work (over 8s)")
                
            except Exception as e:
                end_time = time.time()
                processing_time = end_time - start_time
                print(f"💥 Error in {processing_time:.2f}s: {e}")
                results.append({
                    'item': item,
                    'time': processing_time,
                    'success': False,
                    'error': str(e)
                })
        
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        # Summary
        print("\n" + "="*50)
        print("⚡ ULTRA-AGGRESSIVE RESULTS")
        print("="*50)
        
        successful = sum(1 for r in results if r['success'])
        avg_time = sum(r['time'] for r in results) / len(results)
        
        print(f"📊 Items tested: {len(results)}")
        print(f"✅ Successful: {successful}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"📈 Average per item: {avg_time:.2f}s")
        
        # Speed categories
        excellent = sum(1 for r in results if r['time'] < 3)
        good = sum(1 for r in results if 3 <= r['time'] < 8)
        slow = sum(1 for r in results if r['time'] >= 8)
        
        print(f"\n🚀 EXCELLENT (< 3s): {excellent}")
        print(f"⚡ GOOD (3-8s): {good}")  
        print(f"🐌 SLOW (≥ 8s): {slow}")
        
        if avg_time < 5:
            print(f"\n🎉 SUCCESS! Average time now {avg_time:.2f}s - much better!")
        elif avg_time < 15:
            print(f"\n👍 PROGRESS! Average time {avg_time:.2f}s - getting better")
        else:
            print(f"\n⚠️  Still slow at {avg_time:.2f}s average")
        
        # Diagnosis
        print(f"\n🔍 DIAGNOSIS:")
        if slow > 0:
            print(f"   - {slow} items still slow - may be server-side delays")
        if excellent >= 2:
            print(f"   - {excellent} items are now excellent - optimizations working!")
        print(f"   - Try running test again to see if results are consistent")
        
        return results
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        return None
    finally:
        scraper.cleanup()
        print("\n🧹 Cleanup complete")

if __name__ == "__main__":
    print("Starting ultra-aggressive performance test...")
    results = test_ultra_aggressive()
    
    if results:
        print("\n⚡ Ultra-aggressive test completed!")
        avg_time = sum(r['time'] for r in results) / len(results)
        if avg_time < 10:
            print(f"🎯 Target achieved! Average time: {avg_time:.2f}s")
        else:
            print(f"🔧 More optimization needed. Current average: {avg_time:.2f}s")
    else:
        print("\n💥 Test failed completely")

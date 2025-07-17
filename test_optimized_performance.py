#!/usr/bin/env python3
"""
Quick performance test for the optimized CSGOSkins scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scrapers.csgoskins_scraper import CSGOSkinsGGScraper
import time

def test_performance_optimization():
    """Test scraper with optimized delays"""
    print("🚀 Testing OPTIMIZED CSGOSkins scraper performance...")
    
    # Initialize scraper with visible browser for debugging
    scraper = CSGOSkinsGGScraper(headless=False)
    
    try:
        # Test with a few quick items
        test_items = [
            "AK-47 | Redline",
            "AWP | Asiimov", 
            "M4A4 | Howl",
            "Glock-18 | Water Elemental",
            "Desert Eagle | Blaze"
        ]
        
        print(f"\n🎯 Testing {len(test_items)} items with OPTIMIZED delays...")
        print("🔧 Changes made:")
        print("   - Pattern delays: 5-10s → 1-1.5s (10th item), 3-5s → 0.5-1s (7th item)")
        print("   - Base human delays: 0.5-3s → 0.2-1s")
        print("   - Navigation delay: 1-3s → 0.2-1s")
        print("   - Verification delays: 2-6s → 0.5-2s")
        print("   - Page load delay: 1s → 0.3s")
        print("\n" + "="*60 + "\n")
        
        total_start_time = time.time()
        results = []
        
        for i, item in enumerate(test_items, 1):
            print(f"\n🔍 Item {i}/{len(test_items)}: {item}")
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
                    if 'price' in result:
                        print(f"   💰 Price: ${result['price']}")
                    elif 'prices' in result:
                        fn_price = result['prices'].get('FN', 0)
                        if fn_price > 0:
                            print(f"   💰 Factory New: ${fn_price}")
                else:
                    print(f"❌ Failed in {processing_time:.2f}s")
                
                # Show significant performance improvement
                if processing_time < 5:
                    print(f"   🚀 FAST! (under 5s)")
                elif processing_time < 10:
                    print(f"   ⚡ Good (under 10s)")
                elif processing_time < 30:
                    print(f"   ⏰ Acceptable (under 30s)")
                else:
                    print(f"   🐌 Still slow (over 30s)")
                
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
        print("\n" + "="*60)
        print("🚀 OPTIMIZED PERFORMANCE SUMMARY")
        print("="*60)
        
        successful = sum(1 for r in results if r['success'])
        avg_time = sum(r['time'] for r in results) / len(results)
        
        print(f"📊 Total items: {len(results)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {len(results) - successful}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"📈 Average per item: {avg_time:.2f}s")
        
        # Performance categories
        fast_items = sum(1 for r in results if r['time'] < 5)
        good_items = sum(1 for r in results if 5 <= r['time'] < 10)
        slow_items = sum(1 for r in results if r['time'] >= 30)
        
        print(f"\n🚀 FAST items (< 5s): {fast_items}")
        print(f"⚡ GOOD items (5-10s): {good_items}")
        print(f"🐌 SLOW items (≥ 30s): {slow_items}")
        
        if avg_time < 10:
            print(f"\n🎉 EXCELLENT! Average time is now {avg_time:.2f}s (much better than 1+ minute)")
        elif avg_time < 20:
            print(f"\n👍 GOOD! Average time is now {avg_time:.2f}s (significant improvement)")
        else:
            print(f"\n⚠️  Still room for improvement. Average: {avg_time:.2f}s")
        
        return results
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        return None
    finally:
        scraper.cleanup()
        print("\n🧹 Scraper closed")

if __name__ == "__main__":
    print("Starting OPTIMIZED performance test...")
    results = test_performance_optimization()
    
    if results:
        print("\n🎉 Performance test completed!")
        print("💡 If times are still over 10s, there may be other bottlenecks to investigate.")
    else:
        print("\n💥 Performance test failed")

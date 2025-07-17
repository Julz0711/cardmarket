#!/usr/bin/env python3
"""
Multi-instance parallel scraper for CSGOSkins.gg
Uses multiple browser instances to scrape items in parallel for dramatically improved performance
"""

import sys
import os
import time
import logging
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import random

# Add the backend directory to the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from scrapers.csgoskins_scraper import CSGOSkinsGGScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ParallelCSGOSkinsScraper:
    """
    Parallel scraper using multiple CSGOSkins.gg scraper instances
    """
    
    def __init__(self, num_instances=3, headless=True):
        """
        Initialize parallel scraper
        
        Args:
            num_instances (int): Number of parallel scraper instances (default: 3)
            headless (bool): Whether to run browsers in headless mode
        """
        self.num_instances = num_instances
        self.headless = headless
        self.scrapers = []
        self.results_queue = Queue()
        
        logger.info(f"Initializing parallel scraper with {num_instances} instances")
    
    def create_scraper_instance(self, instance_id):
        """
        Create and setup a scraper instance
        
        Args:
            instance_id (int): Unique ID for this instance
            
        Returns:
            CSGOSkinsGGScraper: Configured scraper instance
        """
        try:
            scraper = CSGOSkinsGGScraper(headless=self.headless)
            
            # Add slight delay between instance startups to avoid conflicts
            time.sleep(instance_id * 0.5)
            
            if scraper.setup_driver():
                logger.info(f"✅ Scraper instance {instance_id} ready")
                return scraper
            else:
                logger.error(f"❌ Failed to setup scraper instance {instance_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating scraper instance {instance_id}: {e}")
            return None
    
    def scrape_item_batch(self, scraper, items_batch, instance_id):
        """
        Scrape a batch of items using a single scraper instance with fresh browser per item
        
        Args:
            scraper (CSGOSkinsGGScraper): Scraper instance to use
            items_batch (list): List of items to scrape
            instance_id (int): Instance ID for logging
            
        Returns:
            list: Results from this batch
        """
        results = []
        
        try:
            logger.info(f"🚀 Instance {instance_id} starting batch of {len(items_batch)} items")
            
            for i, item_data in enumerate(items_batch):
                try:
                    item_name = item_data.get('name', '')
                    condition = item_data.get('condition', None)
                    
                    # Clean item name for search
                    clean_name = scraper.clean_item_name(item_name)
                    variant = scraper.detect_variant(item_name)
                    
                    start_time = time.time()
                    
                    # Debug timing for each search step
                    logger.info(f"Instance {instance_id}: 🔍 Starting search for '{item_name}' (condition: {condition})")
                    
                    # ENHANCED FRESH BROWSER STRATEGY: Restart browser every 2 items + randomize timing
                    if i > 0 and i % 2 == 0:
                        logger.info(f"Instance {instance_id}: 🔄 Refreshing browser for item #{i+1} to prevent slowdown")
                        scraper.close()
                        
                        # Add random delay before restarting to break patterns
                        pattern_break_delay = random.uniform(1.0, 3.0)
                        logger.info(f"Instance {instance_id}: ⏸️ Pattern-breaking delay: {pattern_break_delay:.2f}s")
                        time.sleep(pattern_break_delay)
                        
                        if not scraper.setup_driver():
                            logger.error(f"Instance {instance_id}: Failed to restart browser")
                            continue
                    
                    result = scraper.search_item(clean_name, condition, variant)
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    # Log detailed timing info
                    if processing_time > 10:  # Slow item (>10 seconds)
                        logger.warning(f"Instance {instance_id}: 🐌 SLOW ITEM: {item_name} took {processing_time:.2f}s")
                    elif processing_time > 5:  # Medium slow (>5 seconds)
                        logger.info(f"Instance {instance_id}: ⚠️ Medium slow: {item_name} took {processing_time:.2f}s")
                    else:  # Fast item (<5 seconds)
                        logger.info(f"Instance {instance_id}: ⚡ Fast: {item_name} took {processing_time:.2f}s")
                    
                    if result:
                        result['instance_id'] = instance_id
                        result['processing_time'] = processing_time
                        result['item_order'] = i + 1  # Track order within batch
                        results.append(result)
                        logger.info(f"Instance {instance_id}: ✅ {item_name} -> ${result.get('price', 0):.2f} ({processing_time:.2f}s)")
                    else:
                        logger.warning(f"Instance {instance_id}: ❌ Failed to get price for {item_name} after {processing_time:.2f}s")
                    
                    # Shorter delay between items since we're using fresh browsers
                    if i < len(items_batch) - 1:
                        time.sleep(random.uniform(0.2, 0.8))  # Reduced from 0.5-1.5
                        
                except Exception as e:
                    logger.error(f"Instance {instance_id}: Error processing {item_name}: {e}")
                    continue
            
            logger.info(f"🎯 Instance {instance_id} completed batch: {len(results)}/{len(items_batch)} successful")
            
        except Exception as e:
            logger.error(f"Instance {instance_id}: Batch processing error: {e}")
        
        finally:
            # Clean up this instance
            if scraper:
                scraper.close()
        
        return results
    
    def distribute_items(self, items_data):
        """
        Distribute items across instances for optimal load balancing
        
        Args:
            items_data (list): List of all items to scrape
            
        Returns:
            list: List of batches, one per instance
        """
        if not items_data:
            return []
        
        # Calculate items per instance
        items_per_instance = len(items_data) // self.num_instances
        remainder = len(items_data) % self.num_instances
        
        batches = []
        start_idx = 0
        
        for i in range(self.num_instances):
            # Add one extra item to first 'remainder' instances
            batch_size = items_per_instance + (1 if i < remainder else 0)
            end_idx = start_idx + batch_size
            
            if start_idx < len(items_data):
                batch = items_data[start_idx:end_idx]
                batches.append(batch)
                
                # Show which items are assigned to which instance
                item_names = [item.get('name', f'Item {idx}') for idx, item in enumerate(batch, start_idx + 1)]
                logger.info(f"Instance {i+1} assigned {len(batch)} items:")
                for idx, name in enumerate(item_names):
                    logger.info(f"   Item #{start_idx + idx + 1}: {name}")
                
                start_idx = end_idx
        
        return batches
    
    def scrape_parallel(self, items_data):
        """
        Scrape items in parallel using multiple instances
        
        Args:
            items_data (list): List of items to scrape
            
        Returns:
            list: Combined results from all instances
        """
        if not items_data:
            return []
        
        logger.info(f"🚀 Starting parallel scraping of {len(items_data)} items with {self.num_instances} instances")
        start_time = time.time()
        
        # Distribute items across instances
        item_batches = self.distribute_items(items_data)
        
        if not item_batches:
            logger.warning("No item batches created")
            return []
        
        all_results = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.num_instances) as executor:
            # Submit scraping tasks
            future_to_instance = {}
            
            for instance_id, batch in enumerate(item_batches):
                scraper = self.create_scraper_instance(instance_id + 1)
                if scraper:
                    future = executor.submit(self.scrape_item_batch, scraper, batch, instance_id + 1)
                    future_to_instance[future] = instance_id + 1
                else:
                    logger.error(f"Skipping instance {instance_id + 1} due to setup failure")
            
            # Collect results as they complete
            completed_instances = 0
            for future in as_completed(future_to_instance):
                instance_id = future_to_instance[future]
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    completed_instances += 1
                    
                    logger.info(f"✅ Instance {instance_id} completed ({completed_instances}/{len(future_to_instance)})")
                    
                except Exception as e:
                    logger.error(f"❌ Instance {instance_id} failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate performance metrics
        successful_items = len(all_results)
        total_items = len(items_data)
        success_rate = (successful_items / total_items * 100) if total_items > 0 else 0
        avg_time_per_item = total_time / successful_items if successful_items > 0 else 0
        
        logger.info(f"📊 PARALLEL SCRAPING COMPLETE")
        logger.info(f"   Total items: {total_items}")
        logger.info(f"   Successful: {successful_items} ({success_rate:.1f}%)")
        logger.info(f"   Total time: {total_time:.2f} seconds")
        logger.info(f"   Average per item: {avg_time_per_item:.2f} seconds")
        
        # Calculate performance improvement
        estimated_sequential_time = total_items * 20  # Assume 20s per item sequentially
        if total_time > 0:
            speedup = estimated_sequential_time / total_time
            logger.info(f"   🚀 Estimated speedup: {speedup:.1f}x faster than sequential")
        
        return all_results
    
    def cleanup(self):
        """Clean up all scraper instances"""
        logger.info("🧹 Cleaning up parallel scraper instances...")
        # Note: Individual scrapers are cleaned up automatically in scrape_item_batch
        # This method exists for API compatibility
        logger.info("✅ Cleanup completed")

def test_parallel_scraping():
    """Test the parallel scraping system"""
    print("🚀 Testing Parallel CSGOSkins.gg Scraping")
    print("=" * 60)
    
    # Test items - mix of weapon types and complexities
    test_items = [
        {'name': 'AK-47 | Redline', 'condition': 'FT'},           # Item 1
        {'name': 'M4A4 | Howl', 'condition': 'MW'},               # Item 2
        {'name': 'AWP | Dragon Lore', 'condition': 'FN'},         # Item 3
        {'name': 'Glock-18 | Fade', 'condition': 'FN'},          # Item 4
        {'name': 'Desert Eagle | Blaze', 'condition': 'FN'},     # Item 5
        {'name': 'StatTrak™ AK-47 | Fire Serpent', 'condition': 'MW'},  # Item 6 - PROBLEMATIC?
        {'name': 'Karambit | Gamma Doppler', 'condition': 'FN'}, # Item 7
        {'name': 'M4A1-S | Hot Rod', 'condition': 'FN'},         # Item 8 - PROBLEMATIC?
        {'name': 'AWP | Lightning Strike', 'condition': 'FN'},   # Item 9
        {'name': 'USP-S | Kill Confirmed', 'condition': 'MW'},   # Item 10
    ]
    
    # Configure parallel scraper
    num_instances = 3  # Use 3 instances for testing
    parallel_scraper = ParallelCSGOSkinsScraper(
        num_instances=num_instances, 
        headless=True  # Set to False for debugging
    )
    
    print(f"📋 Testing {len(test_items)} items with {num_instances} parallel instances")
    print(f"🎯 Expected improvement: ~{num_instances}x faster than sequential")
    print()
    
    try:
        # Run parallel scraping
        results = parallel_scraper.scrape_parallel(test_items)
        
        print("\n" + "=" * 60)
        print("📊 PARALLEL SCRAPING RESULTS")
        print("=" * 60)
        
        if results:
            # Group results by instance for analysis
            instance_results = {}
            slow_items = []
            fast_items = []
            
            for result in results:
                instance_id = result.get('instance_id', 'unknown')
                processing_time = result.get('processing_time', 0)
                
                if instance_id not in instance_results:
                    instance_results[instance_id] = []
                instance_results[instance_id].append(result)
                
                # Categorize by speed
                if processing_time > 10:
                    slow_items.append(result)
                elif processing_time < 3:
                    fast_items.append(result)
            
            print(f"✅ Total successful items: {len(results)}/{len(test_items)}")
            
            # Show results by instance
            for instance_id, instance_items in instance_results.items():
                avg_time = sum(r.get('processing_time', 0) for r in instance_items) / len(instance_items)
                min_time = min(r.get('processing_time', 0) for r in instance_items)
                max_time = max(r.get('processing_time', 0) for r in instance_items)
                print(f"   Instance {instance_id}: {len(instance_items)} items, avg {avg_time:.2f}s (range: {min_time:.1f}s - {max_time:.1f}s)")
            
            # Analyze slow items
            if slow_items:
                print(f"\n🐌 SLOW ITEMS (>10s): {len(slow_items)}")
                for item in slow_items:
                    name = item.get('item_name', 'Unknown')
                    time_taken = item.get('processing_time', 0)
                    order = item.get('item_order', '?')
                    instance = item.get('instance_id', '?')
                    print(f"   #{order} on Instance {instance}: {name} ({time_taken:.2f}s)")
            
            # Analyze fast items
            if fast_items:
                print(f"\n⚡ FAST ITEMS (<3s): {len(fast_items)}")
                for item in fast_items[:3]:  # Show first 3
                    name = item.get('item_name', 'Unknown')
                    time_taken = item.get('processing_time', 0)
                    order = item.get('item_order', '?')
                    instance = item.get('instance_id', '?')
                    print(f"   #{order} on Instance {instance}: {name} ({time_taken:.2f}s)")
            
            # Show sample prices
            print(f"\n💰 Sample Prices:")
            for result in results[:5]:
                item_name = result.get('item_name', 'Unknown')
                price = result.get('price', 0)
                condition = result.get('condition', 'N/A')
                time_taken = result.get('processing_time', 0)
                print(f"   {item_name} ({condition}): ${price:.2f} [{time_taken:.1f}s]")
            
            return True
        else:
            print("❌ No results obtained")
            return False
            
    except Exception as e:
        print(f"❌ Parallel scraping test failed: {e}")
        return False

if __name__ == '__main__':
    success = test_parallel_scraping()
    if success:
        print("\n🎉 Parallel scraping test successful!")
    else:
        print("\n💥 Parallel scraping test failed!")

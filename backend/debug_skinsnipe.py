#!/usr/bin/env python3
"""
Quick test to debug SkinSnipe search results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.skinsnipe_scraper import SkinSnipeScraper
import logging
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_skinsnipe_search():
    """Debug what happens when we search on SkinSnipe"""
    logger.info("=== SkinSnipe.com Search Debug ===")
    
    try:
        # Initialize scraper (not headless so we can see what's happening)
        scraper = SkinSnipeScraper(headless=False)
        
        logger.info("Setting up driver...")
        if not scraper.setup_driver():
            logger.error("Failed to setup driver")
            return False
        
        # Test different condition scenarios
        test_items = [
            ("AK-47 | Aquamarine Revenge", "Minimal Wear"),  # Should select MW
            ("StatTrak AK-47 | Redline", "Minimal Wear"),    # Should select ST MW
            ("AK-47 | Redline", "Field-Tested"),             # Should select FT
            ("AK-47 | Redline", "Battle-Scarred")            # Should select BS
        ]
        
        for item_name, condition in test_items:
            logger.info(f"\n=== Testing: {item_name} ({condition}) ===")
            result = scraper.search_item(item_name, condition)
            
            if result:
                logger.info(f"✅ SUCCESS: Found price: ${result['price']}")
            else:
                logger.warning("❌ No result found")
            
            # Small delay between tests
            time.sleep(3)
        
        # Keep browser open for manual inspection
        logger.info("Keeping browser open for 15 seconds for inspection...")
        time.sleep(15)
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        return False
    finally:
        try:
            if scraper and scraper.driver:
                scraper.cleanup()
                logger.info("Driver cleaned up")
        except:
            pass

if __name__ == "__main__":
    success = debug_skinsnipe_search()
    if success:
        print("\n✅ Debug test completed")
    else:
        print("\n❌ Debug test failed")
        sys.exit(1)

#!/usr/bin/env python3
"""
Debug test for AWP Dragon Lore (Battle-Scarred) price extraction issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.skinsnipe_scraper import SkinSnipeScraper
import logging
import time

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_awp_dragon_lore():
    """Debug the specific AWP Dragon Lore (Battle-Scarred) issue"""
    logger.info("=== AWP Dragon Lore (Battle-Scarred) Debug Test ===")
    
    try:
        # Initialize scraper (not headless so we can see what's happening)
        scraper = SkinSnipeScraper(headless=False)
        
        logger.info("Setting up driver...")
        if not scraper.setup_driver():
            logger.error("Failed to setup driver")
            return False
        
        item_name = "AWP | Dragon Lore"
        condition = "Battle-Scarred"
        
        logger.info(f"Testing: {item_name} ({condition})")
        
        result = scraper.search_item(item_name, condition)
        
        if result:
            price = result.get('price', 0)
            currency = result.get('currency', 'EUR')
            logger.info(f"✅ SUCCESS: Found price for {item_name} ({condition}): {currency}{price:.2f}")
        else:
            logger.warning(f"❌ FAILED: No price found for {item_name} ({condition})")
        
        # Keep browser open for manual inspection
        logger.info("Keeping browser open for 30 seconds for manual inspection...")
        time.sleep(30)
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False
    finally:
        try:
            if scraper and scraper.driver:
                scraper.cleanup()
                logger.info("Driver cleaned up")
        except:
            pass

if __name__ == "__main__":
    success = debug_awp_dragon_lore()
    if success:
        print("\n✅ AWP Dragon Lore debug test succeeded")
    else:
        print("\n❌ AWP Dragon Lore debug test failed")
        sys.exit(1)

#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.csgoskins_scraper import CSGOSkinsGGScraper
import time

def test_single_item_debug():
    """Debug price extraction for a single item"""
    scraper = CSGOSkinsGGScraper(headless=False)  # Visible for debugging
    
    try:
        print("🔧 DEBUGGING PRICE EXTRACTION")
        print("=" * 50)
        
        # Test with AK-47 Redline (should be weapon type)
        test_item = "AK-47 | Redline"
        test_condition = "FT"
        
        print(f"Testing item: {test_item}")
        print(f"Condition: {test_condition}")
        
        # Check item type detection
        item_type = scraper.detect_item_type(test_item)
        print(f"Detected item type: {item_type}")
        
        if not scraper.setup_driver():
            print("❌ Failed to setup driver")
            return
        
        # Navigate to CSGOSkins.gg
        scraper.driver.get(scraper.base_url)
        time.sleep(2)
        
        # Search for the item manually to debug
        search_input_xpath = "/html/body/nav/div/div[3]/form/div/input"
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(scraper.driver, 10)
            search_input = wait.until(EC.presence_of_element_located((By.XPATH, search_input_xpath)))
            
            search_input.clear()
            search_input.send_keys(test_item)
            time.sleep(1)
            
            # Click on first result
            result_xpath = "/html/body/nav/div/div[3]/form/div/ul/li[1]/a"
            search_result = wait.until(EC.element_to_be_clickable((By.XPATH, result_xpath)))
            search_result.click()
            
            print(f"✅ Successfully navigated to {test_item} page")
            time.sleep(3)  # Wait for page to load
            
            # Now test both extraction methods
            print("\n🔍 Testing extract_all_prices()...")
            all_prices = scraper.extract_all_prices()
            print(f"All prices result: {all_prices}")
            
            print("\n🔍 Testing extract_single_price()...")
            single_price = scraper.extract_single_price()
            print(f"Single price result: {single_price}")
            
            # Let's also check what the page structure looks like
            print("\n🏗️ Checking page structure...")
            try:
                # Check if this is actually a weapon page with multiple conditions
                summary_base_xpath = "/html/body/main/div[2]/div[1]/div[1]/div"
                summary_element = scraper.driver.find_element(By.XPATH, summary_base_xpath)
                print("✅ Found price summary section (weapon-style page)")
                
                # Count condition elements
                condition_links = scraper.driver.find_elements(By.XPATH, f"{summary_base_xpath}/a")
                print(f"Found {len(condition_links)} condition links")
                
                # Print first few condition prices for debugging
                for i, link in enumerate(condition_links[:5]):
                    try:
                        condition_text = link.text.strip()
                        print(f"  Condition {i+1}: {condition_text}")
                    except Exception as e:
                        print(f"  Condition {i+1}: Error reading text - {e}")
                        
            except Exception as e:
                print(f"❌ No weapon-style price summary found: {e}")
                
                # Maybe it's a single-price page?
                try:
                    single_price_xpath = "/html/body/main/div[2]/div[2]/div[1]/div[3]/div[3]/div[2]/span"
                    single_element = scraper.driver.find_element(By.XPATH, single_price_xpath)
                    print(f"✅ Found single price element: {single_element.text}")
                except Exception as e2:
                    print(f"❌ No single price element found either: {e2}")
            
            # Pause to let user inspect manually
            input("\n⏸️ Press Enter to continue (you can inspect the page manually)...")
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
            
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    test_single_item_debug()

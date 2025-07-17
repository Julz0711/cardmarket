#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.csgoskins_scraper import CSGOSkinsGGScraper
import time

def test_price_parsing():
    """Debug price parsing directly"""
    scraper = CSGOSkinsGGScraper()
    
    # Test different price formats
    test_prices = [
        "2.600,00",  # European: 2600.00
        "2,600.00",  # US: 2600.00  
        "$2.600",    # European thousands separator
        "$2,600",    # US thousands separator
        "€2.600,56", # European full format
        "$2,600.56", # US full format
        "2.62",      # Small price
        "2,62",      # Small price European
    ]
    
    print("🧪 Testing price parsing logic:")
    print("=" * 50)
    
    for price_text in test_prices:
        parsed = scraper.parse_price(price_text)
        print(f"'{price_text}' -> {parsed}")
    
    print("\n" + "=" * 50)

def test_hot_rod_manual():
    """Test M4A1-S Hot Rod manually to see what price text is extracted"""
    scraper = CSGOSkinsGGScraper(headless=False)
    
    try:
        if not scraper.setup_driver():
            print("❌ Failed to setup driver")
            return
        
        # Navigate and search for Hot Rod
        scraper.driver.get(scraper.base_url)
        time.sleep(2)
        
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        print("🔍 Searching for M4A1-S Hot Rod...")
        
        # Search
        search_input_xpath = "/html/body/nav/div/div[3]/form/div/input"
        wait = WebDriverWait(scraper.driver, 10)
        search_input = wait.until(EC.presence_of_element_located((By.XPATH, search_input_xpath)))
        
        search_input.clear()
        search_input.send_keys("M4A1-S | Hot Rod")
        time.sleep(1)
        
        # Click first result
        result_xpath = "/html/body/nav/div/div[3]/form/div/ul/li[1]/a"
        search_result = wait.until(EC.element_to_be_clickable((By.XPATH, result_xpath)))
        search_result.click()
        
        print("✅ Navigated to Hot Rod page")
        time.sleep(3)
        
        # Try to extract the raw price text to see what we're getting
        print("\n🔍 Extracting price elements...")
        
        try:
            # Check condition links
            summary_base_xpath = "/html/body/main/div[2]/div[1]/div[1]/div"
            condition_links = scraper.driver.find_elements(By.XPATH, f"{summary_base_xpath}/a")
            print(f"Found {len(condition_links)} condition links")
            
            for i, link in enumerate(condition_links[:3], 1):
                try:
                    link_text = link.text.strip()
                    print(f"\nCondition link {i}:")
                    print(f"  Full text: '{link_text}'")
                    
                    # Try to find price within this link
                    price_xpaths = [
                        f"{summary_base_xpath}/a[{i}]/div/div[2]/span",
                        f"{summary_base_xpath}/a[{i}]/div/div[1]/span", 
                        f"{summary_base_xpath}/a[{i}]/div/span",
                        f"{summary_base_xpath}/a[{i}]//span[contains(text(), '$')]",
                    ]
                    
                    for j, xpath in enumerate(price_xpaths):
                        try:
                            price_element = scraper.driver.find_element(By.XPATH, xpath)
                            price_text = price_element.text.strip()
                            parsed_price = scraper.parse_price(price_text)
                            print(f"  XPath {j+1}: '{price_text}' -> {parsed_price}")
                            break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"  Error: {e}")
                    
        except Exception as e:
            print(f"❌ Error extracting prices: {e}")
        
        input("\n⏸️ Press Enter to continue (inspect the page manually)...")
        
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    test_price_parsing()
    print("\n")
    test_hot_rod_manual()

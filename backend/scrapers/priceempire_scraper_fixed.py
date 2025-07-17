#!/usr/bin/env python3
"""
PriceEmpire.com Scraper - CS2 skin price aggregator with modal search
"""

import time
import random
import re
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException,
    WebDriverException
)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PriceEmpireScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.base_url = "https://pricempire.com"
        self.session_active = False
        self.max_retries = 2
        self.search_cache = {}
        self.last_request_time = 0
        self.request_count = 0
        
        # Condition mapping for PriceEmpire
        self.condition_mapping = {
            'Factory New': 'FN',
            'Minimal Wear': 'MW', 
            'Field-Tested': 'FT',
            'Well-Worn': 'WW',
            'Battle-Scarred': 'BS'
        }
        
    def setup_driver(self):
        """Initialize Chrome WebDriver with optimized options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--window-size=1920,1080")
            else:
                chrome_options.add_argument("--window-size=1920,1080")
            
            # Performance optimizations
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            
            # Anti-detection measures
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Random user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            ]
            selected_ua = random.choice(user_agents)
            chrome_options.add_argument(f"--user-agent={selected_ua}")
            
            # Disable image loading for faster performance
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.implicitly_wait(3)
            self.session_active = True
            
            logger.info(f"Chrome WebDriver initialized for PriceEmpire scraping")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False
    
    def apply_human_like_delay(self, min_delay=0.3, max_delay=1.5):
        """Apply human-like delays between requests"""
        current_time = time.time()
        
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            target_delay = random.uniform(min_delay, max_delay)
            remaining_delay = max(0, target_delay - time_since_last)
            
            if remaining_delay > 0:
                logger.debug(f"Human-like delay: {remaining_delay:.2f}s")
                time.sleep(remaining_delay)
        else:
            initial_delay = random.uniform(min_delay * 0.5, max_delay * 0.5)
            logger.debug(f"Initial delay: {initial_delay:.2f}s")
            time.sleep(initial_delay)
        
        self.last_request_time = time.time()
    
    def search_item(self, item_name, condition=None):
        """
        Search for an item on PriceEmpire.com using modal search
        
        Args:
            item_name (str): Name of the CS2 item
            condition (str): Condition filter (FN, MW, FT, WW, BS) - optional
            
        Returns:
            dict: Item data with price information
        """
        search_start_time = time.time()
        
        self.request_count += 1
        logger.info(f"Processing request #{self.request_count}: {item_name}")
        
        try:
            # Check cache first
            cache_key = f"{item_name}_{condition}"
            if cache_key in self.search_cache:
                logger.info(f"Using cached result for: {item_name}")
                return self.search_cache[cache_key]
            
            if not self.driver or not self.session_active:
                if not self.setup_driver():
                    logger.error("Failed to setup driver")
                    return None
            
            logger.info(f"Searching for item: {item_name}")
            
            # Navigate to PriceEmpire main page if not already there
            current_url = self.driver.current_url
            if not current_url.startswith("https://pricempire.com"):
                self.apply_human_like_delay()
                self.driver.get(self.base_url)
                
                # Wait for page to fully load
                wait = WebDriverWait(self.driver, 15)
                try:
                    # Wait for a key element to be present
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(5)  # Additional time for JavaScript to load
                    logger.debug("Page loaded successfully")
                except TimeoutException:
                    logger.warning("Page did not load properly")
                    return None
            
            # Find and click search button - let's try different approaches
            logger.debug("Looking for search button or input...")
            
            # First, try to find any existing search input that's immediately visible
            visible_search_inputs = self.driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'search') or contains(@placeholder, 'Search')]")
            
            if visible_search_inputs:
                logger.info("Found visible search input, using direct approach")
                search_input = visible_search_inputs[0]
                
                # Clear and type in the search input
                search_input.clear()
                time.sleep(0.3)
                
                for char in item_name:
                    search_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.1))
                
                logger.info(f"Typed search query: {item_name}")
                time.sleep(2)  # Wait for results
                
                # Look for search results dropdown or navigate
                search_results = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'search-result') or contains(@class, 'dropdown')]//a")
                
                if search_results:
                    logger.info(f"Found {len(search_results)} search results")
                    # Click first result
                    search_results[0].click()
                    time.sleep(3)
                    
                    # Extract price from item page
                    return self.extract_price_from_page(item_name, condition, search_start_time)
            
            # If no visible search input, try to find search button to open modal
            search_button_selectors = [
                "//button[contains(@class, 'search')]",
                "//button[contains(text(), 'Search')]", 
                "//button[@aria-label*='search']",
                "//button[@aria-label*='Search']",
                "//header//button",
                "//nav//button",
                "//button[contains(@data-testid, 'search')]",
                "button[aria-label*='search']",
                ".search-btn",
                "#search-btn"
            ]
            
            search_button = None
            
            for selector in search_button_selectors:
                try:
                    if selector.startswith("//"):
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    else:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = (button.get_attribute('textContent') or button.text or '').lower()
                            button_class = (button.get_attribute('class') or '').lower()
                            button_aria = (button.get_attribute('aria-label') or '').lower()
                            
                            if ('search' in button_text or 'search' in button_class or 'search' in button_aria):
                                search_button = button
                                break
                    
                    if search_button:
                        break
                        
                except Exception as e:
                    continue
            
            if search_button:
                try:
                    search_button.click()
                    logger.info("Clicked search button to open modal")
                    time.sleep(2)
                    
                    # Now look for modal input
                    modal_input_selectors = [
                        "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[1]/div/div/input",
                        "//div[contains(@class, 'modal')]//input",
                        "//div[contains(@class, 'search-modal')]//input",
                        "//input[@placeholder*='search']",
                        "//input[@placeholder*='Search']"
                    ]
                    
                    modal_input = None
                    
                    for selector in modal_input_selectors:
                        try:
                            if selector.startswith("//"):
                                inputs = self.driver.find_elements(By.XPATH, selector)
                            else:
                                inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            for input_elem in inputs:
                                if input_elem.is_displayed() and input_elem.is_enabled():
                                    modal_input = input_elem
                                    break
                            
                            if modal_input:
                                break
                        except Exception as e:
                            continue
                    
                    if modal_input:
                        logger.info("Found modal search input")
                        
                        # Clear and type search term
                        modal_input.clear()
                        time.sleep(0.3)
                        
                        for char in item_name:
                            modal_input.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.1))
                        
                        logger.info(f"Typed search query in modal: {item_name}")
                        time.sleep(2)
                        
                        # Look for search results in modal
                        result_selectors = [
                            "//div[contains(@class, 'result')]",
                            "//div[@role='option']",
                            "//button[contains(@class, 'result')]",
                            "//*[contains(text(), '" + item_name.split()[0] + "')]/.."
                        ]
                        
                        best_match = None
                        
                        for selector in result_selectors:
                            try:
                                results = self.driver.find_elements(By.XPATH, selector)
                                
                                for result in results[:5]:  # Check first 5 results
                                    result_text = result.text.lower()
                                    if any(part.lower() in result_text for part in item_name.split() if len(part) > 2):
                                        best_match = result
                                        break
                                
                                if best_match:
                                    break
                            except Exception as e:
                                continue
                        
                        if best_match:
                            best_match.click()
                            logger.info("Clicked on matching search result")
                            time.sleep(3)
                            
                            return self.extract_price_from_page(item_name, condition, search_start_time)
                        else:
                            logger.warning("No matching results found in modal")
                            return None
                    else:
                        logger.error("Could not find modal search input")
                        return None
                        
                except Exception as e:
                    logger.error(f"Error with modal search: {e}")
                    return None
            else:
                logger.error("Could not find any search button or input")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for item {item_name}: {e}")
            return None
    
    def extract_price_from_page(self, item_name, condition, search_start_time):
        """Extract price from the current item page"""
        try:
            # Try different price extraction paths
            price_selectors = [
                "/html/body/div[6]/div[2]/div[2]/div[2]/div[3]/div/div[2]/div[1]/section/div[4]/article[1]/div/div[2]/div/div[2]/div[1]/div[2]/div[1]/div/div[2]/div[2]/span",
                "//span[contains(@class, 'price')]",
                "//div[contains(@class, 'price')]//span",
                "//*[contains(text(), '$')]",
                "//article[1]//span[contains(text(), '$')]"
            ]
            
            price_text = None
            
            for selector in price_selectors:
                try:
                    if selector.startswith("//"):
                        price_elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        price_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in price_elements:
                        text = elem.text.strip()
                        if '$' in text and any(char.isdigit() for char in text):
                            price_text = text
                            break
                    
                    if price_text:
                        break
                except Exception as e:
                    continue
            
            if price_text:
                logger.debug(f"Found price text: '{price_text}'")
                price = self.parse_price(price_text)
                
                if price > 0:
                    # Try to get item name from page
                    try:
                        title_selectors = ["//h1", "//h2", "//*[contains(@class, 'title')]"]
                        found_name = item_name
                        
                        for selector in title_selectors:
                            try:
                                title_elem = self.driver.find_element(By.XPATH, selector)
                                if title_elem.text.strip():
                                    found_name = title_elem.text.strip()
                                    break
                            except:
                                continue
                    except:
                        found_name = item_name
                    
                    found_condition = self.extract_condition_from_name(found_name)
                    
                    result = {
                        'item_name': item_name,
                        'found_name': found_name,
                        'source': 'pricempire.com',
                        'timestamp': time.time(),
                        'price': price,
                        'condition': found_condition or condition,
                        'currency': 'USD'
                    }
                    
                    cache_key = f"{item_name}_{condition}"
                    self.search_cache[cache_key] = result
                    
                    search_end_time = time.time()
                    logger.info(f"TOTAL search time for {item_name}: {search_end_time - search_start_time:.2f} seconds")
                    logger.info(f"Found price for {item_name}: ${price}")
                    return result
                else:
                    logger.warning(f"Could not parse price: '{price_text}'")
                    return None
            else:
                logger.warning("No price found on page")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting price from page: {e}")
            return None
    
    def extract_condition_from_name(self, item_name):
        """Extract condition from item name"""
        name_lower = item_name.lower()
        
        if 'factory new' in name_lower or '(fn)' in name_lower:
            return 'FN'
        elif 'minimal wear' in name_lower or '(mw)' in name_lower:
            return 'MW'
        elif 'field-tested' in name_lower or '(ft)' in name_lower:
            return 'FT'
        elif 'well-worn' in name_lower or '(ww)' in name_lower:
            return 'WW'
        elif 'battle-scarred' in name_lower or '(bs)' in name_lower:
            return 'BS'
        
        return None
    
    def parse_price(self, price_text):
        """Parse price from text string"""
        try:
            if not price_text or price_text.strip() == '' or price_text.strip() == '-':
                return 0.0
            
            logger.debug(f"Parsing price from text: '{price_text}'")
            
            # Remove currency symbols and clean the text
            cleaned_text = re.sub(r'[^\d.,]', '', price_text.strip())
            
            if not cleaned_text:
                return 0.0
            
            # Handle different decimal formats
            if ',' in cleaned_text and '.' in cleaned_text:
                # Both comma and period present
                comma_pos = cleaned_text.rfind(',')
                dot_pos = cleaned_text.rfind('.')
                
                if comma_pos > dot_pos:
                    # European format: 1.234,56
                    price_str = cleaned_text.replace('.', '').replace(',', '.')
                else:
                    # US format: 1,234.56
                    price_str = cleaned_text.replace(',', '')
            elif ',' in cleaned_text:
                # Only comma - check if decimal or thousands
                parts = cleaned_text.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Likely decimal
                    price_str = cleaned_text.replace(',', '.')
                else:
                    # Likely thousands
                    price_str = cleaned_text.replace(',', '')
            elif '.' in cleaned_text:
                # Only period - check if decimal or thousands  
                parts = cleaned_text.split('.')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Likely decimal
                    price_str = cleaned_text
                else:
                    # Likely thousands
                    price_str = cleaned_text.replace('.', '')
            else:
                # No separators
                price_str = cleaned_text
            
            try:
                price = float(price_str)
                logger.debug(f"Successfully parsed price: {price}")
                return price
            except ValueError:
                logger.debug(f"Could not convert to float: '{price_str}'")
                return 0.0
                
        except Exception as e:
            logger.debug(f"Error parsing price '{price_text}': {e}")
            return 0.0
    
    def clean_item_name(self, item_name):
        """Clean item name for better search results"""
        cleaned_name = item_name
        
        # Remove condition from name if present
        conditions = ['(Factory New)', '(Minimal Wear)', '(Field-Tested)', '(Well-Worn)', '(Battle-Scarred)']
        for condition in conditions:
            cleaned_name = cleaned_name.replace(condition, '').strip()
        
        # Remove StatTrak™ symbol issues
        cleaned_name = cleaned_name.replace('StatTrak™', 'StatTrak')
        cleaned_name = cleaned_name.replace('★', '')
        
        # Remove extra whitespace
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        return cleaned_name
    
    def scrape_item_prices(self, items_data):
        """Scrape prices for multiple items"""
        results = []
        
        try:
            if not self.setup_driver():
                logger.error("Failed to setup driver for batch processing")
                return results
            
            for i, item_data in enumerate(items_data):
                item_name = item_data.get('name', '')
                condition = item_data.get('condition', None)
                
                if not item_name:
                    continue
                
                try:
                    clean_name = self.clean_item_name(item_name)
                    result = self.search_item(clean_name, condition)
                    
                    if result:
                        results.append(result)
                    else:
                        # Add failed result
                        results.append({
                            'item_name': item_name,
                            'condition': condition,
                            'price': 0.0,
                            'currency': 'USD',
                            'source': 'pricempire.com',
                            'timestamp': time.time(),
                            'error': 'No price found'
                        })
                    
                    # Delay between requests
                    if i < len(items_data) - 1:
                        self.apply_human_like_delay()
                    
                except Exception as e:
                    logger.error(f"Error processing item {item_name}: {e}")
                    results.append({
                        'item_name': item_name,
                        'condition': condition,
                        'price': 0.0,
                        'currency': 'USD',
                        'source': 'pricempire.com',
                        'timestamp': time.time(),
                        'error': str(e)
                    })
                    continue
                
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
        finally:
            self.cleanup()
        
        return results
    
    def cleanup(self):
        """Close the WebDriver and clear session state"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome WebDriver closed")
            except Exception as e:
                logger.debug(f"Error closing driver: {e}")
            finally:
                self.driver = None
                self.session_active = False
    
    def clear_cache(self):
        """Clear the search cache"""
        self.search_cache.clear()
        logger.info("Search cache cleared")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

# Usage example
if __name__ == "__main__":
    # Example usage
    with PriceEmpireScraper(headless=False) as scraper:
        result = scraper.search_item("AK-47 | Redline")
        if result:
            print(f"Found price: {result}")
        else:
            print("No results found")

"""
CSFloat Market Price Scraper
Scrapes current market prices for CS2 items from csfloat.com
"""

import logging
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

logger = logging.getLogger(__name__)

class CSFloatScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://csfloat.com/search"
        
        # Condition mapping
        self.condition_buttons = {
            'FN': 1,  # Factory New
            'MW': 2,  # Minimal Wear
            'FT': 3,  # Field-Tested
            'WW': 4,  # Well-Worn
            'BS': 5   # Battle-Scarred
        }
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with options"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False
    
    def search_item(self, item_name, condition=None):
        """
        Search for an item on CSFloat market
        
        Args:
            item_name (str): Name of the CS2 item
            condition (str): Condition filter (FN, MW, FT, WW, BS)
            
        Returns:
            dict: Item data with price information
        """
        try:
            if not self.driver:
                if not self.setup_driver():
                    return None
            
            logger.info(f"Searching for item: {item_name} (condition: {condition})")
            
            # Navigate to CSFloat search page
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Wait for page to load and find search input
            wait = WebDriverWait(self.driver, 15)
            
            # Find search input field - try multiple selectors
            search_input = None
            selectors = [
                "input[placeholder*='Search']",
                "input[placeholder*='search']",
                "input.mat-mdc-input-element",
                "#mat-input-18",
                "input[matinput]",
                "input[type='text']"
            ]
            
            for selector in selectors:
                try:
                    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"Found search input with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not search_input:
                logger.error("Could not find search input field")
                return None
            
            # Make sure input is visible and clickable
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors[0])))
            except:
                pass
            
            # Clear and enter item name
            search_input.clear()
            search_input.send_keys(item_name)
            time.sleep(3)  # Wait for suggestions to load
            
            # Try to click on first search suggestion
            suggestion_clicked = False
            suggestion_selectors = [
                "//mat-option[1]",
                "//mat-option[contains(@class, 'mat-option')][1]",
                ".mat-option:first-child",
                "mat-option:first-of-type"
            ]
            
            for selector in suggestion_selectors:
                try:
                    if selector.startswith("//"):
                        suggestion = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        suggestion = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    suggestion.click()
                    suggestion_clicked = True
                    logger.info(f"Clicked search suggestion with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not suggestion_clicked:
                logger.info("No suggestions found, pressing Enter")
                search_input.send_keys("\n")
            
            time.sleep(2)
            
            # Set condition filter if specified
            if condition and condition.upper() in self.condition_buttons:
                try:
                    condition_button_index = self.condition_buttons[condition.upper()]
                    condition_xpath = f"/html/body/app-root/div/div[2]/app-market-search/app-search/app-filter-content-container/div/div[1]/app-advanced-search/div/app-search-row[2]/div/div[2]/div/div[3]/div[{condition_button_index}]"
                    
                    condition_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, condition_xpath))
                    )
                    condition_button.click()
                    time.sleep(1)
                    logger.info(f"Applied condition filter: {condition}")
                    
                except TimeoutException:
                    logger.warning(f"Could not apply condition filter: {condition}")
            
            # Wait for search results to load and update
            time.sleep(4)  # Give more time for search to complete
            
            # Check if we have search results
            try:
                # Wait for items to load - look for item cards
                items_container_xpath = "//app-item-container/div/item-card"
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, items_container_xpath))
                )
                logger.info("Search results loaded successfully")
            except TimeoutException:
                logger.warning(f"No search results found for {item_name}")
                return None
            
            # Try to find the first item result that matches our search
            first_item_xpath = "/html/body/app-root/div/div[2]/app-market-search/app-search/app-filter-content-container/div/div[2]/div/app-item-container/div/item-card[1]"
            
            try:
                first_item = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, first_item_xpath))
                )
                
                # Extract price from the first item
                price = self.extract_price_from_item(first_item)
                
                if price:
                    result = {
                        'item_name': item_name,
                        'condition': condition,
                        'price': price,
                        'currency': 'USD',  # CSFloat typically shows USD
                        'source': 'csfloat.com',
                        'timestamp': time.time()
                    }
                    
                    logger.info(f"Found price for {item_name}: ${price}")
                    return result
                else:
                    logger.warning(f"Could not extract price for {item_name}")
                    return None
                    
            except TimeoutException:
                logger.warning(f"No search results found for {item_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for item {item_name}: {e}")
            return None
    
    def extract_price_from_item(self, item_element):
        """
        Extract price from an item card element
        
        Args:
            item_element: Selenium WebElement of the item card
            
        Returns:
            float: Price in USD or None if not found
        """
        try:
            # Get all text from the item element
            item_text = item_element.text
            logger.debug(f"Item element text: {item_text}")
            
            # Try different price selectors with more specific patterns
            price_selectors = [
                ".price",
                ".item-price", 
                "[class*='price']",
                ".mat-card-content",
                ".item-info",
                "span",
                "div"
            ]
            
            found_prices = []
            
            for selector in price_selectors:
                try:
                    price_elements = item_element.find_elements(By.CSS_SELECTOR, selector)
                    for price_element in price_elements:
                        price_text = price_element.text.strip()
                        
                        # Look for price patterns: $X.XX, X.XX, $X, etc.
                        price_matches = re.findall(r'\$?(\d+(?:\.\d{1,2})?)', price_text)
                        for match in price_matches:
                            price = float(match)
                            # Filter reasonable prices (between $0.01 and $100,000)
                            if 0.01 <= price <= 100000:
                                found_prices.append(price)
                                
                except Exception:
                    continue
            
            # If no structured price found, try regex on full text
            if not found_prices:
                price_matches = re.findall(r'\$?(\d+(?:\.\d{1,2})?)', item_text)
                for match in price_matches:
                    price = float(match)
                    # Filter reasonable prices
                    if 0.01 <= price <= 100000:
                        found_prices.append(price)
            
            if found_prices:
                # Return the most reasonable price (usually the first valid one)
                price = found_prices[0]
                logger.info(f"Extracted price: ${price}")
                return price
            
            logger.warning("Could not extract price from item element")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting price: {e}")
            return None
    
    def scrape_item_prices(self, items_data):
        """
        Scrape prices for multiple items
        
        Args:
            items_data (list): List of dicts with 'name' and optionally 'condition'
            
        Returns:
            list: List of price results
        """
        results = []
        
        try:
            for item_data in items_data:
                item_name = item_data.get('name', '')
                condition = item_data.get('condition', None)
                
                if not item_name:
                    continue
                
                # Skip items like coins, medals, stock guns, etc.
                if self.should_skip_item(item_name):
                    logger.info(f"Skipping item: {item_name} (not suitable for pricing)")
                    results.append({
                        'item_name': item_name,
                        'condition': condition,
                        'price': 0.0,
                        'currency': 'USD',
                        'source': 'csfloat.com',
                        'timestamp': time.time(),
                        'skipped': True,
                        'skip_reason': 'Item type not suitable for pricing'
                    })
                    continue
                
                # Setup fresh driver for each item to avoid session issues
                if not self.setup_driver():
                    logger.error(f"Failed to setup driver for {item_name}")
                    continue
                
                try:
                    # Clean item name for search
                    clean_name = self.clean_item_name(item_name)
                    
                    result = self.search_item(clean_name, condition)
                    if result:
                        results.append(result)
                    
                    # Add delay between requests to avoid rate limiting
                    time.sleep(2)
                    
                finally:
                    # Clean up driver after each item
                    self.cleanup()
                
        except Exception as e:
            logger.error(f"Error scraping item prices: {e}")
            self.cleanup()
        
        return results
    
    def should_skip_item(self, item_name):
        """
        Check if an item should be skipped (coins, stock guns, etc.)
        
        Args:
            item_name (str): Name of the item
            
        Returns:
            bool: True if item should be skipped
        """
        skip_keywords = [
            'coin',
            'medal',
            'badge',
            'service medal',
            'operation',
            'music kit',
            'graffiti',
            'patch',
            'sticker',
            'case',
            'key'
        ]
        
        # Check for stock guns (no skin name after |)
        if '|' not in item_name:
            # Skip if it's just a base weapon name like "AK-47", "AWP", etc.
            base_weapons = [
                'ak-47', 'awp', 'm4a4', 'm4a1-s', 'glock-18', 'usp-s', 
                'deagle', 'desert eagle', 'p250', 'five-seven', 'tec-9',
                'cz75-auto', 'dual berettas', 'p2000', 'famas', 'galil ar',
                'ssg 08', 'aug', 'sg 553', 'g3sg1', 'scar-20', 'negev',
                'm249', 'nova', 'xm1014', 'mag-7', 'sawed-off', 'mac-10',
                'mp9', 'mp7', 'ump-45', 'p90', 'pp-bizon', 'mp5-sd'
            ]
            
            item_lower = item_name.lower().strip()
            if item_lower in base_weapons:
                return True
        
        # Check for skip keywords
        item_lower = item_name.lower()
        for keyword in skip_keywords:
            if keyword in item_lower:
                return True
        
        return False

    def clean_item_name(self, item_name):
        """
        Clean item name for better search results
        
        Args:
            item_name (str): Original item name
            
        Returns:
            str: Cleaned item name
        """
        # Remove condition from name if present
        conditions = ['(Factory New)', '(Minimal Wear)', '(Field-Tested)', '(Well-Worn)', '(Battle-Scarred)']
        cleaned_name = item_name
        
        for condition in conditions:
            cleaned_name = cleaned_name.replace(condition, '').strip()
        
        # Remove extra whitespace
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        return cleaned_name
    
    def extract_condition_from_name(self, item_name):
        """
        Extract condition from item name
        
        Args:
            item_name (str): Item name that may contain condition
            
        Returns:
            str: Condition code (FN, MW, FT, WW, BS) or None
        """
        condition_mapping = {
            'Factory New': 'FN',
            'Minimal Wear': 'MW',
            'Field-Tested': 'FT',
            'Well-Worn': 'WW',
            'Battle-Scarred': 'BS'
        }
        
        for condition_name, condition_code in condition_mapping.items():
            if condition_name in item_name:
                return condition_code
        
        return None
    
    def cleanup(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")

# Usage example
if __name__ == "__main__":
    scraper = CSFloatScraper(headless=False)  # Set to False for debugging
    
    # Test with realistic items (mix of valid and skippable items)
    test_items = [
        {'name': 'AK-47 | Redline', 'condition': 'FT'},
        {'name': 'AWP | Dragon Lore', 'condition': 'FN'},
        {'name': 'Austin 2025 Silver Coin', 'condition': None},  # Should be skipped
        {'name': 'AK-47', 'condition': None},  # Stock gun, should be skipped
        {'name': 'M4A4 | Asiimov', 'condition': 'FT'}
    ]
    
    results = scraper.scrape_item_prices(test_items)
    
    for result in results:
        if result.get('skipped'):
            print(f"SKIPPED - {result['item_name']}: {result['skip_reason']}")
        else:
            print(f"Item: {result['item_name']}")
            print(f"Condition: {result['condition']}")
            print(f"Price: ${result['price']}")
        print("---")

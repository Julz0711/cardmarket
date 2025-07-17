#!/usr/bin/env python3
"""
PriceEmpire.com Scraper - CS2 skin price aggregator with live search
"""

import time
import random
import re
import logging
from selenium import webdriver
from selenium.webdriver.common.by impo            if not search_button:
                logger.error("Could not find search button")
                # Let's try to find any clickable search-related elements
                logger.debug("Trying to find alternative search elements...")
                
                # Check for search icons or inputs that might be clickable
                search_elements = self.driver.find_elements(By.XPATH, "//*[contains(@placeholder, 'search') or contains(@placeholder, 'Search')]")
                if search_elements:
                    logger.info(f"Found {len(search_elements)} search input elements, trying first one")
                    search_button = search_elements[0]
                else:
                    return None
            
            try:
                # Click the search button/element
                search_button.click()
                logger.info("Clicked search element to open modal")
                time.sleep(2)  # Wait for modal to open
                
            except Exception as e:
                logger.error(f"Error clicking search element: {e}")
                return None
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
        self.base_url = "https://pricempire.com/cs2-skin-search"
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
                self.driver.get("https://pricempire.com")
                
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
            
            # Click the search button to open modal
            search_button_xpath = "/html/body/div[6]/div[2]/header/div/div[3]/div/button"
            
            # Try multiple possible search button selectors
            search_button_selectors = [
                "/html/body/div[6]/div[2]/header/div/div[3]/div/button",
                "//button[contains(@class, 'search')]",
                "//button[contains(text(), 'Search')]", 
                "//button[@aria-label*='search']",
                "//button[@aria-label*='Search']",
                "//header//button",
                "//nav//button",
                "//*[@role='button' and contains(@class, 'search')]",
                "button[data-testid*='search']",
                ".search-button",
                "#search-button"
            ]
            
            search_button = None
            wait = WebDriverWait(self.driver, 10)
            
            # Debug: Check page structure
            logger.debug(f"Current URL: {self.driver.current_url}")
            logger.debug("Looking for search button...")
            
            # Try to find all buttons first
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.debug(f"Found {len(all_buttons)} button elements on page")
            
            for i, selector in enumerate(search_button_selectors):
                logger.debug(f"Trying search button selector {i+1}/{len(search_button_selectors)}: {selector}")
                try:
                    if selector.startswith("/"):
                        # XPath selector
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS selector
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    logger.debug(f"Found {len(buttons)} elements with selector: {selector}")
                    
                    for j, button in enumerate(buttons):
                        try:
                            if button.is_displayed() and button.is_enabled():
                                button_text = button.get_attribute('textContent') or button.text or ''
                                button_class = button.get_attribute('class') or ''
                                button_aria = button.get_attribute('aria-label') or ''
                                
                                logger.debug(f"Button {j+1}: text='{button_text[:30]}...', class='{button_class}', aria='{button_aria}'")
                                
                                # Check if this looks like a search button
                                if ('search' in button_text.lower() or 
                                    'search' in button_class.lower() or 
                                    'search' in button_aria.lower() or
                                    '🔍' in button_text or
                                    'magnify' in button_class.lower()):
                                    search_button = button
                                    logger.info(f"Found potential search button: {selector}")
                                    break
                        except Exception as e:
                            logger.debug(f"Error checking button {j+1}: {e}")
                            continue
                    
                    if search_button:
                        break
                        
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Wait for modal to appear and find the input field
            modal_input_xpath = "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[1]/div/div/input"
            
            try:
                modal_input = wait.until(EC.element_to_be_clickable((By.XPATH, modal_input_xpath)))
                logger.info("Found modal search input")
                
                # Clear and enter item name
                modal_input.clear()
                time.sleep(0.3)
                
                # Type the item name character by character for live search
                for char in item_name:
                    modal_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.1))  # Human-like typing
                
                logger.info(f"Typed search query in modal: {item_name}")
                
                # Wait for search results to appear
                time.sleep(2)
                
                # Look for specific search results that match our condition
                # The results should appear in the modal as individual items with conditions
                search_results_xpath = "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[2]//div[contains(@class, 'result') or contains(@role, 'option')]"
                
                try:
                    # Wait for search results to appear
                    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[2]")))
                    
                    # Get all search result options
                    search_results = self.driver.find_elements(By.XPATH, search_results_xpath)
                    
                    if not search_results:
                        # Try alternative selectors for search results
                        alternative_selectors = [
                            "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[2]//*[contains(text(), 'AK-47') or contains(text(), 'Redline')]/..",
                            "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[2]//button",
                            "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[2]//div[@role='option']",
                            "/html/body/div[6]/div[2]/header/div/div[3]/div/div[1]/div[2]/div/div[2]//*[contains(@class, 'item')]"
                        ]
                        
                        for selector in alternative_selectors:
                            search_results = self.driver.find_elements(By.XPATH, selector)
                            if search_results:
                                logger.debug(f"Found {len(search_results)} results with alternative selector")
                                break
                    
                    logger.debug(f"Found {len(search_results)} search results in modal")
                    
                    # Find the best matching result based on condition
                    best_match = None
                    target_condition_lower = condition.lower() if condition else None
                    
                    for i, result in enumerate(search_results[:10]):  # Check first 10 results
                        try:
                            result_text = result.text.strip().lower()
                            logger.debug(f"Result {i+1}: '{result_text[:100]}...'")
                            
                            # Check if this result matches our item and condition
                            item_parts = item_name.lower().split()
                            item_matches = all(part in result_text for part in item_parts if len(part) > 2)
                            
                            if item_matches:
                                if not condition:
                                    # No specific condition requested, take first match
                                    best_match = result
                                    logger.info(f"Found matching result (no condition filter): {result_text[:50]}...")
                                    break
                                elif target_condition_lower:
                                    # Check for condition match
                                    condition_patterns = {
                                        'fn': ['factory new', 'fn', '(fn)'],
                                        'mw': ['minimal wear', 'mw', '(mw)'],
                                        'ft': ['field-tested', 'ft', '(ft)'],
                                        'ww': ['well-worn', 'ww', '(ww)'],
                                        'bs': ['battle-scarred', 'bs', '(bs)']
                                    }
                                    
                                    if target_condition_lower in condition_patterns:
                                        if any(pattern in result_text for pattern in condition_patterns[target_condition_lower]):
                                            best_match = result
                                            logger.info(f"Found matching result with condition {condition}: {result_text[:50]}...")
                                            break
                                    elif target_condition_lower in result_text:
                                        best_match = result
                                        logger.info(f"Found matching result with condition {condition}: {result_text[:50]}...")
                                        break
                        
                        except Exception as e:
                            logger.debug(f"Error checking result {i+1}: {e}")
                            continue
                    
                    if not best_match and search_results:
                        # If no perfect match, try the first result that contains our item name
                        for result in search_results[:5]:
                            try:
                                result_text = result.text.strip().lower()
                                item_parts = item_name.lower().split()
                                if any(part in result_text for part in item_parts if len(part) > 2):
                                    best_match = result
                                    logger.info(f"Using first available match: {result_text[:50]}...")
                                    break
                            except Exception as e:
                                continue
                    
                    if best_match:
                        # Click on the best matching result
                        best_match.click()
                        logger.info("Clicked on matching search result")
                        time.sleep(3)  # Wait for navigation to item page
                        
                        # Now we should be on the item page, extract price from first recommended marketplace
                        first_marketplace_xpath = "/html/body/div[6]/div[2]/div[2]/div[2]/div[3]/div/div[2]/div[1]/section/div[4]/article[1]"
                        price_xpath = "/html/body/div[6]/div[2]/div[2]/div[2]/div[3]/div/div[2]/div[1]/section/div[4]/article[1]/div/div[2]/div/div[2]/div[1]/div[2]/div[1]/div/div[2]/div[2]/span"
                        
                        try:
                            # Wait for the marketplace section to load
                            wait.until(EC.presence_of_element_located((By.XPATH, first_marketplace_xpath)))
                            
                            # Extract the price
                            price_element = self.driver.find_element(By.XPATH, price_xpath)
                            price_text = price_element.text.strip()
                            
                            logger.debug(f"Found price text: '{price_text}'")
                            
                            price = self.parse_price(price_text)
                            
                            if price > 0:
                                # Extract item name and condition from page if possible
                                try:
                                    # Try to get the exact item name from the page
                                    item_title_selectors = [
                                        "//h1",
                                        "//h2", 
                                        "//*[contains(@class, 'title')]",
                                        "//*[contains(@class, 'name')]"
                                    ]
                                    
                                    found_name = item_name  # Default to search term
                                    for selector in item_title_selectors:
                                        try:
                                            title_element = self.driver.find_element(By.XPATH, selector)
                                            if title_element.text.strip():
                                                found_name = title_element.text.strip()
                                                break
                                        except:
                                            continue
                                
                                except Exception as e:
                                    logger.debug(f"Could not extract item name from page: {e}")
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
                                
                                self.search_cache[cache_key] = result
                                
                                search_end_time = time.time()
                                logger.info(f"TOTAL search time for {item_name}: {search_end_time - search_start_time:.2f} seconds")
                                logger.info(f"Found price for {item_name}: ${price}")
                                return result
                            else:
                                logger.warning(f"Could not parse price: '{price_text}'")
                                return None
                                
                        except Exception as e:
                            logger.error(f"Error extracting price from marketplace: {e}")
                            return None
                    
                    else:
                        logger.warning(f"No matching search results found for {item_name}")
                        return None
                
                except TimeoutException:
                    logger.warning("No search results appeared in modal")
                    return None
                    
            except TimeoutException:
                logger.error("Could not find modal search input")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for item {item_name}: {e}")
            return None
    
    def get_condition_price_from_item_page(self, first_result_element, item_name, condition, search_start_time):
        """
        Navigate to item page and extract price for specific condition from variants table
        
        Args:
            first_result_element: WebElement of the first search result
            item_name (str): Original item name
            condition (str): Desired condition
            search_start_time (float): Start time for performance tracking
            
        Returns:
            dict: Item data with condition-specific price
        """
        try:
            # Click on the first result to go to item page
            first_result_element.click()
            logger.info("Clicked on first result, navigating to item page")
            
            # Wait for item page to load
            time.sleep(3)
            
            # Find the variants table (updated structure)
            variants_table_xpath = "/html/body/div[16]/div[2]/div[2]/div[2]/div[3]/div/div[1]/div[1]/div/div[4]"
            
            try:
                wait = WebDriverWait(self.driver, 10)
                variants_table = wait.until(EC.presence_of_element_located((By.XPATH, variants_table_xpath)))
                
                # Get all variant links in the table (updated structure)
                variant_links_xpath = "/html/body/div[16]/div[2]/div[2]/div[2]/div[3]/div/div[1]/div[1]/div/div[4]/div[2]/a"
                variant_links = variants_table.find_elements(By.XPATH, variant_links_xpath)
                
                logger.debug(f"Found {len(variant_links)} variant options")
                
                # Search for the matching condition
                target_condition = condition.upper() if condition else None
                
                for i, link in enumerate(variant_links, 1):
                    try:
                        # Get the condition text from the link
                        condition_text = link.text.strip()
                        logger.debug(f"Variant {i}: '{condition_text}'")
                        
                        # Check if this matches our target condition
                        if self.condition_matches(condition_text, target_condition):
                            logger.info(f"Found matching condition variant: '{condition_text}'")
                            
                            # Extract price from this variant (updated structure - simplified)
                            # price_xpath = f"/html/body/div[16]/div[2]/div[2]/div[2]/div[3]/div/div[1]/div[1]/div/div[4]/div[2]/a[{i}]/div[2]/span"
                            
                            try:
                                price_element = link.find_element(By.XPATH, f"./div[2]/span")
                                price_text = price_element.text.strip()
                                
                                logger.debug(f"Found condition price: '{price_text}'")
                                
                                price = self.parse_price(price_text)
                                
                                if price > 0:
                                    result = {
                                        'item_name': item_name,
                                        'found_name': f"{item_name} ({condition_text})",
                                        'source': 'pricempire.com',
                                        'timestamp': time.time(),
                                        'price': price,
                                        'condition': target_condition or self.extract_condition_from_name(condition_text),
                                        'currency': 'USD'
                                    }
                                    
                                    cache_key = f"{item_name}_{condition}"
                                    self.search_cache[cache_key] = result
                                    
                                    search_end_time = time.time()
                                    logger.info(f"TOTAL search time for {item_name}: {search_end_time - search_start_time:.2f} seconds")
                                    logger.info(f"Found condition price for {item_name} ({condition_text}): ${price}")
                                    return result
                                else:
                                    logger.warning(f"Could not parse price: '{price_text}'")
                                    
                            except NoSuchElementException:
                                logger.debug(f"No price element found for variant {i}")
                                continue
                    
                    except Exception as e:
                        logger.debug(f"Error checking variant {i}: {e}")
                        continue
                
                # If no specific condition found, try to get the first available price
                if variant_links and not target_condition:
                    try:
                        first_link = variant_links[0]
                        condition_text = first_link.text.strip()
                        price_element = first_link.find_element(By.XPATH, "./div[2]/span")
                        price_text = price_element.text.strip()
                        
                        price = self.parse_price(price_text)
                        
                        if price > 0:
                            result = {
                                'item_name': item_name,
                                'found_name': f"{item_name} ({condition_text})",
                                'source': 'pricempire.com',
                                'timestamp': time.time(),
                                'price': price,
                                'condition': self.extract_condition_from_name(condition_text),
                                'currency': 'USD'
                            }
                            
                            cache_key = f"{item_name}_{condition}"
                            self.search_cache[cache_key] = result
                            
                            search_end_time = time.time()
                            logger.info(f"TOTAL search time for {item_name}: {search_end_time - search_start_time:.2f} seconds")
                            logger.info(f"Found first available price for {item_name}: ${price}")
                            return result
                    
                    except Exception as e:
                        logger.debug(f"Error getting first variant price: {e}")
                
                logger.warning(f"No matching condition found for {item_name} with condition {condition}")
                return None
                
            except TimeoutException:
                logger.warning("Variants table not found on item page")
                return None
                
        except Exception as e:
            logger.error(f"Error getting condition price from item page: {e}")
            return None
    
    def condition_matches(self, condition_text, target_condition):
        """
        Check if condition text matches target condition
        
        Args:
            condition_text (str): Condition text from the website
            target_condition (str): Target condition code (FN, MW, FT, WW, BS)
            
        Returns:
            bool: True if conditions match
        """
        if not target_condition:
            return True  # Accept any condition if none specified
        
        condition_lower = condition_text.lower()
        target_lower = target_condition.lower()
        
        # Direct matches
        condition_map = {
            'fn': ['factory new', 'fn'],
            'mw': ['minimal wear', 'mw'],
            'ft': ['field-tested', 'ft'],
            'ww': ['well-worn', 'ww'],
            'bs': ['battle-scarred', 'bs']
        }
        
        if target_lower in condition_map:
            return any(keyword in condition_lower for keyword in condition_map[target_lower])
        
        return target_lower in condition_lower
    
    def extract_condition_from_name(self, item_name):
        """
        Extract condition from item name
        
        Args:
            item_name (str): Full item name potentially containing condition
            
        Returns:
            str: Condition code or None
        """
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
        """
        Parse price from text string
        
        Args:
            price_text (str): Raw price text from website
            
        Returns:
            float: Parsed price or 0.0 if parsing fails
        """
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
        """
        Scrape prices for multiple items
        
        Args:
            items_data (list): List of dicts with 'name' and optionally 'condition'
            
        Returns:
            list: List of price results
        """
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

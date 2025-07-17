#!/usr/bin/env python3
"""
CSGOStocks.de Scraper - CS2 skin price aggregator
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

class CSGOStocksScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.base_url = "https://csgostocks.de"
        self.session_active = False
        self.max_retries = 2
        self.search_cache = {}
        self.last_request_time = 0
        self.request_count = 0
        
        # Condition mapping for CSGOStocks
        self.condition_mapping = {
            'Factory New': 'Factory New',
            'Minimal Wear': 'Minimal Wear', 
            'Field-Tested': 'Field-Tested',
            'Well-Worn': 'Well-Worn',
            'Battle-Scarred': 'Battle Scarred'
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
            
            self.driver.implicitly_wait(5)
            self.session_active = True
            
            logger.info(f"Chrome WebDriver initialized for CSGOStocks scraping")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False
    
    def apply_human_like_delay(self, min_delay=0.2, max_delay=1.0):
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
    
    def handle_cookie_popup(self):
        """Handle cookie popup if present"""
        try:
            # Use the specific XPaths you found for CSGOStocks.de cookie popup
            cookie_overlay_xpath = "/html/body/div"
            cookie_box_xpath = "/html/body/div/div[2]"
            cookie_accept_xpath = "/html/body/div/div[2]/div[2]/div[2]/div[2]/button[1]"
            
            # First check if cookie overlay exists
            try:
                overlay = self.driver.find_element(By.XPATH, cookie_overlay_xpath)
                if overlay.is_displayed():
                    logger.info("Found cookie overlay")
                    
                    # Check if the accept button exists and is clickable
                    try:
                        accept_button = self.driver.find_element(By.XPATH, cookie_accept_xpath)
                        if accept_button.is_displayed() and accept_button.is_enabled():
                            logger.info("Found cookie accept button")
                            
                            # Scroll to button and click it
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", accept_button)
                            time.sleep(0.5)
                            
                            try:
                                accept_button.click()
                                logger.info("Clicked cookie accept button")
                            except:
                                # Try JavaScript click if regular click fails
                                self.driver.execute_script("arguments[0].click();", accept_button)
                                logger.info("Clicked cookie accept button with JavaScript")
                            
                            # Wait for popup to disappear
                            time.sleep(2)
                            
                            # Verify the overlay is gone
                            try:
                                remaining_overlay = self.driver.find_element(By.XPATH, cookie_overlay_xpath)
                                if not remaining_overlay.is_displayed():
                                    logger.info("Cookie popup successfully closed")
                                else:
                                    logger.warning("Cookie overlay still visible after clicking accept")
                            except:
                                logger.info("Cookie popup successfully closed (overlay element not found)")
                            
                        else:
                            logger.debug("Cookie accept button not interactable")
                    except Exception as e:
                        logger.debug(f"Could not find cookie accept button: {e}")
                else:
                    logger.debug("Cookie overlay not visible")
            except Exception as e:
                logger.debug(f"No cookie overlay found: {e}")
                
            # Fallback: try generic cookie popup handling if specific XPaths don't work
            if self.driver.find_elements(By.XPATH, "//div[contains(@class, 'fc-dialog-overlay')]"):
                logger.info("Found generic cookie popup, trying fallback methods")
                
                generic_selectors = [
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'Akzeptieren')]",
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(text(), 'Verstanden')]",
                    "//button[contains(text(), 'Zustimmen')]",
                    "//button[contains(@class, 'fc-')]",
                    "//div[contains(@class, 'fc-')]//button"
                ]
                
                for selector in generic_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                try:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    logger.info(f"Clicked generic cookie button with selector: {selector}")
                                    time.sleep(2)
                                    return
                                except:
                                    continue
                    except:
                        continue
                
        except Exception as e:
            logger.debug(f"Error handling cookie popup: {e}")
    
    def find_and_select_exact_match(self, formatted_name, original_item_name, condition):
        """
        Find and select the exact match from dropdown search results
        
        Args:
            formatted_name (str): The formatted search term we typed
            original_item_name (str): The original item name without condition
            condition (str): The condition filter
            
        Returns:
            bool: True if exact match was found and selected, False otherwise
        """
        try:
            # Wait a moment for dropdown to appear
            time.sleep(1)
            
            # Look for dropdown container first
            dropdown_container = None
            container_selectors = [
                "//div[contains(@class, 'dropdown')]",
                "//div[contains(@class, 'autocomplete')]",
                "//div[contains(@class, 'suggestion')]",
                "//ul[contains(@class, 'dropdown')]",
                "//div[@role='listbox']"
            ]
            
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    if containers:
                        dropdown_container = containers[0]
                        logger.debug(f"Found dropdown container with selector: {selector}")
                        break
                except:
                    continue
            
            # Look for dropdown results - try multiple selectors
            dropdown_selectors = [
                "//div[contains(@class, 'dropdown')]//div[contains(@class, 'item')]",
                "//div[contains(@class, 'suggestion')]",
                "//div[contains(@class, 'autocomplete')]//div",
                "//ul[contains(@class, 'dropdown')]//li",
                "//div[@role='option']",
                "//div[contains(@class, 'search-result')]",
                # More specific for weapon results
                "//div[contains(text(), 'UMP-45') or contains(text(), 'AWP') or contains(text(), 'AK-47')]",
                "//*[contains(text(), '" + original_item_name.split('|')[0].strip() + "')]"
            ]
            
            dropdown_results = []
            
            # Try each selector to find dropdown results
            for selector in dropdown_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.debug(f"Found {len(elements)} dropdown elements with selector: {selector}")
                        dropdown_results = elements
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not dropdown_results:
                logger.debug("No dropdown results found")
                return False
            
            logger.info(f"Found {len(dropdown_results)} dropdown results, looking for exact match")
            
            # Scroll through dropdown if possible to find more results
            if dropdown_container:
                try:
                    # Scroll down a few times to load more results
                    for i in range(3):
                        self.driver.execute_script("arguments[0].scrollTop += 200;", dropdown_container)
                        time.sleep(0.3)
                        
                        # Get updated results after scrolling
                        for selector in dropdown_selectors:
                            try:
                                new_elements = self.driver.find_elements(By.XPATH, selector)
                                if len(new_elements) > len(dropdown_results):
                                    dropdown_results = new_elements
                                    logger.debug(f"Found {len(dropdown_results)} results after scrolling")
                                    break
                            except:
                                continue
                except Exception as e:
                    logger.debug(f"Error scrolling dropdown: {e}")
            
            # Analyze each result to find the best match
            skin_matches = []
            sticker_matches = []
            
            for i, result in enumerate(dropdown_results[:20]):  # Limit to first 20 results
                try:
                    result_text = result.text.strip()
                    if not result_text:
                        continue
                    
                    logger.debug(f"Dropdown result {i+1}: '{result_text}'")
                    
                    # Categorize results
                    result_lower = result_text.lower()
                    
                    # Skip stickers unless we're specifically looking for one
                    if 'sticker' in result_lower and 'sticker' not in original_item_name.lower():
                        logger.debug(f"Skipping sticker result: '{result_text}'")
                        sticker_matches.append((result, result_text))
                        continue
                    
                    # Check for exact match for actual skins
                    if self.is_exact_match(result_text, original_item_name, condition, formatted_name):
                        skin_matches.append((result, result_text))
                        logger.info(f"Found exact skin match: '{result_text}'")
                
                except Exception as e:
                    logger.debug(f"Error processing dropdown result {i+1}: {e}")
                    continue
            
            # Prefer skin matches over sticker matches
            if skin_matches:
                best_match, match_text = skin_matches[0]
                logger.info(f"Selecting skin match: '{match_text}'")
            elif sticker_matches and 'sticker' in original_item_name.lower():
                # Only use sticker if we're actually looking for a sticker
                best_match, match_text = sticker_matches[0]
                logger.info(f"Selecting sticker match: '{match_text}'")
            else:
                logger.warning("No exact match found in dropdown results")
                return False
            
            # Click the selected match
            try:
                # Scroll to the element and click it
                self.driver.execute_script("arguments[0].scrollIntoView(true);", best_match)
                time.sleep(0.3)  # Reduced wait time
                
                # Try regular click first
                try:
                    best_match.click()
                    logger.info("Clicked dropdown result with regular click")
                except:
                    # Try JavaScript click if regular click fails
                    self.driver.execute_script("arguments[0].click();", best_match)
                    logger.info("Clicked dropdown result with JavaScript click")
                
                # Reduced wait time for page to load
                time.sleep(2)
                return True
                
            except Exception as e:
                logger.error(f"Error clicking dropdown result: {e}")
                return False
                
        except Exception as e:
            logger.debug(f"Error in find_and_select_exact_match: {e}")
            return False
    
    def is_exact_match(self, result_text, original_item_name, condition, formatted_name):
        """
        Check if a dropdown result is an exact match for our search
        
        Args:
            result_text (str): Text from the dropdown result
            original_item_name (str): Original item name without condition
            condition (str): The condition we're looking for
            formatted_name (str): The full formatted search term
            
        Returns:
            bool: True if this is an exact match
        """
        try:
            result_lower = result_text.lower()
            original_lower = original_item_name.lower()
            
            # Exclude stickers unless we're specifically looking for one
            if 'sticker' in result_lower and 'sticker' not in original_lower:
                logger.debug(f"Excluding sticker result: '{result_text}'")
                return False
            
            # If we're looking for a sticker, make sure result is a sticker
            if 'sticker' in original_lower and 'sticker' not in result_lower:
                logger.debug(f"Looking for sticker but result is not a sticker: '{result_text}'")
                return False
            
            # Split the original item name to get weapon and skin name
            if '|' in original_item_name:
                weapon_part = original_item_name.split('|')[0].strip().lower()
                skin_part = original_item_name.split('|')[1].strip().lower()
            else:
                weapon_part = original_item_name.lower()
                skin_part = ""
            
            # Must contain the weapon part (unless it's a case)
            if not ('case' in weapon_part or weapon_part in result_lower):
                logger.debug(f"Weapon part '{weapon_part}' not found in result: '{result_text}'")
                return False
            
            # Must contain the skin part if it exists
            if skin_part and skin_part not in result_lower:
                # Try removing common words that might differ
                skin_cleaned = skin_part.replace('|', '').replace('-', ' ').strip()
                if skin_cleaned and skin_cleaned not in result_lower:
                    logger.debug(f"Skin part '{skin_part}' not found in result: '{result_text}'")
                    return False
            
            # If we have a condition, check for it
            if condition:
                condition_lower = condition.lower()
                
                # Map condition variations
                condition_mappings = {
                    'factory new': ['factory new', 'fn'],
                    'minimal wear': ['minimal wear', 'mw'],
                    'field-tested': ['field-tested', 'field tested', 'ft'],
                    'well-worn': ['well-worn', 'well worn', 'ww'],
                    'battle-scarred': ['battle-scarred', 'battle scarred', 'bs']
                }
                
                condition_found = False
                for full_condition, variations in condition_mappings.items():
                    if condition_lower in variations:
                        for variation in variations:
                            if variation in result_lower:
                                condition_found = True
                                break
                        if condition_found:
                            break
                
                if not condition_found:
                    logger.debug(f"Condition '{condition}' not found in result: '{result_text}'")
                    return False
            
            # Exclude Souvenir versions unless specifically requested
            if 'souvenir' in result_lower and 'souvenir' not in original_lower:
                logger.debug(f"Excluding Souvenir version: '{result_text}'")
                return False
            
            # Exclude StatTrak versions unless specifically requested
            if ('stattrak' in result_lower or 'stat-trak' in result_lower) and ('stattrak' not in original_lower and 'stat-trak' not in original_lower):
                logger.debug(f"Excluding StatTrak version: '{result_text}'")
                return False
            
            # Additional check: if we want StatTrak, make sure it's included
            if ('stattrak' in original_lower or 'stat-trak' in original_lower) and ('stattrak' not in result_lower and 'stat-trak' not in result_lower):
                logger.debug(f"Missing StatTrak in result: '{result_text}'")
                return False
            
            # Check for exact weapon type match for common confusions
            weapon_types = ['awp', 'ak-47', 'ump-45', 'm4a4', 'm4a1-s', 'glock-18', 'usp-s']
            for weapon_type in weapon_types:
                if weapon_type in original_lower:
                    if weapon_type not in result_lower:
                        logger.debug(f"Weapon type mismatch: looking for '{weapon_type}' but result is '{result_text}'")
                        return False
                    break
            
            logger.debug(f"Exact match found: '{result_text}' matches '{original_item_name}' with condition '{condition}'")
            return True
            
        except Exception as e:
            logger.debug(f"Error in is_exact_match: {e}")
            return False
    
    def format_item_name(self, item_name, condition=None):
        """Format item name according to CSGOStocks requirements (full names with conditions)"""
        formatted_name = item_name
        
        # Clean up common formatting issues
        formatted_name = formatted_name.replace('StatTrak™', 'StatTrak')
        formatted_name = formatted_name.replace('★', '')
        formatted_name = re.sub(r'\s+', ' ', formatted_name).strip()
        
        # If condition is provided and not already in the name, add it
        if condition and condition not in formatted_name:
            # Map short condition to full condition name
            full_condition = self.condition_mapping.get(condition, condition)
            formatted_name = f"{formatted_name} ({full_condition})"
        
        logger.debug(f"Formatted item name: '{item_name}' -> '{formatted_name}'")
        return formatted_name
    
    def search_item(self, item_name, condition=None):
        """
        Search for an item on CSGOStocks.de
        
        Args:
            item_name (str): Name of the CS2 item
            condition (str): Condition filter - optional
            
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
            
            # Format the item name with full details
            formatted_name = self.format_item_name(item_name, condition)
            logger.info(f"Searching for item: {formatted_name}")
            
            # Navigate to CSGOStocks main page if not already there
            current_url = self.driver.current_url
            if not current_url.startswith("https://csgostocks.de"):
                self.apply_human_like_delay()
                self.driver.get(self.base_url)
                
                # Wait for page to fully load
                wait = WebDriverWait(self.driver, 15)
                try:
                    # Wait for the search input to be present
                    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/app-root/navbar/nav/div[1]/input")))
                    time.sleep(1.5)  # Reduced time for JavaScript to load
                    logger.debug("Page loaded successfully")
                except TimeoutException:
                    logger.warning("Page did not load properly")
                    return None
                    
                # Handle cookie popup if present
                self.handle_cookie_popup()
            
            # Find the search input using the provided XPath
            try:
                search_input = self.driver.find_element(By.XPATH, "/html/body/app-root/navbar/nav/div[1]/input")
                logger.info("Found search input")
                
                # Make sure the input is interactable by scrolling to it
                self.driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
                time.sleep(0.5)
                
                # Try clicking on the input first to focus it
                try:
                    search_input.click()
                    time.sleep(0.2)
                except Exception as e:
                    logger.debug(f"Could not click search input: {e}")
                
                # Clear and type the search term
                search_input.clear()
                time.sleep(0.5)
                
                # Type the search term quickly but naturally
                search_input.send_keys(formatted_name)
                time.sleep(0.3)  # Brief pause after typing
                
                logger.info(f"Typed search query: {formatted_name}")
                
                # Wait for dropdown search results to appear
                time.sleep(1.2)  # Further reduced for speed
                
                # Look for dropdown search results and find exact match
                exact_match_found = self.find_and_select_exact_match(formatted_name, item_name, condition)
                
                if not exact_match_found:
                    # Fallback: Press Enter to search if no exact match found in dropdown
                    search_input.send_keys(Keys.ENTER)
                    logger.debug("No exact match in dropdown, pressed Enter to search")
                    
                    # Wait for search results to load
                    time.sleep(1.5)  # Reduced from 2 seconds for speed
                
                # Check if we're on a results page
                current_url = self.driver.current_url
                logger.debug(f"Current URL after search: {current_url}")
                
                # Try to extract price from the specified location
                return self.extract_price_from_page(item_name, condition, search_start_time)
                
            except NoSuchElementException:
                logger.error("Could not find search input")
                return None
            except Exception as e:
                logger.error(f"Error during search: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for item {item_name}: {e}")
            return None
    
    def extract_price_from_page(self, item_name, condition, search_start_time):
        """Extract price from the current page using the specified XPath"""
        try:
            # Wait a moment for the page to fully load
            time.sleep(1.5)  # Reduced from 2 seconds
            
            # Try to find the price element using the provided XPath
            price_xpath = "/html/body/app-root/app-chart/article/table/tr[3]/td[3]/a/span"
            
            try:
                price_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, price_xpath))
                )
                
                # Scroll to the price element to ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", price_element)
                time.sleep(1)  # Wait for scroll to complete
                
                price_text = price_element.text.strip()
                logger.debug(f"Found price text: '{price_text}'")
                
                if price_text:
                    price = self.parse_price(price_text)
                    
                    if price > 0:
                        # Try to get item name from page title or heading
                        try:
                            page_title = self.driver.title
                            found_name = page_title if page_title else item_name
                        except:
                            found_name = item_name
                        
                        result = {
                            'item_name': item_name,
                            'found_name': found_name,
                            'source': 'csgostocks.de',
                            'timestamp': time.time(),
                            'price': price,
                            'condition': condition,
                            'currency': 'EUR'  # Assuming EUR since it's a German site
                        }
                        
                        cache_key = f"{item_name}_{condition}"
                        self.search_cache[cache_key] = result
                        
                        search_end_time = time.time()
                        logger.info(f"TOTAL search time for {item_name}: {search_end_time - search_start_time:.2f} seconds")
                        logger.info(f"Found price for {item_name}: €{price}")
                        return result
                    else:
                        logger.warning(f"Could not parse price: '{price_text}'")
                        return None
                else:
                    logger.warning("Price element found but no text")
                    return None
                    
            except TimeoutException:
                logger.warning("Price element not found within timeout")
                
                # Try alternative price selectors as fallback
                alternative_selectors = [
                    # Different table row positions
                    "/html/body/app-root/app-chart/article/table/tr[2]/td[3]/a/span",
                    "/html/body/app-root/app-chart/article/table/tr[4]/td[3]/a/span",
                    "/html/body/app-root/app-chart/article/table/tr[1]/td[3]/a/span",
                    # Different table structures
                    "//table//tr//td[3]//span[contains(text(), '€')]",
                    "//table//tr//td[contains(@class, 'price')]//span",
                    # Generic price selectors
                    "//span[contains(@class, 'price')]",
                    "//td[contains(@class, 'price')]//span",
                    "//*[contains(text(), '€')]",
                    "//table//span[contains(text(), '€')]",
                    "//tr[3]//span",
                    # More specific paths for different layouts
                    "//app-chart//table//span[contains(text(), '€')]",
                    "//article//table//span[contains(text(), '€')]"
                ]
                
                for selector in alternative_selectors:
                    try:
                        price_elements = self.driver.find_elements(By.XPATH, selector)
                        logger.debug(f"Selector '{selector}' found {len(price_elements)} elements")
                        for elem in price_elements:
                            price_text = elem.text.strip()
                            logger.debug(f"Element text: '{price_text}'")
                            if '€' in price_text or '$' in price_text:
                                logger.debug(f"Found alternative price: '{price_text}'")
                                price = self.parse_price(price_text)
                                if price > 0:
                                    result = {
                                        'item_name': item_name,
                                        'found_name': item_name,
                                        'source': 'csgostocks.de',
                                        'timestamp': time.time(),
                                        'price': price,
                                        'condition': condition,
                                        'currency': 'EUR'
                                    }
                                    return result
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
                
                # If still no price found, let's debug the page structure
                logger.debug("=== DEBUG: Analyzing page structure ===")
                try:
                    # Check page title
                    page_title = self.driver.title
                    logger.debug(f"Page title: {page_title}")
                    
                    # Check current URL
                    current_url = self.driver.current_url
                    logger.debug(f"Current URL: {current_url}")
                    
                    # Look for any table elements
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    logger.debug(f"Found {len(tables)} table elements")
                    
                    # Look for any elements containing €
                    euro_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                    logger.debug(f"Found {len(euro_elements)} elements containing '€'")
                    for i, elem in enumerate(euro_elements[:5]):  # Show first 5
                        try:
                            text = elem.text.strip()
                            logger.debug(f"Euro element {i+1}: '{text}'")
                        except:
                            pass
                    
                    # Check if we're on the right page
                    if 'dragon lore' in page_title.lower() or 'redline' in page_title.lower():
                        logger.debug("✓ We seem to be on the correct item page")
                    else:
                        logger.warning(f"⚠ Page title doesn't match expected item: {page_title}")
                        
                except Exception as e:
                    logger.debug(f"Error in page structure debug: {e}")
                
                logger.warning("No price found with any selector")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting price from page: {e}")
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
            
            # Handle different decimal formats (German sites often use comma as decimal separator)
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
                # Only comma - likely decimal in European format
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
                    result = self.search_item(item_name, condition)
                    
                    if result:
                        results.append(result)
                    else:
                        # Add failed result
                        results.append({
                            'item_name': item_name,
                            'condition': condition,
                            'price': 0.0,
                            'currency': 'EUR',
                            'source': 'csgostocks.de',
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
                        'currency': 'EUR',
                        'source': 'csgostocks.de',
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
    with CSGOStocksScraper(headless=False) as scraper:
        # Test with the examples you provided
        test_items = [
            ("Lt. Commander Ricksaw | NSWC SEAL", None),
            ("StatTrak AK-47 | Redline", "Minimal Wear"),
            ("AK-47 | Redline", "Battle Scarred"),
            ("Spectrum Case", None)
        ]
        
        for item_name, condition in test_items:
            result = scraper.search_item(item_name, condition)
            if result:
                print(f"✅ Found price for {item_name}: €{result['price']}")
            else:
                print(f"❌ No price found for {item_name}")
            time.sleep(1)  # Small delay between tests

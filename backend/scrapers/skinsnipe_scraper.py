#!/usr/bin/env python3
"""
SkinSnipe.com Scraper - CS2 skin price aggregator
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SkinSnipeScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.base_url = "https://www.skinsnipe.com"
        self.session_active = False
        self.max_retries = 2
        self.search_cache = {}
        self.last_request_time = 0
        self.request_count = 0
        
        # Condition mapping for SkinSnipe (based on the variants you described)
        self.condition_mapping = {
            'Factory New': 'FN',
            'Minimal Wear': 'MW',
            'Field-Tested': 'FT', 
            'Well-Worn': 'WW',
            'Battle-Scarred': 'BS',
            'N/A': 'Standard'  # For items without conditions (cases, stickers, etc.)
        }
        
        # StatTrak mapping
        self.stattrak_mapping = {
            'Factory New': 'ST FN',
            'Minimal Wear': 'ST MW',
            'Field-Tested': 'ST FT',
            'Well-Worn': 'ST WW', 
            'Battle-Scarred': 'ST BS',
            'N/A': 'ST Standard'  # For StatTrak items without conditions
        }
        
        # Non-tradeable item patterns (items that don't have market prices)
        self.non_tradeable_patterns = [
            # Stock weapons (default CS2 guns)
            r'^(AK-47|M4A4|M4A1-S|AWP|Desert Eagle|Glock-18|USP-S|P2000)$',
            r'^(Galil AR|FAMAS|MP7|MP9|MAC-10|UMP-45|P90|PP-Bizon)$',
            r'^(Nova|XM1014|Sawed-Off|MAG-7|M249|Negev)$',
            r'^(Five-SeveN|Tec-9|CZ75-Auto|P250|Dual Berettas|R8 Revolver)$',
            r'^(SSG 08|G3SG1|SCAR-20|SG 553|AUG)$',
            # Coins and collectibles (broader patterns)
            r'.*coin.*',
            r'.*medal.*',
            r'.*trophy.*',
            r'.*pin.*',
            r'.*badge.*',
            r'.*collectible.*',
            # r'.*souvenir package.*',  # Removed: allow souvenir packages to be scraped
            r'.*commemorative.*',
            # Specific problematic items
            r'.*global offensive.*',
            r'.*service medal.*',
            r'.*rank.*badge.*',
            r'.*loyalty.*badge.*',
            r'.*years.*service.*',
            r'.*operation.*coin.*',
            # Default Music Kits (non-tradeable)
            r'^music kit.*valve.*cs.*go.*',
            r'^music kit.*valve.*counter.*strike.*',
            # Items with (N/A) condition - usually non-tradeable
            r'.*\(n/a\).*',
            r'.*\(not applicable\).*',
            # Other non-tradeable items
            # r'.*souvenir package.*',  # Removed duplicate
            r'.*viewer pass.*',
            r'.*operation.*pass.*',
            r'.*pick.*em.*challenge.*',
        ]
        
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
            
            logger.info(f"Chrome WebDriver initialized for SkinSnipe scraping")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False
    
    def apply_human_like_delay(self, min_delay=0.3, max_delay=1.0):
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
    
    def is_tradeable_item(self, item_name):
        """Check if an item is tradeable and has market value"""
        if not item_name:
            return False
            
        item_lower = item_name.lower().strip()
        
        # First check for tradeable items that might match non-tradeable patterns
        # Charms are tradeable (souvenir charms, team charms, etc.) - check before souvenir patterns
        if 'charm' in item_lower:
            return True

        # Music kits are tradeable (but exclude default Valve ones)
        if 'music kit' in item_lower:
            # Check if it's a default Valve music kit (non-tradeable)
            if ('valve' in item_lower and ('cs:go' in item_lower or 'counter-strike' in item_lower)):
                return False
            return True

        # If it contains a pipe "|", it's likely a skin and tradeable
        if '|' in item_name:
            return True

        # Cases are tradeable
        if 'case' in item_lower and 'key' not in item_lower:
            return True

        # Keys are tradeable
        if 'key' in item_lower:
            return True

        # Stickers are tradeable
        if 'sticker' in item_lower:
            return True

        # Graffiti is tradeable
        if 'graffiti' in item_lower or 'sealed graffiti' in item_lower:
            return True

        # Patches are tradeable
        if 'patch' in item_lower:
            return True

        # Agent skins are tradeable
        if 'agent' in item_lower or 'specialist' in item_lower:
            return True
        
        # Check against non-tradeable patterns
        for pattern in self.non_tradeable_patterns:
            if re.search(pattern, item_lower, re.IGNORECASE):
                logger.debug(f"Item '{item_name}' matches non-tradeable pattern: {pattern}")
                return False
        
        # Additional checks for stock weapons without skins
        # If it's just the base weapon name without a skin pattern
        base_weapons = [
            'ak-47', 'm4a4', 'm4a1-s', 'awp', 'desert eagle', 'glock-18', 
            'usp-s', 'p2000', 'galil ar', 'famas', 'mp7', 'mp9', 'mac-10',
            'ump-45', 'p90', 'pp-bizon', 'nova', 'xm1014', 'sawed-off',
            'mag-7', 'm249', 'negev', 'five-seven', 'tec-9', 'cz75-auto',
            'p250', 'dual berettas', 'r8 revolver', 'ssg 08', 'g3sg1',
            'scar-20', 'sg 553', 'aug'
        ]
        
        # Check if it's exactly a base weapon name (no skin)
        if item_lower in base_weapons:
            logger.debug(f"Item '{item_name}' is a stock weapon without skin")
            return False
        
        # If we can't determine, assume it's tradeable to be safe
        logger.debug(f"Unknown item type '{item_name}' - assuming tradeable")
        return True
    
    def format_item_name(self, item_name, condition=None):
        """Format item name for SkinSnipe search (just the base name without condition or StatTrak)"""
        formatted_name = item_name
        
        # Clean up common formatting issues
        formatted_name = formatted_name.replace('StatTrak™', 'StatTrak')
        formatted_name = formatted_name.replace('★', '')
        formatted_name = re.sub(r'\s+', ' ', formatted_name).strip()
        
        # Remove StatTrak from search query (but we'll remember it for variant selection)
        formatted_name = formatted_name.replace('StatTrak ', '').strip()
        formatted_name = formatted_name.replace('StatTrak', '').strip()
        
        # Remove condition from name if present (SkinSnipe handles conditions via variants)
        for condition_name in self.condition_mapping.keys():
            formatted_name = formatted_name.replace(f"({condition_name})", "").strip()
            formatted_name = formatted_name.replace(f" {condition_name}", "").strip()
        
        # For cases, try to be more specific to avoid keys
        if "case" in formatted_name.lower() and "key" not in formatted_name.lower():
            # Add "case" to the end if not already there to be more specific
            if not formatted_name.lower().endswith("case"):
                formatted_name = formatted_name + " case"
        
        logger.debug(f"Formatted item name: '{item_name}' -> '{formatted_name}'")
        return formatted_name
    
    def get_condition_variant_text(self, original_item_name, condition):
        """Get the expected variant text for a condition based on the ORIGINAL item name"""
        if not condition:
            return None
        # Check if StatTrak in the ORIGINAL item name (before formatting)
        # Only treat as StatTrak if the name starts with StatTrak, StatTrak™, or Stat-Trak (not just 'St')
        name_lc = original_item_name.strip().lower()
        is_stattrak = (
            name_lc.startswith('stattrak') or
            name_lc.startswith('stat-trak') or
            name_lc.startswith('stattrak™')
        )
        if is_stattrak:
            # Always use StatTrak mapping for StatTrak items
            variant_text = self.stattrak_mapping.get(condition, None)
            if not variant_text:
                # Try to match ignoring whitespace/case
                for k, v in self.stattrak_mapping.items():
                    if k.replace(' ', '').lower() == condition.replace(' ', '').lower():
                        variant_text = v
                        break
            if not variant_text:
                variant_text = f"ST {condition}"  # Fallback
        else:
            variant_text = self.condition_mapping.get(condition, None)
            if not variant_text:
                for k, v in self.condition_mapping.items():
                    if k.replace(' ', '').lower() == condition.replace(' ', '').lower():
                        variant_text = v
                        break
            if not variant_text:
                variant_text = condition
        logger.debug(f"Expected variant text for '{condition}' (StatTrak: {is_stattrak}) from original item '{original_item_name}': '{variant_text}'")
        return variant_text
    
    def search_item(self, item_name, condition=None, unique_id=None, force_fresh=False):
        """
        Search for an item on SkinSnipe.com
        
        Args:
            item_name (str): Name of the CS2 item
            condition (str): Condition filter - optional
            
        Returns:
            dict: Item data with price information
        """
        search_start_time = time.time()
        
        self.request_count += 1
        logger.info(f"Processing request #{self.request_count}: {item_name}")
        
        # Check if item is tradeable before attempting to scrape
        if not self.is_tradeable_item(item_name):
            logger.info(f"⏭️  Skipping non-tradeable item: {item_name}")
            return {
                'item_name': item_name,
                'found_name': item_name,
                'source': 'skinsnipe.com',
                'timestamp': time.time(),
                'price': 0.0,
                'condition': condition,
                'currency': 'USD',
                'error': 'Non-tradeable item (no market value)',
                'skipped': True
            }
        
        try:
            # Check cache first (allow bypass for batch mode or unique items)
            cache_key = f"{item_name}_{condition}"
            if unique_id is not None:
                cache_key += f"_{unique_id}"
            if not force_fresh and cache_key in self.search_cache:
                logger.info(f"Using cached result for: {item_name} (cache key: {cache_key})")
                return self.search_cache[cache_key]
            if not self.driver or not self.session_active:
                if not self.setup_driver():
                    logger.error("Failed to setup driver")
                    return None
            
            # Format the item name (no condition in search)
            formatted_name = self.format_item_name(item_name, condition)
            logger.info(f"Searching for item: {formatted_name}")
            
            # Navigate to SkinSnipe main page if not already there
            current_url = self.driver.current_url
            if not current_url.startswith("https://www.skinsnipe.com"):
                self.apply_human_like_delay()
                self.driver.get(self.base_url)
                
                # Wait for page to fully load
                wait = WebDriverWait(self.driver, 10)
                try:
                    # Wait for the search input to be present
                    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/app-root/app-header/header/div/div[1]/div[1]/input")))
                    time.sleep(1.5)  # Wait for JavaScript to load
                    logger.debug("Page loaded successfully")
                except TimeoutException:
                    logger.warning("Page did not load properly")
                    return None
            
            # Find the search input using the provided XPath
            try:
                search_input = self.driver.find_element(By.XPATH, "/html/body/app-root/app-header/header/div/div[1]/div[1]/input")
                logger.info("Found search input")
                
                # Make sure the input is interactable by scrolling to it
                self.driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
                time.sleep(0.5)
                
                # Clear and type the search term
                search_input.clear()
                time.sleep(0.3)
                search_input.send_keys(formatted_name)
                logger.info(f"Typed search query: {formatted_name}")                    # Wait for search suggestions to load
                time.sleep(1)
                
                # Wait for search results dropdown to appear
                try:
                    # Wait a bit for dropdown to populate
                    time.sleep(0.8)
                    
                    # Try to find search results dropdown
                    dropdown_selectors = [
                        "/html/body/app-root/app-header/header/div/div[1]/div[2]/div/div[2]/div/a",  # Your exact path
                        "/html/body/app-root/app-header/header/div/div[1]/div[2]//a",  # More flexible
                        "//app-header//div[contains(@class, 'dropdown')]//a",  # Generic dropdown
                        "//app-header//a[contains(@href, '/')]"  # Any link in header
                    ]
                    
                    first_result = None
                    for selector in dropdown_selectors:
                        try:
                            results = self.driver.find_elements(By.XPATH, selector)
                            if results:
                                first_result = results[0]
                                logger.info(f"Found {len(results)} search results with selector: {selector}")
                                break
                        except Exception as e:
                            logger.debug(f"Selector {selector} failed: {e}")
                            continue
                    
                    if not first_result:
                        logger.warning("No search results found in dropdown")
                        return {
                            'item_name': item_name,
                            'found_name': item_name,
                            'source': 'skinsnipe.com',
                            'timestamp': time.time(),
                            'price': 0.0,
                            'condition': condition,
                            'currency': 'USD',
                            'error': 'No search results found (likely non-tradeable)',
                            'skipped': True
                        }
                    
                    logger.info("Found first search result")
                    
                    # For cases, we need to be more careful about result selection
                    if "case" in item_name.lower():
                        logger.info(f"Case detected - checking results for: '{item_name}'")
                        
                        # If there's only one result, it's probably the right case
                        if len(results) == 1:
                            logger.info("Only one result found - likely the correct case, using it")
                            result_text = "Single case result"
                        else:
                            # Look through multiple results to find the best case match
                            best_result = None
                            best_result_text = ""
                            found_any_text = False
                            
                            for i, result in enumerate(results):
                                try:
                                    # Try multiple ways to get text from the result element
                                    result_text = ""
                                    if hasattr(result, 'text') and result.text:
                                        result_text = result.text.strip()
                                    
                                    # Try JavaScript to get text content
                                    if not result_text:
                                        try:
                                            result_text = self.driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", result).strip()
                                        except:
                                            pass
                                    
                                    # Try common attributes
                                    if not result_text:
                                        for attr in ['title', 'aria-label', 'data-title']:
                                            try:
                                                attr_text = result.get_attribute(attr)
                                                if attr_text:
                                                    result_text = attr_text.strip()
                                                    break
                                            except:
                                                continue
                                    
                                    logger.debug(f"Result {i+1}: '{result_text}'")
                                    
                                    if result_text:
                                        found_any_text = True
                                        result_lower = result_text.lower()
                                        
                                        # Check if this result is a case (not key)
                                        has_key = "key" in result_lower
                                        
                                        if not has_key:
                                            logger.info(f"✅ Found non-key result at position {i+1}: '{result_text}'")
                                            best_result = result
                                            best_result_text = result_text
                                            break
                                        else:
                                            logger.debug(f"Skipping key result: '{result_text}'")
                                            
                                except Exception as e:
                                    logger.debug(f"Error checking result {i+1}: {e}")
                                    continue
                            
                            if best_result:
                                first_result = best_result
                                result_text = best_result_text
                                logger.info(f"Selected case result: '{result_text}'")
                            elif not found_any_text:
                                # If we couldn't find any text in multiple results, use first
                                logger.info("No text found in results - using first result")
                                result_text = "First result (no text available)"
                            else:
                                logger.warning("Could not find any suitable case (non-key) results")
                                return None
                    else:
                        # For non-case items, use the first result as before
                        result_text = ""
                        
                        # Try multiple ways to get text from the result element
                        if hasattr(first_result, 'text') and first_result.text:
                            result_text = first_result.text.strip()
                        
                        # Try JavaScript to get text content if no text found
                        if not result_text:
                            try:
                                result_text = self.driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", first_result).strip()
                            except:
                                pass
                        
                        # Try common attributes if still no text
                        if not result_text:
                            for attr in ['title', 'aria-label', 'data-title']:
                                try:
                                    attr_text = first_result.get_attribute(attr)
                                    if attr_text:
                                        result_text = attr_text.strip()
                                        break
                                except:
                                    continue
                        
                        # Use fallback if still no text
                        if not result_text:
                            result_text = "No text available"
                        
                        logger.info(f"First result text: '{result_text}'")
                    
                    # Click the first result
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", first_result)
                    time.sleep(0.3)
                    
                    try:
                        first_result.click()
                        logger.info("Clicked first search result with regular click")
                    except:
                        # Try JavaScript click if regular click fails
                        self.driver.execute_script("arguments[0].click();", first_result)
                        logger.info("Clicked first search result with JavaScript click")
                    
                    # Wait for the item page to load
                    time.sleep(2)
                    
                    # Now handle condition selection and price extraction
                    return self.extract_price_from_page(item_name, condition, search_start_time)
                    
                except TimeoutException:
                    logger.warning("No search results found")
                    return {
                        'item_name': item_name,
                        'found_name': item_name,
                        'source': 'skinsnipe.com',
                        'timestamp': time.time(),
                        'price': 0.0,
                        'condition': condition,
                        'currency': 'USD',
                        'error': 'No search results found (likely non-tradeable)',
                        'skipped': True
                    }
                    
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
        """Extract price from the current page, handling condition variants if needed"""
        try:
            # Wait for page to load
            time.sleep(1.5)
            
            # Check if there are condition variants to choose from
            if condition:
                variant_selected = self.select_condition_variant(condition, item_name)  # Pass original item_name
                if not variant_selected:
                    logger.warning(f"Could not select condition variant for {condition}")
                    # Continue anyway, maybe it's a single-condition item
            
            # Extract price using the provided XPath
            price_xpath = "/html/body/app-root/div/app-compare/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[1]/div[3]/a"
            
            try:
                price_element = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, price_xpath))
                )
                
                # Scroll to the price element to ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", price_element)
                time.sleep(0.5)
                
                price_text = price_element.text.strip()
                logger.debug(f"Found price text: '{price_text}'")
                
                if price_text:
                    price = self.parse_price(price_text)
                    
                    if price > 0:
                        # Try to get item name from page
                        try:
                            page_title = self.driver.title
                            found_name = page_title if page_title else item_name
                        except:
                            found_name = item_name
                        
                        result = {
                            'item_name': item_name,
                            'found_name': found_name,
                            'source': 'skinsnipe.com',
                            'timestamp': time.time(),
                            'price': price,
                            'condition': condition,
                            'currency': 'USD'  # SkinSnipe shows prices in dollars
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
                    logger.warning("Price element found but no text")
                    return None
                    
            except TimeoutException:
                logger.warning("Price element not found within timeout")
                
                # Try alternative price selectors
                alternative_selectors = [
                    # Different positions in the table
                    "/html/body/app-root/div/app-compare/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[2]/div[3]/a",
                    "/html/body/app-root/div/app-compare/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[3]/a",
                    # Generic price selectors
                    "//a[contains(text(), '$')]",
                    "//div[contains(@class, 'price')]//a",
                    "//*[contains(text(), '$')]",
                    "//app-compare//a[contains(text(), '$')]"
                ]
                
                for selector in alternative_selectors:
                    try:
                        price_elements = self.driver.find_elements(By.XPATH, selector)
                        logger.debug(f"Selector '{selector}' found {len(price_elements)} elements")
                        for elem in price_elements:
                            price_text = elem.text.strip()
                            logger.debug(f"Element text: '{price_text}'")
                            if '$' in price_text:
                                logger.debug(f"Found alternative price: '{price_text}'")
                                price = self.parse_price(price_text)
                                if price > 0:
                                    result = {
                                        'item_name': item_name,
                                        'found_name': item_name,
                                        'source': 'skinsnipe.com',
                                        'timestamp': time.time(),
                                        'price': price,
                                        'condition': condition,
                                        'currency': 'USD'
                                    }
                                    return result
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
                
                logger.warning("No price found with any selector")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting price from page: {e}")
            return None
    
    def select_condition_variant(self, condition, original_item_name):
        """Select the appropriate condition variant from the variants box"""
        try:
            # Look for the variants container
            variants_xpath = "/html/body/app-root/div/app-compare/div[1]/div/div[3]"
            
            try:
                variants_container = self.driver.find_element(By.XPATH, variants_xpath)
                logger.info("Found variants container")
                
                # Get the expected variant text using the ORIGINAL item name for StatTrak detection
                expected_variant = self.get_condition_variant_text(original_item_name, condition)
                if not expected_variant:
                    logger.debug("No condition variant needed")
                    return True
                
                logger.info(f"Looking for variant: '{expected_variant}' for condition: '{condition}' (original item: '{original_item_name}')")
                
                # Find all variant links in the container
                variant_links = variants_container.find_elements(By.TAG_NAME, "a")
                logger.debug(f"Found {len(variant_links)} variant options")
                
                # Log all available variants for debugging
                logger.debug("Available variants:")
                for i, link in enumerate(variant_links):
                    try:
                        variant_text = link.text.strip()
                        logger.debug(f"  Variant {i+1}: '{variant_text}'")
                    except:
                        logger.debug(f"  Variant {i+1}: [Could not get text]")
                
                # Try to match variant links robustly: exact, case-insensitive, ignore whitespace, and with/without 'ST ' prefix
                def normalize(text):
                    return text.replace(' ', '').replace('™', '').replace('-', '').upper()

                norm_expected = normalize(expected_variant)
                candidates = []
                for i, link in enumerate(variant_links):
                    try:
                        variant_text = link.text.strip()
                        norm_variant = normalize(variant_text)
                        candidates.append((i, link, variant_text, norm_variant))
                    except Exception as e:
                        logger.debug(f"Error processing variant {i+1}: {e}")
                        continue

                # 1. Exact normalized match
                for i, link, variant_text, norm_variant in candidates:
                    if norm_variant == norm_expected:
                        logger.info(f"Found EXACT normalized match: '{variant_text}' == '{expected_variant}'")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", link)
                        time.sleep(0.5)
                        try:
                            link.click()
                            logger.info(f"✅ Successfully clicked exact variant: '{variant_text}'")
                            time.sleep(2)
                            return True
                        except Exception as click_e:
                            logger.debug(f"Regular click failed, trying JavaScript: {click_e}")
                            self.driver.execute_script("arguments[0].click();", link)
                            logger.info(f"✅ Successfully clicked exact variant with JS: '{variant_text}'")
                            time.sleep(1.5)
                            return True

                # 2. Partial normalized match
                for i, link, variant_text, norm_variant in candidates:
                    if norm_expected in norm_variant or norm_variant in norm_expected:
                        logger.info(f"Found PARTIAL normalized match: '{variant_text}' ~ '{expected_variant}'")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", link)
                        time.sleep(0.5)
                        try:
                            link.click()
                            logger.info(f"✅ Successfully clicked partial variant: '{variant_text}'")
                            time.sleep(2)
                            return True
                        except Exception as click_e:
                            logger.debug(f"Regular click failed, trying JavaScript: {click_e}")
                            self.driver.execute_script("arguments[0].click();", link)
                            logger.info(f"✅ Successfully clicked partial variant with JS: '{variant_text}'")
                            time.sleep(1.5)
                            return True

                logger.warning(f"❌ No matching variant found for condition: '{condition}' (expected: '{expected_variant}')")
                logger.warning("Available variants were:")
                for i, link, variant_text, _ in candidates:
                    logger.warning(f"  - '{variant_text}'")
                return False
                
            except NoSuchElementException:
                logger.debug("No variants container found - might be a single condition item")
                return True
                
        except Exception as e:
            logger.debug(f"Error selecting condition variant: {e}")
            return False
    
    def parse_price(self, price_text):
        """Parse price from text string (USD format)"""
        try:
            if not price_text or price_text.strip() == '' or price_text.strip() == '-':
                return 0.0
            
            logger.debug(f"Parsing price from text: '{price_text}'")
            
            # Handle multi-line prices - take the first price found
            lines = price_text.split('\n')
            for line in lines:
                line = line.strip()
                if '$' in line:
                    logger.debug(f"Using price line: '{line}'")
                    price_text = line
                    break
            
            # Remove currency symbols and clean the text
            cleaned_text = re.sub(r'[^\d.,]', '', price_text.strip())
            
            if not cleaned_text:
                return 0.0
            
            # Handle different decimal formats (USD typically uses period as decimal separator)
            if ',' in cleaned_text and '.' in cleaned_text:
                # Both comma and period present - likely US format: 1,234.56
                price_str = cleaned_text.replace(',', '')
            elif ',' in cleaned_text:
                # Only comma - likely thousands separator in USD
                price_str = cleaned_text.replace(',', '')
            elif '.' in cleaned_text:
                # Only period - likely decimal
                price_str = cleaned_text
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
        """Scrape prices for multiple items, allowing duplicate items to each get a price."""
        results = []
        skipped_count = 0
        try:
            if not self.setup_driver():
                logger.error("Failed to setup driver for batch processing")
                return results
            for i, item_data in enumerate(items_data):
                item_name = item_data.get('name', '')
                condition = item_data.get('condition', None)
                # Use index as unique_id to allow multiple identical items to each get a price
                unique_id = item_data.get('inventory_id', i)
                if not item_name:
                    continue
                try:
                    # Always force fresh scrape for each item in batch mode
                    result = self.search_item(item_name, condition, unique_id=unique_id, force_fresh=True)
                    if result:
                        results.append(result)
                        if result.get('skipped', False):
                            skipped_count += 1
                    else:
                        # Add failed result
                        results.append({
                            'item_name': item_name,
                            'condition': condition,
                            'price': 0.0,
                            'currency': 'USD',
                            'source': 'skinsnipe.com',
                            'timestamp': time.time(),
                            'error': 'No price found'
                        })
                    # Only delay between requests if we actually scraped (didn't skip)
                    if i < len(items_data) - 1 and not result.get('skipped', False):
                        self.apply_human_like_delay()
                except Exception as e:
                    logger.error(f"Error processing item {item_name}: {e}")
                    results.append({
                        'item_name': item_name,
                        'condition': condition,
                        'price': 0.0,
                        'currency': 'USD',
                        'source': 'skinsnipe.com',
                        'timestamp': time.time(),
                        'error': str(e)
                    })
                    continue
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
        finally:
            self.cleanup()
        if skipped_count > 0:
            logger.info(f"📊 Batch complete: {len(results)} total, {skipped_count} skipped (non-tradeable)")
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
    with SkinSnipeScraper(headless=False) as scraper:
        # Test with some example items
        test_items = [
            ("AK-47 | Redline", "Minimal Wear"),
            ("AWP | Dragon Lore", "Factory New"),
            ("Spectrum Case", None),  # No condition for case
            ("StatTrak AK-47 | Redline", "Field-Tested")
        ]
        
        for item_name, condition in test_items:
            result = scraper.search_item(item_name, condition)
            if result:
                print(f"✅ Found price for {item_name}: ${result['price']}")
            else:
                print(f"❌ No price found for {item_name}")
            time.sleep(2)  # Delay between tests

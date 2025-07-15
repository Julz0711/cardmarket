"""
CSGOSkins.gg Price Scraper
Scrapes current market prices for CS2 items from csgoskins.gg
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

class CSGOSkinsGGScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://csgoskins.gg/"
        self.session_active = False
        self.max_retries = 2
        self.search_cache = {}  # Cache search results
        
        # Condition mapping to array indices
        self.condition_indices = {
            'FN': 1,  # Factory New
            'MW': 2,  # Minimal Wear
            'FT': 3,  # Field-Tested
            'WW': 4,  # Well-Worn
            'BS': 5,  # Battle-Scarred
            'ST_FN': 6,  # StatTrak Factory New
            'ST_MW': 7,  # StatTrak Minimal Wear
            'ST_FT': 8,  # StatTrak Field-Tested
            'ST_WW': 9,  # StatTrak Well-Worn
            'ST_BS': 10, # StatTrak Battle-Scarred
            'SV_FN': 6,  # Souvenir Factory New (same indices as StatTrak)
            'SV_MW': 7,  # Souvenir Minimal Wear
            'SV_FT': 8,  # Souvenir Field-Tested
            'SV_WW': 9,  # Souvenir Well-Worn
            'SV_BS': 10  # Souvenir Battle-Scarred
        }
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with optimized options for speed"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Performance optimizations (keeping JavaScript enabled for compatibility)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-images")  # Don't load images
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--window-size=1280,720")  # Smaller window
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Disable loading of images for faster page loads (keep CSS for layout)
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(3)  # Reduced from 10 to 3 seconds
            self.session_active = True
            
            logger.info("Optimized Chrome WebDriver initialized successfully (JavaScript enabled)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False
    
    def search_item(self, item_name, condition=None, variant=None):
        """
        Search for an item on CSGOSkins.gg with optimized performance
        
        Args:
            item_name (str): Name of the CS2 item
            condition (str): Condition filter (FN, MW, FT, WW, BS)
            variant (str): Variant type (None, ST for StatTrak, SV for Souvenir)
            
        Returns:
            dict: Item data with price information for all conditions
        """
        try:
            # Check cache first
            cache_key = f"{item_name}_{condition}_{variant}"
            if cache_key in self.search_cache:
                logger.info(f"Using cached result for: {item_name}")
                return self.search_cache[cache_key]
            
            if not self.driver or not self.session_active:
                if not self.setup_driver():
                    return None
            
            logger.info(f"Searching for item: {item_name} (condition: {condition}, variant: {variant})")
            
            # Navigate to CSGOSkins.gg only if not already there
            current_url = self.driver.current_url
            if not current_url.startswith(self.base_url):
                self.driver.get(self.base_url)
                time.sleep(0.5)  # Reduced wait time
            
            # Find search input field with shorter wait
            search_input_xpath = "/html/body/nav/div/div[3]/form/div/input"
            
            try:
                wait = WebDriverWait(self.driver, 5)  # Reduced from 10 to 5 seconds
                search_input = wait.until(EC.presence_of_element_located((By.XPATH, search_input_xpath)))
                
                # Clear and enter item name
                search_input.clear()
                search_input.send_keys(item_name)
                time.sleep(0.3)  # Reduced wait for search suggestions
                
                # Determine which search result to click based on item type
                if self.detect_item_type(item_name) == 'case':
                    # For cases, take the 3rd result
                    result_xpath = "/html/body/nav/div/div[3]/form/div/ul/li[3]/a"
                    result_index = "3rd"
                else:
                    # For other items, take the 1st result
                    result_xpath = "/html/body/nav/div/div[3]/form/div/ul/li[1]/a"
                    result_index = "1st"
                
                # Click on the appropriate search result
                search_result = wait.until(EC.element_to_be_clickable((By.XPATH, result_xpath)))
                search_result.click()
                
                logger.info(f"Clicked on {result_index} search result for: {item_name}")
                
                # Shorter wait for page to load
                time.sleep(1)  # Reduced from 3 to 1 second
                
                # Detect item type to determine where to look for pricing
                item_type = self.detect_item_type(item_name)
                
                # Extract pricing information based on item type
                if item_type == 'weapon':
                    prices = self.extract_all_prices()
                else:
                    # For non-weapon items (agents, cases, stickers, etc.)
                    prices = self.extract_single_price()
                
                if prices:
                    result = {
                        'item_name': item_name,
                        'source': 'csgoskins.gg',
                        'timestamp': time.time(),
                        'item_type': item_type
                    }
                    
                    # Handle different price structures
                    if item_type == 'weapon' and 'price' not in prices:
                        # Multiple conditions for weapons
                        result['prices'] = prices
                        
                        # If specific condition and variant requested, return that price
                        if condition and variant:
                            key = f"{variant}_{condition}" if variant else condition
                            specific_price = prices.get(key, 0.0)
                            result['price'] = specific_price
                            result['condition'] = condition
                            result['variant'] = variant
                        elif condition:
                            specific_price = prices.get(condition, 0.0)
                            result['price'] = specific_price
                            result['condition'] = condition
                    else:
                        # Single price for non-weapon items
                        result['price'] = prices.get('price', 0.0)
                        result['currency'] = 'USD'
                    
                    # Cache the result
                    self.search_cache[cache_key] = result
                    
                    logger.info(f"Found prices for {item_name}: {prices}")
                    return result
                else:
                    logger.warning(f"Could not extract prices for {item_name}")
                    return None
                    
            except TimeoutException:
                logger.warning(f"Search failed for {item_name} - element not found")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for item {item_name}: {e}")
            return None
    
    def extract_all_prices(self):
        """
        Extract all available prices from the pricing summary
        
        Returns:
            dict: Dictionary with condition codes as keys and prices as values
        """
        prices = {}
        
        try:
            # Base xpath for the pricing summary
            summary_base_xpath = "/html/body/main/div[2]/div[1]/div[1]/div"
            
            # Extract prices for all conditions (1-10: FN, MW, FT, WW, BS, ST_FN, ST_MW, ST_FT, ST_WW, ST_BS)
            condition_names = ['', 'FN', 'MW', 'FT', 'WW', 'BS', 'ST_FN', 'ST_MW', 'ST_FT', 'ST_WW', 'ST_BS']
            
            for i in range(1, 11):  # Indices 1-10
                try:
                    # Try to get the price for this condition
                    if i <= 5:
                        # Regular conditions (FN-BS)
                        price_xpath = f"{summary_base_xpath}/a[{i}]/div/div[2]/span"
                    else:
                        # StatTrak/Souvenir conditions (ST_FN-ST_BS)
                        price_xpath = f"{summary_base_xpath}/a[{i}]/div/div[2]/span"
                    
                    price_element = self.driver.find_element(By.XPATH, price_xpath)
                    price_text = price_element.text.strip()
                    
                    # Extract price value
                    price = self.parse_price(price_text)
                    
                    if price > 0:
                        condition_name = condition_names[i]
                        prices[condition_name] = price
                        logger.debug(f"Found {condition_name}: ${price}")
                    
                except (NoSuchElementException, TimeoutException):
                    # This condition is not available for this item
                    continue
                except Exception as e:
                    logger.debug(f"Error extracting price for condition {i}: {e}")
                    continue
            
            return prices
            
        except Exception as e:
            logger.error(f"Error extracting all prices: {e}")
            return {}
    
    def extract_single_price(self):
        """
        Extract price for non-weapon items (agents, cases, stickers, etc.)
        
        Returns:
            dict: Dictionary with a single price
        """
        try:
            # Wait a bit for the page to fully load
            time.sleep(0.5)
            
            # Primary location you specified - this should be the main one
            primary_xpath = "/html/body/main/div[2]/div[2]/div[1]/div[3]/div[3]/div[2]/span"
            
            # Fallback XPaths in order of preference
            price_xpaths = [
                primary_xpath,  # Your specified primary location
                "/html/body/main/div[2]/div[2]/div[1]/div[3]/div[3]/div[2]",  # Parent div if span doesn't work
                "/html/body/main/div[2]/div[2]/div[1]/div[3]//span[contains(text(), '$')]",  # Any span with $ in the section
                "/html/body/main/div[2]/div[2]/div[1]/div[3]//div[contains(text(), '$')]",  # Any div with $ in the section
                "/html/body/main/div[2]/div[2]/div[1]/div[3]//*[contains(text(), '$')]",  # Any element with $ in the section
                "//span[contains(text(), '$') and not(contains(text(), 'Steam')) and not(contains(text(), 'Market'))]",  # Any $ text (not Steam Market)
            ]
            
            for i, xpath in enumerate(price_xpaths):
                try:
                    logger.debug(f"Trying XPath {i+1}/{len(price_xpaths)}: {xpath}")
                    
                    # Use explicit wait for the first (primary) xpath
                    if i == 0:
                        wait = WebDriverWait(self.driver, 3)
                        price_element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    else:
                        price_element = self.driver.find_element(By.XPATH, xpath)
                    
                    price_text = price_element.text.strip()
                    logger.debug(f"Found text: '{price_text}' with xpath {i+1}")
                    
                    # Extract price value
                    price = self.parse_price(price_text)
                    
                    if price > 0:
                        logger.info(f"Found single price: ${price} using xpath {i+1}: {xpath}")
                        return {'price': price}
                    else:
                        logger.debug(f"Could not parse price from text: '{price_text}'")
                        
                except TimeoutException:
                    logger.debug(f"Timeout waiting for xpath {i+1}: {xpath}")
                    continue
                except (NoSuchElementException):
                    logger.debug(f"Element not found for xpath {i+1}: {xpath}")
                    continue
                except Exception as e:
                    logger.debug(f"Error with xpath {i+1} ({xpath}): {e}")
                    continue
            
            # If we still haven't found a price, try to get page source for debugging
            logger.warning("Could not find single price with any xpath")
            try:
                # Log the relevant section of the page for debugging
                section_element = self.driver.find_element(By.XPATH, "/html/body/main/div[2]/div[2]/div[1]/div[3]")
                section_html = section_element.get_attribute('innerHTML')
                logger.debug(f"Section HTML: {section_html[:500]}...")  # First 500 chars
            except Exception as e:
                logger.debug(f"Could not get section HTML for debugging: {e}")
            
            return {}
            
        except Exception as e:
            logger.error(f"Error extracting single price: {e}")
            return {}
    
    def detect_item_type(self, item_name):
        """
        Detect the type of item to determine pricing structure
        
        Args:
            item_name (str): Name of the item
            
        Returns:
            str: 'weapon', 'case', or 'other'
        """
        item_lower = item_name.lower()
        
        # Check for cases first (special handling)
        case_indicators = [
            'case', 'weapon case', 'container', 'capsule', 'package',
            'box', 'collection package', 'souvenir package'
        ]
        
        for indicator in case_indicators:
            if indicator in item_lower:
                return 'case'
        
        # Items that typically have multiple conditions/wear levels
        weapon_indicators = ['|', 'knife', 'gloves', 'wraps']
        
        # Items that typically have single prices
        single_price_indicators = [
            'sticker', 'music kit', 'agent', 'charm',
            'patch', 'graffiti', 'key', 'pass', 'collectible', 'pin',
            'autograph', 'spray'
        ]
        
        # Check for single-price item types
        for indicator in single_price_indicators:
            if indicator in item_lower:
                return 'other'
        
        # Check for weapon indicators
        for indicator in weapon_indicators:
            if indicator in item_lower:
                return 'weapon'
        
        # Default to weapon type for items with conditions in parentheses
        if any(condition in item_name for condition in ['(Factory New)', '(Minimal Wear)', '(Field-Tested)', '(Well-Worn)', '(Battle-Scarred)']):
            return 'weapon'
        
        # Default to other for everything else
        return 'other'
    
    def parse_price(self, price_text):
        """
        Parse price from text string with improved handling
        
        Args:
            price_text (str): Raw price text from website
            
        Returns:
            float: Parsed price or 0.0 if parsing fails
        """
        try:
            if not price_text or price_text.strip() == '':
                return 0.0
            
            logger.debug(f"Parsing price from text: '{price_text}'")
            
            # Remove common currency symbols and clean the text
            cleaned_text = price_text.strip()
            
            # Handle different currency formats
            # $12.34, 12.34$, €12.34, 12,34€, etc.
            currency_patterns = [
                r'\$\s*(\d+(?:[.,]\d{1,2})?)',  # $12.34 or $12,34
                r'(\d+(?:[.,]\d{1,2})?)\s*\$',  # 12.34$ or 12,34$
                r'€\s*(\d+(?:[.,]\d{1,2})?)',  # €12.34
                r'(\d+(?:[.,]\d{1,2})?)\s*€',  # 12.34€
                r'(\d+(?:[.,]\d{1,2})?)',       # Just numbers: 12.34 or 12,34
            ]
            
            for pattern in currency_patterns:
                match = re.search(pattern, cleaned_text)
                if match:
                    price_str = match.group(1)
                    # Convert comma decimal separator to dot
                    price_str = price_str.replace(',', '.')
                    
                    try:
                        price = float(price_str)
                        logger.debug(f"Successfully parsed price: {price}")
                        return price
                    except ValueError:
                        continue
            
            # If no pattern matched, try to extract any number
            numbers = re.findall(r'\d+(?:[.,]\d{1,2})?', cleaned_text)
            if numbers:
                # Take the first number found
                price_str = numbers[0].replace(',', '.')
                try:
                    price = float(price_str)
                    logger.debug(f"Fallback parsed price: {price}")
                    return price
                except ValueError:
                    pass
            
            logger.debug(f"Could not parse any price from: '{price_text}'")
            return 0.0
                
        except Exception as e:
            logger.debug(f"Error parsing price '{price_text}': {e}")
            return 0.0
    
    def should_skip_item(self, item_name):
        """
        Check if an item should be skipped (coins, stock guns, etc.)
        
        Args:
            item_name (str): Name of the item
            
        Returns:
            bool: True if item should be skipped
        """
        item_lower = item_name.lower()
        
        # Expanded skip keywords - medals, coins, badges, etc.
        skip_keywords = [
            'coin', 'silver coin', 'gold coin', 'bronze coin',
            'medal', 'service medal', 'operation medal',
            'badge', 'operation badge', 'global offensive badge',
            'premier season', 'operation', 'season medal',
            '2025 service medal', 'austin 2025', 'major medal'
        ]
        
        # Check for skip keywords
        for keyword in skip_keywords:
            if keyword in item_lower:
                return True
        
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
            
            item_lower_clean = item_lower.strip()
            if item_lower_clean in base_weapons:
                return True
        
        return False
    
    def scrape_item_prices(self, items_data):
        """
        Scrape prices for multiple items with optimized batch processing
        
        Args:
            items_data (list): List of dicts with 'name' and optionally 'condition'
            
        Returns:
            list: List of price results
        """
        results = []
        
        try:
            # Setup driver once for the entire batch
            if not self.setup_driver():
                logger.error("Failed to setup driver for batch processing")
                return results
            
            # Group items by type to optimize processing order
            weapon_items = []
            other_items = []
            skipped_items = []
            
            for item_data in items_data:
                item_name = item_data.get('name', '')
                if not item_name:
                    continue
                
                # Skip items like coins, medals, stock guns, etc.
                if self.should_skip_item(item_name):
                    skipped_items.append(item_data)
                    continue
                
                # Group by item type for more efficient processing
                if self.detect_item_type(item_name) == 'weapon':
                    weapon_items.append(item_data)
                else:
                    other_items.append(item_data)
            
            # Process skipped items first (fastest)
            for item_data in skipped_items:
                item_name = item_data.get('name', '')
                condition = item_data.get('condition', None)
                
                logger.info(f"Skipping item: {item_name} (not suitable for pricing)")
                results.append({
                    'item_name': item_name,
                    'condition': condition,
                    'price': 0.0,
                    'currency': 'USD',
                    'source': 'csgoskins.gg',
                    'timestamp': time.time(),
                    'skipped': True,
                    'skip_reason': 'Item type not suitable for pricing'
                })
            
            # Process all valid items (weapons first, then others)
            all_valid_items = weapon_items + other_items
            
            for i, item_data in enumerate(all_valid_items):
                item_name = item_data.get('name', '')
                condition = item_data.get('condition', None)
                
                try:
                    # Clean item name for search
                    clean_name = self.clean_item_name(item_name)
                    
                    # Detect StatTrak or Souvenir variant
                    variant = self.detect_variant(item_name)
                    
                    result = self.search_item(clean_name, condition, variant)
                    if result:
                        results.append(result)
                        logger.info(f"Processed {i+1}/{len(all_valid_items)}: {item_name}")
                    
                    # Reduced delay between requests
                    if i < len(all_valid_items) - 1:  # Don't wait after the last item
                        time.sleep(0.5)  # Reduced from 2 to 0.5 seconds
                    
                except Exception as e:
                    logger.error(f"Error processing item {item_name}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
        finally:
            # Clean up driver after entire batch
            self.cleanup()
        
        return results
    
    def scrape_batch_optimized(self, items_data, batch_size=10):
        """
        Optimized batch processing for large item lists
        
        Args:
            items_data (list): List of items to process
            batch_size (int): Number of items to process per batch
            
        Returns:
            list: Combined results from all batches
        """
        if not items_data:
            return []
        
        all_results = []
        total_items = len(items_data)
        
        # Process items in batches to manage memory and connection stability
        for i in range(0, total_items, batch_size):
            batch = items_data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_items + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
            
            try:
                batch_results = self.scrape_item_prices(batch)
                all_results.extend(batch_results)
                
                # Brief pause between batches to avoid overwhelming the server
                if i + batch_size < total_items:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                continue
        
        logger.info(f"Completed processing {total_items} items in {total_batches} batches")
        return all_results

    def detect_variant(self, item_name):
        """
        Detect if item is StatTrak or Souvenir with improved detection
        
        Args:
            item_name (str): Item name
            
        Returns:
            str: 'ST' for StatTrak, 'SV' for Souvenir, None for regular
        """
        item_lower = item_name.lower()
        
        # Check for StatTrak variations
        stattrak_patterns = [
            'stattrak™', 'stattrak', 'stat-trak', 'stat trak', 'st '
        ]
        
        for pattern in stattrak_patterns:
            if pattern in item_lower:
                return 'ST'
        
        # Check for Souvenir
        if 'souvenir' in item_lower:
            return 'SV'
        
        return None
    
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
        
        # Don't remove StatTrak™ and Souvenir prefixes - keep them for accurate search
        # CSGOSkins.gg needs these to find the correct item
        # Only remove the ™ symbol which might cause search issues
        cleaned_name = cleaned_name.replace('StatTrak™', 'StatTrak')
        cleaned_name = cleaned_name.replace('★', '')  # Remove star symbol from knives/gloves
        
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
        """Close the WebDriver and clear session state"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.session_active = False
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
    
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
    # Example 1: Context manager for automatic cleanup
    with CSGOSkinsGGScraper(headless=True) as scraper:
        test_items = [
            {'name': 'AK-47 | Redline', 'condition': 'FT'},
            {'name': 'StatTrak™ AWP | Dragon Lore', 'condition': 'FN'},
            {'name': 'Lt. Commander Ricksaw | NSWC SEAL', 'condition': None},
            {'name': 'Dreams & Nightmares Case', 'condition': None},
        ]
        
        results = scraper.scrape_item_prices(test_items)
        
        for result in results:
            if result.get('skipped'):
                print(f"SKIPPED - {result['item_name']}: {result['skip_reason']}")
            else:
                print(f"Item: {result['item_name']} (Type: {result.get('item_type', 'unknown')})")
                if 'price' in result:
                    print(f"Price: ${result['price']}")
            print("---")
    
    # Example 2: Batch processing for large lists
    scraper = CSGOSkinsGGScraper(headless=True)
    
    large_item_list = [
        {'name': 'AK-47 | Redline', 'condition': 'FT'},
        {'name': 'StatTrak™ AWP | Dragon Lore', 'condition': 'FN'},
        {'name': 'Lt. Commander Ricksaw | NSWC SEAL', 'condition': None},
        {'name': 'Dreams & Nightmares Case', 'condition': None},
        {'name': 'Sticker | Team Liquid (Holo) | Stockholm 2021', 'condition': None},
        {'name': 'Music Kit | TWERL and Ekko & Sidetrack, Under Bright Lights', 'condition': None},
        {'name': 'Souvenir Charm | Austin 2025 Highlight | Catches Smoke', 'condition': None},
        # Add more items as needed...
    ]
    
    # Process in optimized batches
    results = scraper.scrape_batch_optimized(large_item_list, batch_size=5)
    
    print(f"\nProcessed {len(results)} items total")
    scraper.cleanup()

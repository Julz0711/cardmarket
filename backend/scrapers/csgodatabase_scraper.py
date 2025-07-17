#!/usr/bin/env python3
"""
CSGODatabase.com Scraper - 3rd party marketplace price aggregator
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

class CSGODatabaseScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.base_url = "https://www.csgodatabase.com/"
        self.session_active = False
        self.max_retries = 2
        self.search_cache = {}
        self.last_request_time = 0
        self.request_count = 0
        
        # Condition mapping for CSGODatabase
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
            
            logger.info(f"Chrome WebDriver initialized for CSGODatabase scraping")
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
        Search for an item on CSGODatabase.com
        
        Args:
            item_name (str): Name of the CS2 item
            condition (str): Condition filter (FN, MW, FT, WW, BS) - optional
            
        Returns:
            dict: Item data with price information for all conditions
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
            
            # Check if this is an agent - handle separately
            if self.is_agent_item(item_name):
                return self.search_agent(item_name, condition, search_start_time)
            
            # Navigate to CSGODatabase if not already there
            current_url = self.driver.current_url
            if not current_url.startswith(self.base_url):
                self.apply_human_like_delay()
                self.driver.get(self.base_url)
                time.sleep(2)
            
            # Find search input field
            search_input_xpath = "/html/body/header/nav/div/form/div/input"
            
            try:
                wait = WebDriverWait(self.driver, 10)
                search_input = wait.until(EC.presence_of_element_located((By.XPATH, search_input_xpath)))
                
                # Clear and enter item name
                search_input.clear()
                search_input.send_keys(item_name)
                
                # Human-like typing delay
                time.sleep(random.uniform(0.2, 0.5))
                
                # Hit Enter (no dropdown suggestions)
                search_input.send_keys(Keys.RETURN)
                logger.info(f"Submitted search for: {item_name}")
                
                # Wait for search results page to load
                time.sleep(2)
                
                # Click on first result
                first_result_xpath = "/html/body/main/article/section/div/div[2]/div/div"
                
                try:
                    first_result = wait.until(EC.element_to_be_clickable((By.XPATH, first_result_xpath)))
                    first_result.click()
                    logger.info("Clicked on first search result")
                    
                    # Wait for item page to load
                    time.sleep(2)
                    
                    # Determine item type and extract pricing accordingly
                    if self.is_case_item(item_name):
                        prices = self.extract_case_price()
                    else:
                        prices = self.extract_prices_from_table()
                    
                    if prices:
                        result = {
                            'item_name': item_name,
                            'source': 'csgodatabase.com',
                            'timestamp': time.time(),
                            'prices': prices
                        }
                        
                        # If specific condition requested, return that price
                        if condition and condition in prices:
                            result['price'] = prices[condition]
                            result['condition'] = condition
                        
                        # Cache the result
                        self.search_cache[cache_key] = result
                        
                        search_end_time = time.time()
                        logger.info(f"TOTAL search time for {item_name}: {search_end_time - search_start_time:.2f} seconds")
                        logger.info(f"Found prices for {item_name}: {prices}")
                        return result
                    else:
                        logger.warning(f"Could not extract prices for {item_name}")
                        return None
                        
                except TimeoutException:
                    logger.warning(f"Could not click first result for {item_name}")
                    return None
                    
            except TimeoutException:
                logger.warning(f"Search input not found for {item_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for item {item_name}: {e}")
            return None
    
    def extract_prices_from_table(self):
        """
        Extract all condition prices from the CSGODatabase pricing table
        
        Returns:
            dict: Dictionary with condition codes as keys and prices as values
        """
        prices = {}
        
        try:
            # Wait for table to load
            time.sleep(1)
            
            # Base table xpath
            table_xpath = "/html/body/main/article/section/div[4]/div[1]/table"
            
            try:
                table = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, table_xpath))
                )
                
                # Get header row to identify condition columns
                header_xpath = "/html/body/main/article/section/div[4]/div[1]/table/thead/tr"
                header_row = table.find_element(By.XPATH, header_xpath)
                header_cells = header_row.find_elements(By.TAG_NAME, "th")
                
                # Map column indices to conditions by reading actual header text
                condition_columns = {}
                
                logger.debug(f"Found {len(header_cells)} header columns")
                
                # Check if this is a single condition item (small table)
                if len(header_cells) <= 3:  # Marketplace + 1-2 conditions
                    logger.info("Detected single condition item - using first column")
                    # For single condition items, always take the first price column (index 1)
                    if len(header_cells) >= 2:
                        condition_text = header_cells[1].text.strip()
                        logger.debug(f"Single condition header: '{condition_text}'")
                        
                        # Determine condition type
                        if 'StatTrak' in condition_text or condition_text.startswith('ST '):
                            condition_code = self.map_stattrak_condition(condition_text)
                        else:
                            condition_code = self.map_regular_condition(condition_text)
                        
                        if condition_code:
                            condition_columns[1] = condition_code
                            logger.debug(f"Single condition mapped to: {condition_code}")
                else:
                    # Regular multi-condition table handling
                    for i, cell in enumerate(header_cells):
                        if i == 0:  # Skip first column (marketplace names)
                            continue
                        
                        condition_text = cell.text.strip()
                        logger.debug(f"Header column {i}: '{condition_text}'")
                        
                        # Determine if this is StatTrak or regular based on header text
                        if 'StatTrak' in condition_text or condition_text.startswith('ST '):
                            # This is a StatTrak column
                            condition_code = self.map_stattrak_condition(condition_text)
                        else:
                            # This is a regular condition column
                            condition_code = self.map_regular_condition(condition_text)
                        
                        if condition_code:
                            condition_columns[i] = condition_code
                            logger.debug(f"Mapped column {i} to condition: {condition_code}")
                
                # Extract Skinport prices (row 3, index 2)
                skinport_row_xpath = "/html/body/main/article/section/div[4]/div[1]/table/tbody/tr[2]"
                
                try:
                    skinport_row = table.find_element(By.XPATH, skinport_row_xpath)
                    price_cells = skinport_row.find_elements(By.TAG_NAME, "td")
                    
                    # Extract prices for each condition
                    for col_index, condition_code in condition_columns.items():
                        if col_index < len(price_cells):
                            try:
                                price_cell = price_cells[col_index]
                                
                                # Look for price link or text
                                price_text = ""
                                try:
                                    price_link = price_cell.find_element(By.TAG_NAME, "a")
                                    price_text = price_link.text.strip()
                                except NoSuchElementException:
                                    price_text = price_cell.text.strip()
                                
                                if price_text and price_text != "-":
                                    price = self.parse_price(price_text)
                                    if price > 0:
                                        prices[condition_code] = price
                                        logger.debug(f"Found {condition_code}: ${price}")
                                
                            except Exception as e:
                                logger.debug(f"Error extracting price for {condition_code}: {e}")
                                continue
                    
                except NoSuchElementException:
                    logger.warning("Skinport row not found in table")
                
            except TimeoutException:
                logger.warning("Pricing table not found")
                return {}
            
            return prices
            
        except Exception as e:
            logger.error(f"Error extracting prices from table: {e}")
            return {}
    
    def is_agent_item(self, item_name):
        """Check if item is an agent"""
        agent_keywords = [
            'lieutenant', 'commander', 'officer', 'specialist', 'seal', 'swat', 
            'fbi', 'gign', 'gsg-9', 'sas', 'agent', 'elite crew'
        ]
        item_lower = item_name.lower()
        return any(keyword in item_lower for keyword in agent_keywords)
    
    def is_case_item(self, item_name):
        """Check if item is a case"""
        case_keywords = [
            'case', 'weapon case', 'container', 'capsule', 'package',
            'collection package', 'souvenir package'
        ]
        item_lower = item_name.lower()
        return any(keyword in item_lower for keyword in case_keywords)
    
    def extract_case_price(self):
        """
        Extract price for case items from the specific case price location
        
        Returns:
            dict: Dictionary with case price
        """
        try:
            # Wait for case page to load
            time.sleep(1)
            
            # Case price location
            case_price_xpath = "/html/body/main/article/section/div[2]/div/div/div[2]/a"
            
            try:
                price_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, case_price_xpath))
                )
                
                price_text = price_element.text.strip()
                logger.debug(f"Found case price text: '{price_text}'")
                
                # Special handling for case prices (they might be in different format)
                price = self.parse_case_price(price_text)
                
                if price > 0:
                    logger.info(f"Found case price: ${price}")
                    return {'case': price}  # Use 'case' as the condition key
                else:
                    logger.warning(f"Could not parse case price from: '{price_text}'")
                    return {}
                    
            except TimeoutException:
                logger.warning("Case price element not found")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting case price: {e}")
            return {}
    
    def search_agent(self, item_name, condition, search_start_time):
        """
        Search for agent items on the dedicated agents page
        
        Args:
            item_name (str): Agent name
            condition (str): Condition (optional, agents usually don't have conditions)
            search_start_time (float): Start time for performance tracking
            
        Returns:
            dict: Agent price data
        """
        try:
            logger.info(f"Searching for agent: {item_name}")
            
            # Navigate to agents page
            agents_url = "https://www.csgodatabase.com/agents/"
            self.driver.get(agents_url)
            time.sleep(2)
            
            # Scroll down to load more agents (they are lazy loaded)
            logger.debug("Scrolling to load all agents...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Calculate new scroll height and compare with last height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            logger.debug("Finished loading all agents")
            
            # Find all agent boxes after scrolling
            agent_container_xpath = "/html/body/main/article/section/div/div[2]"
            
            try:
                # Wait for agent container to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, agent_container_xpath))
                )
                
                # Get all agent divs within the container
                agent_boxes = self.driver.find_elements(By.XPATH, f"{agent_container_xpath}/div")
                logger.debug(f"Found {len(agent_boxes)} agent boxes after scrolling")
                
                # Search for matching agent name
                for i, box in enumerate(agent_boxes, 1):
                    try:
                        # Get agent name from the h3/a/span structure
                        name_elements = box.find_elements(By.XPATH, ".//h3/a/span[2]")
                        
                        if name_elements:
                            agent_name = name_elements[0].text.strip()
                            logger.debug(f"Agent {i}: '{agent_name}'")
                            
                            # Check if this matches our search
                            if self.agent_names_match(item_name, agent_name):
                                logger.info(f"Found matching agent: '{agent_name}'")
                                
                                # Click on the agent box
                                agent_box = box.find_element(By.XPATH, ".//div")
                                
                                # Scroll to the agent to make sure it's visible
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", agent_box)
                                time.sleep(0.5)
                                
                                agent_box.click()
                                
                                # Wait for agent page to load
                                time.sleep(2)
                                
                                # Extract agent price (they usually have single prices)
                                prices = self.extract_prices_from_table()
                                
                                if prices:
                                    result = {
                                        'item_name': item_name,
                                        'source': 'csgodatabase.com',
                                        'timestamp': time.time(),
                                        'prices': prices,
                                        'item_type': 'agent'
                                    }
                                    
                                    # Cache the result
                                    cache_key = f"{item_name}_{condition}"
                                    self.search_cache[cache_key] = result
                                    
                                    search_end_time = time.time()
                                    logger.info(f"TOTAL agent search time: {search_end_time - search_start_time:.2f} seconds")
                                    logger.info(f"Found agent prices: {prices}")
                                    return result
                                else:
                                    logger.warning(f"Could not extract prices for agent: {agent_name}")
                                    return None
                    
                    except Exception as e:
                        logger.debug(f"Error checking agent box {i}: {e}")
                        continue
                
                logger.warning(f"No matching agent found for: {item_name}")
                return None
                
            except TimeoutException:
                logger.warning("Agent container not found on agents page")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for agent {item_name}: {e}")
            return None
    
    def parse_case_price(self, price_text):
        """
        Parse case price with special handling for different formats
        
        Args:
            price_text (str): Raw price text from case page
            
        Returns:
            float: Parsed price or 0.0 if parsing fails
        """
        try:
            if not price_text or price_text.strip() == '' or price_text.strip() == '-':
                return 0.0
            
            logger.debug(f"Parsing case price from text: '{price_text}'")
            
            # Extract price using regex - look for price patterns
            price_pattern = r'\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)'
            matches = re.findall(price_pattern, price_text)
            
            if matches:
                price_text_clean = matches[0]  # Take the first price found
                logger.debug(f"Extracted price pattern: '{price_text_clean}'")
                
                # Handle different decimal formats
                if ',' in price_text_clean and '.' in price_text_clean:
                    # Both comma and period present
                    comma_pos = price_text_clean.rfind(',')
                    dot_pos = price_text_clean.rfind('.')
                    
                    if comma_pos > dot_pos:
                        # European format: 1.234,56
                        price_str = price_text_clean.replace('.', '').replace(',', '.')
                    else:
                        # US format: 1,234.56
                        price_str = price_text_clean.replace(',', '')
                elif ',' in price_text_clean:
                    # Only comma - check if it's decimal separator
                    parts = price_text_clean.split(',')
                    if len(parts) == 2 and len(parts[1]) <= 2:
                        # Decimal separator
                        price_str = price_text_clean.replace(',', '.')
                    else:
                        # Thousands separator
                        price_str = price_text_clean.replace(',', '')
                elif '.' in price_text_clean:
                    # Only period - check if it's decimal separator
                    parts = price_text_clean.split('.')
                    if len(parts) == 2 and len(parts[1]) <= 2 and len(parts[0]) <= 3:
                        # Decimal separator (and first part not too long)
                        price_str = price_text_clean
                    else:
                        # Thousands separator
                        price_str = price_text_clean.replace('.', '')
                else:
                    # No separators
                    price_str = price_text_clean
                
                try:
                    price = float(price_str)
                    logger.debug(f"Successfully parsed case price: {price}")
                    return price
                except ValueError:
                    logger.debug(f"Could not convert case price to float: '{price_str}'")
                    return 0.0
            else:
                logger.debug(f"No price pattern found in: '{price_text}'")
                return 0.0
                
        except Exception as e:
            logger.debug(f"Error parsing case price '{price_text}': {e}")
            return 0.0
    
    def agent_names_match(self, search_name, agent_name):
        """
        Check if agent names match (fuzzy matching for agent names)
        
        Args:
            search_name (str): Name being searched for
            agent_name (str): Name found on the page
            
        Returns:
            bool: True if names match
        """
        # Clean both names for comparison
        search_clean = re.sub(r'[^\w\s]', '', search_name.lower()).strip()
        agent_clean = re.sub(r'[^\w\s]', '', agent_name.lower()).strip()
        
        # Exact match
        if search_clean == agent_clean:
            return True
        
        # Check if key words match (for names like "Lt. Commander Ricksaw")
        search_words = search_clean.split()
        agent_words = agent_clean.split()
        
        # If most significant words match
        common_words = set(search_words) & set(agent_words)
        if len(common_words) >= min(2, len(search_words) - 1):  # At least 2 words or all but one
            return True
        
        # Check if search name is contained in agent name or vice versa
        if search_clean in agent_clean or agent_clean in search_clean:
            return True
        
        return False
    
    def map_condition_name(self, condition_text):
        """
        Map condition name from CSGODatabase to our standard codes
        
        Args:
            condition_text (str): Condition name from website
            
        Returns:
            str: Standard condition code or None
        """
        condition_text = condition_text.strip()
        
        # Direct mapping
        if condition_text in self.condition_mapping:
            return self.condition_mapping[condition_text]
        
        # Partial matching
        text_lower = condition_text.lower()
        if 'factory new' in text_lower or 'fn' in text_lower:
            return 'FN'
        elif 'minimal wear' in text_lower or 'mw' in text_lower:
            return 'MW'
        elif 'field-tested' in text_lower or 'ft' in text_lower:
            return 'FT'
        elif 'well-worn' in text_lower or 'ww' in text_lower:
            return 'WW'
        elif 'battle-scarred' in text_lower or 'bs' in text_lower:
            return 'BS'
        
        return None
    
    def map_stattrak_condition(self, condition_text):
        """
        Map StatTrak condition name to our standard codes
        
        Args:
            condition_text (str): StatTrak condition name from website
            
        Returns:
            str: StatTrak condition code or None
        """
        text_lower = condition_text.lower()
        
        if 'factory new' in text_lower or 'fn' in text_lower:
            return 'ST_FN'
        elif 'minimal wear' in text_lower or 'mw' in text_lower:
            return 'ST_MW'
        elif 'field-tested' in text_lower or 'ft' in text_lower:
            return 'ST_FT'
        elif 'well-worn' in text_lower or 'ww' in text_lower:
            return 'ST_WW'
        elif 'battle-scarred' in text_lower or 'bs' in text_lower:
            return 'ST_BS'
        
        return None
    
    def map_regular_condition(self, condition_text):
        """
        Map regular condition name to our standard codes
        
        Args:
            condition_text (str): Regular condition name from website
            
        Returns:
            str: Regular condition code or None
        """
        text_lower = condition_text.lower()
        
        if 'factory new' in text_lower or 'fn' in text_lower:
            return 'FN'
        elif 'minimal wear' in text_lower or 'mw' in text_lower:
            return 'MW'
        elif 'field-tested' in text_lower or 'ft' in text_lower:
            return 'FT'
        elif 'well-worn' in text_lower or 'ww' in text_lower:
            return 'WW'
        elif 'battle-scarred' in text_lower or 'bs' in text_lower:
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
                            'source': 'csgodatabase.com',
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
                        'source': 'csgodatabase.com',
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
    with CSGODatabaseScraper(headless=False) as scraper:
        result = scraper.search_item("AK-47 | Redline")
        if result:
            print(f"Found prices: {result}")
        else:
            print("No results found")

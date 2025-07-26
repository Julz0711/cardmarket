"""
Improved CSFloat Scraper for retrieving float values and paint seeds
Fixed version with better selectors, timing, and error handling
"""

import logging
import time
import re
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

# Try to import webdriver_manager, fallback if not available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FloatData:
    float_value: Optional[float]
    paint_seed: Optional[int]
    inspect_link: Optional[str]
    weapon_name: Optional[str] = None
    skin_name: Optional[str] = None
    wear_rating: Optional[str] = None
    success: bool = False
    error: Optional[str] = None

class ImprovedCSFloatScraper:
    """Improved CSFloat scraper with better reliability"""
    
    def __init__(self, headless: bool = True):
        self.driver = None
        self.headless = headless
        self.base_url = "https://csfloat.com/"
        self.logger = logger
        
        self._setup_driver()
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with improved options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')  # Use new headless mode
        
        # Essential options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Better user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Performance optimizations (but keep JavaScript enabled!)
        prefs = {
            "profile.default_content_setting_values": {
                "images": 1,  # Allow images (they might be needed for proper rendering)
                "plugins": 2,
                "popups": 2,
                "geolocation": 2,
                "notifications": 2,
                "media_stream": 2,
            },
            "profile.managed_default_content_settings": {
                "images": 1
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Suppress logging
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        
        try:
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = Service(ChromeDriverManager().install())
            else:
                service = Service()
            
            service.log_path = 'NUL' if os.name == 'nt' else '/dev/null'
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            self.logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Chrome WebDriver: {e}")
    
    def get_float_data(self, inspect_link: str) -> FloatData:
        """
        Get float value and paint seed for a CS2 item from CSFloat
        """
        if not inspect_link or 'steam://' not in inspect_link:
            return FloatData(
                float_value=None,
                paint_seed=None,
                inspect_link=inspect_link,
                success=False,
                error="Invalid inspect link format"
            )
        
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_retries}: Getting float data")
                
                # Navigate to CSFloat
                self.driver.get(self.base_url)
                
                # Wait for page to load completely
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Additional wait for Angular/React to initialize
                time.sleep(3)
                
                # Try multiple strategies to find the input field
                input_element = self._find_input_field()
                if not input_element:
                    if attempt < max_retries - 1:
                        self.logger.warning("Input field not found, retrying...")
                        time.sleep(5)
                        continue
                    else:
                        raise Exception("Could not find input field")
                
                # Clear and enter the inspect link
                self._clear_and_input(input_element, inspect_link)
                
                # Find and click the search/lookup button
                if not self._click_search_button():
                    if attempt < max_retries - 1:
                        self.logger.warning("Search button not found, retrying...")
                        time.sleep(5)
                        continue
                    else:
                        raise Exception("Could not find or click search button")
                
                # Wait for results with progressive timeout
                if not self._wait_for_results():
                    if attempt < max_retries - 1:
                        self.logger.warning("Results not loaded, retrying...")
                        time.sleep(5)
                        continue
                    else:
                        raise Exception("Results did not load")
                
                # Extract data
                float_value = self._extract_float_value()
                paint_seed = self._extract_paint_seed()
                weapon_info = self._extract_weapon_info()
                
                if float_value is not None or paint_seed is not None:
                    self.logger.info(f"Successfully extracted - Float: {float_value}, Paint Seed: {paint_seed}")
                    return FloatData(
                        float_value=float_value,
                        paint_seed=paint_seed,
                        inspect_link=inspect_link,
                        weapon_name=weapon_info.get('weapon_name'),
                        skin_name=weapon_info.get('skin_name'),
                        wear_rating=weapon_info.get('wear_rating'),
                        success=True
                    )
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning("No data extracted, retrying...")
                        time.sleep(5)
                        continue
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
        
        return FloatData(
            float_value=None,
            paint_seed=None,
            inspect_link=inspect_link,
            success=False,
            error="Failed after all retries"
        )
    
    def _find_input_field(self):
        """Find the input field using multiple strategies"""
        selectors = [
            # Common input selectors
            "input[type='text']",
            "input[placeholder*='inspect']",
            "input[placeholder*='Inspect']",
            "input[placeholder*='link']",
            "input[placeholder*='Link']",
            # By class names that might be used
            ".form-control",
            ".input",
            ".search-input",
            # Angular Material selectors
            "mat-form-field input",
            ".mat-input-element",
            # Generic input that's visible
            "input:not([type='hidden']):not([type='submit']):not([type='button'])"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        self.logger.info(f"Found input with selector: {selector}")
                        return element
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return None
    
    def _clear_and_input(self, element, text):
        """Clear input field and enter text with retry logic"""
        for i in range(3):
            try:
                # Clear the field multiple ways
                element.clear()
                time.sleep(0.5)
                element.send_keys(Keys.CONTROL + "a")
                time.sleep(0.2)
                element.send_keys(Keys.DELETE)
                time.sleep(0.5)
                
                # Enter the text
                element.send_keys(text)
                time.sleep(1)
                
                # Verify text was entered
                current_value = element.get_attribute('value')
                if inspect_link in current_value:
                    self.logger.info("Successfully entered inspect link")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Input attempt {i+1} failed: {e}")
                time.sleep(1)
        
        return False
    
    def _click_search_button(self):
        """Find and click the search button"""
        selectors = [
            # Text-based selectors
            "button:contains('Search')",
            "button:contains('Lookup')",
            "button:contains('Check')",
            # Type-based selectors
            "button[type='submit']",
            "input[type='submit']",
            # Class-based selectors
            ".btn-primary",
            ".search-btn",
            ".lookup-btn",
            # Material Design
            ".mat-raised-button",
            ".mat-button",
            # Generic button near input
            "form button",
            ".form button"
        ]
        
        # First try text-based search with XPath
        xpath_selectors = [
            "//button[contains(text(), 'Search') or contains(text(), 'Lookup') or contains(text(), 'Check') or contains(text(), 'Submit')]",
            "//input[@type='submit']",
            "//button[@type='submit']"
        ]
        
        for selector in xpath_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        self.logger.info(f"Clicked button with XPath: {selector}")
                        time.sleep(2)
                        return True
            except Exception as e:
                self.logger.debug(f"XPath selector {selector} failed: {e}")
        
        # Try CSS selectors
        for selector in selectors:
            try:
                if selector.startswith("button:contains"):
                    continue  # Skip jQuery-style selectors in Selenium
                    
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        self.logger.info(f"Clicked button with CSS: {selector}")
                        time.sleep(2)
                        return True
            except Exception as e:
                self.logger.debug(f"CSS selector {selector} failed: {e}")
        
        # Last resort: try pressing Enter on the input field
        try:
            input_element = self._find_input_field()
            if input_element:
                input_element.send_keys(Keys.ENTER)
                self.logger.info("Pressed Enter on input field")
                time.sleep(2)
                return True
        except Exception as e:
            self.logger.debug(f"Enter key press failed: {e}")
        
        return False
    
    def _wait_for_results(self):
        """Wait for results to appear"""
        # Wait for any indication that results are loading or loaded
        result_indicators = [
            # Loading indicators
            ".loading",
            ".spinner",
            ".mat-spinner",
            # Result containers
            ".result",
            ".item-result",
            ".weapon-info",
            ".float-info",
            # Specific elements that appear in results
            "*[class*='float']",
            "*[class*='seed']",
            "*[class*='paint']"
        ]
        
        # First wait for any loading to complete
        time.sleep(5)
        
        # Then check for results
        for i in range(10):  # Wait up to 20 seconds
            try:
                for selector in result_indicators:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        visible_elements = [e for e in elements if e.is_displayed()]
                        if visible_elements:
                            self.logger.info(f"Found results with selector: {selector}")
                            time.sleep(2)  # Additional wait for content to stabilize
                            return True
            except Exception as e:
                self.logger.debug(f"Result check failed: {e}")
            
            time.sleep(2)
        
        return False
    
    def _extract_float_value(self) -> Optional[float]:
        """Extract float value using improved selectors"""
        # Look for elements containing decimal numbers
        try:
            # Get all text on the page
            page_text = self.driver.page_source
            
            # Find potential float values using regex
            float_pattern = r'\b0\.\d{3,}\b'  # Matches 0.xxx format
            matches = re.findall(float_pattern, page_text)
            
            for match in matches:
                try:
                    float_val = float(match)
                    if 0.0 <= float_val <= 1.0:
                        self.logger.info(f"Found float value: {float_val}")
                        return float_val
                except ValueError:
                    continue
            
            # Alternative: look for specific elements
            selectors = [
                "*[class*='float']",
                "*[id*='float']",
                "span, div, p"
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        text = element.text.strip()
                        if text and '.' in text:
                            match = re.search(r'(\d+\.\d+)', text)
                            if match:
                                float_val = float(match.group(1))
                                if 0.0 <= float_val <= 1.0:
                                    self.logger.info(f"Found float in element: {float_val}")
                                    return float_val
                    except (ValueError, AttributeError):
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Float extraction error: {e}")
        
        return None
    
    def _extract_paint_seed(self) -> Optional[int]:
        """Extract paint seed using improved selectors"""
        try:
            # Look for integer values that could be paint seeds
            page_text = self.driver.page_source
            
            # Find potential paint seed values (typically 3-4 digit integers)
            seed_pattern = r'\b\d{3,4}\b'
            matches = re.findall(seed_pattern, page_text)
            
            for match in matches:
                try:
                    seed_val = int(match)
                    if 1 <= seed_val <= 1000:  # Reasonable paint seed range
                        self.logger.info(f"Found potential paint seed: {seed_val}")
                        return seed_val
                except ValueError:
                    continue
            
            # Alternative: look in specific elements
            selectors = [
                "*[class*='seed']",
                "*[class*='paint']",
                "*[id*='seed']",
                "*[id*='paint']",
                "span, div, p"
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        text = element.text.strip()
                        if text and text.isdigit():
                            seed_val = int(text)
                            if 1 <= seed_val <= 1000:
                                self.logger.info(f"Found paint seed in element: {seed_val}")
                                return seed_val
                    except (ValueError, AttributeError):
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Paint seed extraction error: {e}")
        
        return None
    
    def _extract_weapon_info(self) -> Dict[str, str]:
        """Extract additional weapon information"""
        info = {}
        
        try:
            # Look for weapon and skin names in page title or headings
            title_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, .title, .weapon-name")
            for element in title_elements:
                text = element.text.strip()
                if '|' in text:  # Common format: "AK-47 | Redline"
                    parts = text.split('|')
                    if len(parts) >= 2:
                        info['weapon_name'] = parts[0].strip()
                        info['skin_name'] = parts[1].strip()
                        break
            
            # Look for wear rating
            wear_elements = self.driver.find_elements(By.CSS_SELECTOR, "*[class*='wear'], *[class*='condition']")
            for element in wear_elements:
                text = element.text.strip().lower()
                if any(wear in text for wear in ['factory new', 'minimal wear', 'field-tested', 'well-worn', 'battle-scarred']):
                    info['wear_rating'] = element.text.strip()
                    break
                    
        except Exception as e:
            self.logger.debug(f"Weapon info extraction error: {e}")
        
        return info
    
    def cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning up WebDriver: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


# Example usage
def test_improved_scraper():
    """Test the improved scraper"""
    scraper = ImprovedCSFloatScraper(headless=False)  # Set to True for headless mode
    
    # Test with the inspect link from your screenshot
    test_link = "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198205836117A4179072013D1688132858662473768"
    
    try:
        result = scraper.get_float_data(test_link)
        print(f"Result: {result}")
        
        if result.success:
            print(f"Float: {result.float_value}")
            print(f"Paint Seed: {result.paint_seed}")
            print(f"Weapon: {result.weapon_name}")
            print(f"Skin: {result.skin_name}")
        else:
            print(f"Failed: {result.error}")
            
    finally:
        scraper.cleanup()

if __name__ == '__main__':
    test_improved_scraper()
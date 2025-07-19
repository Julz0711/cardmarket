"""
CSFloat Scraper for retrieving float values and paint seeds
Handles scraping of CSFloat.com for CS2 item float values and pattern indices

Features:
- Extracts float values from CSFloat checker
- Gets paint seed (pattern) values
- Handles inspect link processing
- Selenium-based web scraping

Usage:
    scraper = CSFloatScraper()
    float_data = scraper.get_float_data(inspect_link)
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
from .base_scraper import BaseScraper, ScraperError, ValidationError

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
    success: bool = False
    error: Optional[str] = None

class CSFloatScraper(BaseScraper):
    """CSFloat scraper for float values and paint seeds"""
    
    def __init__(self, headless: bool = True):
        super().__init__("CSFloat")
        self.driver = None
        self.headless = headless
        self.base_url = "https://csfloat.com/checker"
        
        self._setup_driver()
        
    def _setup_driver(self):
        """Setup Chrome WebDriver for CSFloat scraping"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Enhanced Chrome options to reduce errors and improve stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--window-size=1280,720')  # Smaller window size
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Don't load images to save resources
        chrome_options.add_argument('--disable-javascript')  # Disable JS initially, we'll enable as needed
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Logging options to reduce console spam
        chrome_options.add_argument('--log-level=3')  # Only fatal errors
        chrome_options.add_argument('--silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Extra options to suppress GCM and Chrome internal logs
        chrome_options.add_argument('--disable-cloud-import')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-print-preview')
        chrome_options.add_argument('--disable-web-resources')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-service-autorun')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-gcm-registration')
        chrome_options.add_argument('--disable-gcm')
        # Performance optimizations
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,  # Block images
                "plugins": 2,  # Block plugins
                "popups": 2,  # Block popups
                "geolocation": 2,  # Block location sharing
                "notifications": 2,  # Block notifications
                "media_stream": 2,  # Block media stream
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = Service(ChromeDriverManager().install())
            else:
                service = Service()  # Assumes chromedriver is in PATH
            
            # Disable logging for service
            service.log_path = 'NUL' if os.name == 'nt' else '/dev/null'
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(5)  # Reduced wait time
            self.driver.set_page_load_timeout(30)  # Set page load timeout
            self.logger.info("Chrome WebDriver initialized successfully for CSFloat")
            
        except Exception as e:
            try:
                service = Service()  # Fallback to PATH
                service.log_path = 'NUL' if os.name == 'nt' else '/dev/null'
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.implicitly_wait(5)
                self.driver.set_page_load_timeout(30)
                self.logger.info("Chrome WebDriver initialized with fallback method for CSFloat")
            except Exception as e2:
                raise ScraperError(f"Failed to initialize Chrome WebDriver for CSFloat: {e2}")
        
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters for CSFloat scraping"""
        inspect_link = kwargs.get('inspect_link')
        
        if not inspect_link or not isinstance(inspect_link, str):
            raise ValidationError("Inspect link must be a non-empty string")
        
        # Basic validation for Steam inspect link format
        if 'steam://' not in inspect_link and 'steamcommunity.com' not in inspect_link:
            raise ValidationError("Invalid inspect link format - must be a Steam inspect link")
        
        return True
    
    def scrape(self, **kwargs) -> Dict[str, Any]:
        """
        Main scraping method - not used for CSFloat, use get_float_data instead
        """
        return self.get_float_data(kwargs.get('inspect_link'))
    
    def get_float_data(self, inspect_link: str) -> FloatData:
        """
        Get float value and paint seed for a CS2 item from CSFloat
        
        Args:
            inspect_link (str): Steam inspect link for the item
            
        Returns:
            FloatData: Object containing float value, paint seed, and success status
        """
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                self.validate_input(inspect_link=inspect_link)
                
                self.logger.info(f"Getting float data (attempt {attempt + 1}/{max_retries + 1}): {inspect_link[:50]}...")
                
                # Navigate to CSFloat checker with timeout handling
                try:
                    self.driver.get(self.base_url)
                except Exception as e:
                    if attempt < max_retries:
                        self.logger.warning(f"Page load failed, retrying: {e}")
                        time.sleep(3)
                        continue
                    else:
                        raise
                
                # Wait for page to load with explicit timeout
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "input"))
                    )
                except TimeoutException:
                    if attempt < max_retries:
                        self.logger.warning("Page load timeout, retrying...")
                        time.sleep(5)
                        continue
                    else:
                        raise TimeoutException("CSFloat page failed to load")
                
                # Add small delay to let Angular fully initialize
                time.sleep(2)
                
                # Find and fill the input field with retry logic
                input_element = None
                for input_attempt in range(3):
                    try:
                        input_selector = "//input[contains(@placeholder, 'Inspect') or contains(@placeholder, 'inspect') or @type='text']"
                        input_element = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, input_selector))
                        )
                        break
                    except TimeoutException:
                        if input_attempt < 2:
                            self.logger.warning(f"Input element not found, trying alternative selector...")
                            # Try alternative selector
                            try:
                                input_element = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                                if input_element.is_enabled():
                                    break
                            except:
                                pass
                            time.sleep(2)
                        else:
                            raise TimeoutException("Could not find input element")
                
                if not input_element:
                    raise ScraperError("Input element not found")
                
                # Clear and input the inspect link
                try:
                    input_element.clear()
                    time.sleep(0.5)
                    input_element.send_keys(inspect_link)
                    time.sleep(0.5)
                except Exception as e:
                    if attempt < max_retries:
                        self.logger.warning(f"Input failed, retrying: {e}")
                        continue
                    else:
                        raise
                
                # Find and click the lookup button with retry logic
                lookup_button = None
                for button_attempt in range(3):
                    try:
                        # Try multiple button selectors
                        button_selectors = [
                            "//button[contains(text(), 'Lookup') or contains(text(), 'Check') or contains(text(), 'Submit')]",
                            "//button[@type='submit']",
                            "button[type='submit']",
                            ".mat-raised-button"
                        ]
                        
                        for selector in button_selectors:
                            try:
                                if selector.startswith("//"):
                                    lookup_button = WebDriverWait(self.driver, 5).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                else:
                                    lookup_button = WebDriverWait(self.driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                break
                            except TimeoutException:
                                continue
                        
                        if lookup_button:
                            break
                        
                        if button_attempt < 2:
                            time.sleep(2)
                        
                    except TimeoutException:
                        continue
                
                if not lookup_button:
                    raise TimeoutException("Could not find lookup button")
                
                # Click the button
                try:
                    lookup_button.click()
                except Exception as e:
                    # Try JavaScript click as fallback
                    try:
                        self.driver.execute_script("arguments[0].click();", lookup_button)
                    except:
                        if attempt < max_retries:
                            self.logger.warning(f"Button click failed, retrying: {e}")
                            continue
                        else:
                            raise
                
                # Wait for results to load with progressive timeout
                time.sleep(3)
                
                # Try to get float value and paint seed
                float_value = self._extract_float_value()
                paint_seed = self._extract_paint_seed()
                
                if float_value is not None or paint_seed is not None:
                    self.logger.info(f"Successfully extracted - Float: {float_value}, Paint Seed: {paint_seed}")
                    return FloatData(
                        float_value=float_value,
                        paint_seed=paint_seed,
                        inspect_link=inspect_link,
                        success=True
                    )
                else:
                    if attempt < max_retries:
                        self.logger.warning("No data found, retrying...")
                        time.sleep(5)
                        continue
                    else:
                        self.logger.warning("Could not extract float or paint seed data after all retries")
                        return FloatData(
                            float_value=None,
                            paint_seed=None,
                            inspect_link=inspect_link,
                            success=False,
                            error="No data found after all retries"
                        )
                
            except ValidationError as e:
                self.logger.error(f"Validation error: {e}")
                return FloatData(
                    float_value=None,
                    paint_seed=None,
                    inspect_link=inspect_link,
                    success=False,
                    error=str(e)
                )
            except TimeoutException as e:
                if attempt < max_retries:
                    self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying: {e}")
                    time.sleep(5)
                    continue
                else:
                    self.logger.error(f"Final timeout after all retries: {e}")
                    return FloatData(
                        float_value=None,
                        paint_seed=None,
                        inspect_link=inspect_link,
                        success=False,
                        error="Timeout after all retries"
                    )
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"Error on attempt {attempt + 1}, retrying: {e}")
                    time.sleep(5)
                    continue
                else:
                    self.logger.error(f"Final error after all retries: {e}")
                    return FloatData(
                        float_value=None,
                        paint_seed=None,
                        inspect_link=inspect_link,
                        success=False,
                        error=str(e)
                    )
    
    def _extract_float_value(self) -> Optional[float]:
        """
        Extract the float value from the CSFloat results page
        
        Returns:
            Optional[float]: The float value if found, None otherwise
        """
        # Multiple selectors to try for float value
        float_selectors = [
            # Original selectors
            "/html/body/app-root/div/div[2]/app-checker-home/div/div/div[3]/div[2]/app-checker-item/div/div[2]/div[2]/item-float-bar/div/div[2]/div[1]",
            "/html/body/app-root/div/div[2]/app-checker-home/div/div/div[4]/div[2]/div[1]/div[1]/span[2]",
            "/html/body/app-root/div/div[2]/app-checker-home/div/div/div[4]/div[2]/div[1]/div[1]/span",
            # Alternative selectors
            "//span[contains(@class, 'float') or contains(text(), '0.')]",
            "//div[contains(@class, 'float-value')]//span",
            ".float-value span",
            "[data-testid='float-value']",
            # Generic selectors for text containing decimal numbers
            "//span[contains(text(), '0.') and string-length(text()) > 3 and string-length(text()) < 10]"
        ]
        
        for selector in float_selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                
                text = element.text.strip()
                self.logger.debug(f"Float element text: '{text}' from selector: {selector}")
                
                # Try to extract float from text
                float_match = re.search(r'(\d+\.\d+)', text)
                if float_match:
                    float_value = float(float_match.group(1))
                    if 0.0 <= float_value <= 1.0:  # Valid float range
                        self.logger.info(f"Found float value: {float_value}")
                        return float_value
                        
            except (TimeoutException, ValueError, NoSuchElementException) as e:
                self.logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        # Try to find any elements that might contain float values
        try:
            all_spans = self.driver.find_elements(By.TAG_NAME, "span")
            for span in all_spans:
                try:
                    text = span.text.strip()
                    if text and '.' in text:
                        float_match = re.search(r'(\d+\.\d+)', text)
                        if float_match:
                            float_value = float(float_match.group(1))
                            if 0.0 <= float_value <= 1.0:
                                self.logger.info(f"Found float value in span: {float_value}")
                                return float_value
                except (ValueError, AttributeError):
                    continue
        except Exception as e:
            self.logger.debug(f"Error in fallback float search: {e}")
        
        self.logger.warning("Could not extract float value")
        return None

    def _extract_paint_seed(self) -> Optional[int]:
        """
        Extract the paint seed from the CSFloat results page
        
        Returns:
            Optional[int]: The paint seed if found, None otherwise
        """
        # Multiple selectors to try for paint seed
        paint_seed_selectors = [
            # Original selectors
            "/html/body/app-root/div/div[2]/app-checker-home/div/div/div[3]/div[2]/app-checker-item/div/div[2]/div[3]/div[1]/div[2]",
            "/html/body/app-root/div/div[2]/app-checker-home/div/div/div[4]/div[2]/div[1]/div[2]/span[2]",
            "/html/body/app-root/div/div[2]/app-checker-home/div/div/div[4]/div[2]/div[1]/div[2]/span",
            # Alternative selectors
            "//span[contains(@class, 'seed') or contains(@class, 'paint')]",
            "//div[contains(@class, 'paint-seed')]//span",
            ".paint-seed span",
            "[data-testid='paint-seed']",
            # Generic selectors for integer values
            "//span[string-length(text()) > 2 and string-length(text()) < 10 and not(contains(text(), '.'))]"
        ]
        
        for selector in paint_seed_selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                
                text = element.text.strip()
                self.logger.debug(f"Paint seed element text: '{text}' from selector: {selector}")
                
                # Try to extract integer from text
                seed_match = re.search(r'(\d+)', text)
                if seed_match:
                    seed_value = int(seed_match.group(1))
                    if 0 <= seed_value <= 1000:  # Reasonable paint seed range
                        self.logger.info(f"Found paint seed: {seed_value}")
                        return seed_value
                        
            except (TimeoutException, ValueError, NoSuchElementException) as e:
                self.logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        # Try to find any elements that might contain paint seed values
        try:
            all_spans = self.driver.find_elements(By.TAG_NAME, "span")
            for span in all_spans:
                try:
                    text = span.text.strip()
                    if text and text.isdigit():
                        seed_value = int(text)
                        if 0 <= seed_value <= 1000:
                            self.logger.info(f"Found paint seed in span: {seed_value}")
                            return seed_value
                except (ValueError, AttributeError):
                    continue
        except Exception as e:
            self.logger.debug(f"Error in fallback paint seed search: {e}")
        
        self.logger.warning("Could not extract paint seed")
        return None
    
    def batch_get_float_data(self, inspect_links: list) -> list:
        """Get float data for multiple items"""
        results = []
        
        for i, inspect_link in enumerate(inspect_links):
            self.logger.info(f"Processing item {i+1}/{len(inspect_links)}")
            
            float_data = self.get_float_data(inspect_link)
            results.append(float_data)
            
            # Add delay between requests to avoid overwhelming CSFloat
            if i < len(inspect_links) - 1:
                time.sleep(2)
        
        return results
    
    def _cleanup(self):
        """Clean up WebDriver resources"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning up WebDriver: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self._cleanup()

# Example usage and testing
def test_csfloat_scraper():
    """Test the CSFloat scraper with a sample inspect link"""
    scraper = CSFloatScraper(headless=False)  # Set to False to see the browser
    
    # Example inspect link (replace with a real one for testing)
    test_inspect_link = "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198123456789A12345678901D7411569213947987648"
    
    try:
        result = scraper.get_float_data(test_inspect_link)
        print(f"Float Data: {result}")
    finally:
        scraper._cleanup()

if __name__ == '__main__':
    test_csfloat_scraper()

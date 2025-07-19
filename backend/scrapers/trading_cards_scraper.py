"""
Trading Cards Scraper
Handles scraping of trading card data from CardMarket
"""

from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import re

from .base_scraper import BaseScraper, ScraperError, ValidationError

# Try to import webdriver_manager, fallback if not available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False


class TradingCardsScraper(BaseScraper):
    """Scraper for trading card data from CardMarket"""
    
    def __init__(self, headless: bool = True):
        super().__init__("TradingCards")
        self.driver = None
        self.headless = headless
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with optimal settings"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = Service(ChromeDriverManager().install())
            else:
                service = Service()
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
            except Exception as e2:
                raise ScraperError(f"Failed to initialize Chrome WebDriver: {e2}")
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters for trading cards scraping"""
        required_fields = ['tcg', 'expansion', 'numbers']
        
        for field in required_fields:
            if field not in kwargs:
                raise ValidationError(f"Missing required field: {field}")
        
        tcg = kwargs.get('tcg')
        expansion = kwargs.get('expansion')
        numbers = kwargs.get('numbers')
        
        if not tcg or not isinstance(tcg, str):
            raise ValidationError("TCG must be a non-empty string")
        
        if not expansion or not isinstance(expansion, str):
            raise ValidationError("Expansion must be a non-empty string")
        
        if not numbers or not isinstance(numbers, list) or len(numbers) == 0:
            raise ValidationError("Numbers must be a non-empty list")
        
        # Check if all numbers are valid integers
        for num in numbers:
            if not isinstance(num, int) or num <= 0:
                raise ValidationError(f"Invalid card number: {num}")
        
        return True
    
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape trading card data from CardMarket using the original working logic
        
        Args:
            tcg (str): Trading Card Game name
            expansion (str): Set/expansion name
            numbers (List[int]): List of card numbers to scrape
            
        Returns:
            List of card dictionaries
        """
        self.validate_input(**kwargs)
        self.log_scraping_start(**kwargs)
        
        tcg = kwargs['tcg']
        expansion = kwargs['expansion']
        numbers = kwargs['numbers']
        
        cards = []

        #test
        
        try:
            # Navigate to CardMarket search page
            url = f"https://www.cardmarket.com/en/{tcg}/Products/Search?category=-1"
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(2)
            
            # Select expansion using original logic
            try:
                # Click expansion dropdown (index 1 based on original code)
                expansion_elements = self.driver.find_elements(By.XPATH, "//option[contains(@value, '51')]")
                if len(expansion_elements) > 1:
                    expansion_elements[1].click()
                else:
                    self.logger.warning("Could not find expansion dropdown")
                    return cards
                
                # Select specific expansion
                expansion_option = self.driver.find_element(By.XPATH, f"//option[normalize-space(.)='{expansion}']")
                expansion_option.click()
                
                # Click search button
                search_buttons = self.driver.find_elements(By.XPATH, "//input[contains(@class, 'btn btn-primary')]")
                if search_buttons:
                    search_buttons[0].click()
                    time.sleep(2)
                else:
                    self.logger.warning("Could not find search button")
                    return cards
                    
            except NoSuchElementException as e:
                self.logger.error(f"Could not navigate to expansion '{expansion}': {e}")
                return cards
            
            # Save the search URL for reuse
            spec_url = self.driver.current_url
            self.logger.info(f"Base search URL: {spec_url}")
            
            # Scrape each card number using original method
            for number in numbers:
                try:
                    self.logger.info(f"Scraping card number: {number}")
                    
                    # Navigate back to search page
                    self.driver.get(spec_url)
                    time.sleep(1)
                    
                    # Enter card number in search
                    search_inputs = self.driver.find_elements(By.NAME, "searchString")
                    if len(search_inputs) > 1:
                        search_inputs[1].clear()
                        search_inputs[1].send_keys(str(number))
                    else:
                        self.logger.warning(f"Could not find search input for card {number}")
                        continue
                    
                    # Click search
                    search_buttons = self.driver.find_elements(By.XPATH, "//input[contains(@class, 'btn btn-primary')]")
                    if search_buttons:
                        search_buttons[0].click()
                        time.sleep(2)
                    else:
                        self.logger.warning(f"Could not find search button for card {number}")
                        continue
                    
                    # Extract card data using original method
                    card_data = self._extract_card_data_original(tcg, expansion, number)
                    if card_data:
                        cards.append(card_data)
                        self.logger.info(f"Successfully scraped: {card_data['name']} (#{card_data['number']})")
                    else:
                        self.logger.warning(f"Failed to extract data for card {number}")
                        
                except Exception as e:
                    self.logger.error(f"Error scraping card {number}: {e}")
                    continue
            
            self.log_scraping_complete(len(cards))
            return cards
            
        except Exception as e:
            self.log_error(e)
            raise ScraperError(f"Scraping failed: {e}")
        
        finally:
            self._cleanup()
    
    def _extract_card_data_original(self, tcg: str, expansion: str, target_number: int) -> Dict[str, Any]:
        """Extract card data from current page using original working logic"""
        try:
            # Extract number
            number_elements = self.driver.find_elements(
                By.XPATH, 
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col')]//div[contains(@class, 'row g-0')]//div"
            )
            if len(number_elements) > 3:
                number_text = number_elements[3].text.strip()
                number = int(''.join(filter(str.isdigit, number_text)))
            else:
                self.logger.warning("Could not find card number")
                number = target_number
            
            # Extract name
            name_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col')]//div[contains(@class, 'row g-0')]//a"
            )
            if name_elements:
                name = name_elements[0].text.strip()
            else:
                self.logger.warning("Could not find card name")
                name = f"Card #{target_number}"
            
            # Extract rarity using BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            rarity_element = soup.find("svg", attrs={"aria-label": True})
            if rarity_element:
                rarity = rarity_element["aria-label"]
            else:
                self.logger.warning("Could not find rarity")
                rarity = "Unknown"
            
            # Extract supply
            supply_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col-availability')]"
            )
            if supply_elements:
                supply_text = supply_elements[0].text.strip()
                supply = int(''.join(filter(str.isdigit, supply_text)))
            else:
                self.logger.warning("Could not find supply")
                supply = 0
            
            # Extract current price
            price_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col-price')]"
            )
            if price_elements:
                price_text = price_elements[0].text.strip()
                # Remove currency symbol and convert comma to dot
                price_clean = price_text[:-2].replace(",", ".")
                current_price = float(price_clean)
            else:
                self.logger.warning("Could not find price")
                current_price = 0.0
            
            return {
                "tcg": tcg,
                "expansion": expansion,
                "number": number,
                "name": name,
                "rarity": rarity,
                "supply": supply,
                "current_price": current_price,
                "price_bought": 0.0,
                "psa": "",
                "last_updated": self.format_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting card data: {e}")
            return None
    
    def _cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error during driver cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self._cleanup()

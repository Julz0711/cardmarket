"""
CardMarket Scraper Module
Integrates with Flask backend to scrape card data from CardMarket.com
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import time
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CardMarketScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome WebDriver"""
        self.driver = None
        self.headless = headless
        self._setup_driver()
    
    def _setup_driver(self):
        """Set up Chrome WebDriver with options"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def scrape_cards(self, tcg, expansion, numbers):
        """
        Scrape card entries from CardMarket
        
        Args:
            tcg: Trading Card Game (e.g., "Pokemon")
            expansion: Set/expansion name
            numbers: List of card numbers to scrape
        
        Returns:
            List of card dictionaries
        """
        cards = []
        try:
            # Navigate to CardMarket search page
            url = f"https://www.cardmarket.com/en/{tcg}/Products/Search?category=-1"
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(2)
            
            # Select expansion
            try:
                # Click expansion dropdown (index 1 based on your code)
                expansion_elements = self.driver.find_elements(By.XPATH, "//option[contains(@value, '51')]")
                if len(expansion_elements) > 1:
                    expansion_elements[1].click()
                else:
                    logger.warning("Could not find expansion dropdown")
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
                    logger.warning("Could not find search button")
                    return cards
                    
            except NoSuchElementException as e:
                logger.error(f"Could not navigate to expansion '{expansion}': {e}")
                return cards
            
            # Save the search URL for reuse
            spec_url = self.driver.current_url
            logger.info(f"Base search URL: {spec_url}")
            
            # Scrape each card number
            for number in numbers:
                try:
                    logger.info(f"Scraping card number: {number}")
                    
                    # Navigate back to search page
                    self.driver.get(spec_url)
                    time.sleep(1)
                    
                    # Enter card number in search
                    search_inputs = self.driver.find_elements(By.NAME, "searchString")
                    if len(search_inputs) > 1:
                        search_inputs[1].clear()
                        search_inputs[1].send_keys(str(number))
                    else:
                        logger.warning(f"Could not find search input for card {number}")
                        continue
                    
                    # Click search
                    search_buttons = self.driver.find_elements(By.XPATH, "//input[contains(@class, 'btn btn-primary')]")
                    if search_buttons:
                        search_buttons[0].click()
                        time.sleep(2)
                    else:
                        logger.warning(f"Could not find search button for card {number}")
                        continue
                    
                    # Extract card data
                    card_data = self._extract_card_data(tcg, expansion)
                    if card_data:
                        cards.append(card_data)
                        logger.info(f"Successfully scraped: {card_data['name']} (#{card_data['number']})")
                    else:
                        logger.warning(f"Failed to extract data for card {number}")
                        
                except Exception as e:
                    logger.error(f"Error scraping card {number}: {e}")
                    continue
            
            return cards
            
        except Exception as e:
            logger.error(f"Error in scrape_cards: {e}")
            return cards
    
    def _extract_card_data(self, tcg, expansion):
        """Extract card data from current page"""
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
                logger.warning("Could not find card number")
                return None
            
            # Extract name
            name_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col')]//div[contains(@class, 'row g-0')]//a"
            )
            if name_elements:
                name = name_elements[0].text.strip()
            else:
                logger.warning("Could not find card name")
                return None
            
            # Extract rarity using BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            rarity_element = soup.find("svg", attrs={"aria-label": True})
            if rarity_element:
                rarity = rarity_element["aria-label"]
            else:
                logger.warning("Could not find rarity")
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
                logger.warning("Could not find supply")
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
                logger.warning("Could not find price")
                current_price = 0.0
            
            return {
                "tcg": tcg,
                "expansion": expansion,
                "number": number,
                "name": name,
                "rarity": rarity,
                "supply": supply,
                "current_price": current_price,
                "price_bought": "-",
                "psa": "raw"
            }
            
        except Exception as e:
            logger.error(f"Error extracting card data: {e}")
            return None
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

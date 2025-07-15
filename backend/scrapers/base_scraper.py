"""
Base Scraper Class
Provides common functionality for all scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"scrapers.{name}")
        
    @abstractmethod
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Abstract method that each scraper must implement
        
        Returns:
            List of dictionaries containing scraped data
        """
        pass
    
    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters for the scraper
        
        Returns:
            True if input is valid, False otherwise
        """
        pass
    
    def log_scraping_start(self, **kwargs):
        """Log the start of scraping operation"""
        self.logger.info(f"Starting {self.name} scraping with parameters: {kwargs}")
    
    def log_scraping_complete(self, count: int):
        """Log the completion of scraping operation"""
        self.logger.info(f"Completed {self.name} scraping. Found {count} items")
    
    def log_error(self, error: Exception):
        """Log scraping errors"""
        self.logger.error(f"Error in {self.name} scraper: {str(error)}")
    
    def format_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    def clean_price(self, price_str: str) -> float:
        """
        Clean and convert price string to float
        
        Args:
            price_str: Price string (e.g., "€1.23", "$5.67", "46,--€", "1,234.56$")
            
        Returns:
            Float value of the price
        """
        if not price_str:
            return 0.0
            
        # Remove currency symbols and whitespace
        cleaned = price_str.replace('€', '').replace('$', '').replace('£', '').replace('¥', '').strip()
        
        # Handle special European format like "46,--" (means 46.00)
        if cleaned.endswith(',--'):
            cleaned = cleaned.replace(',--', '')
            try:
                return float(cleaned)
            except ValueError:
                self.logger.warning(f"Could not parse price: {price_str}")
                return 0.0
        
        # Handle European decimal format (comma as decimal separator)
        # But we need to distinguish between thousands separator and decimal separator
        if ',' in cleaned and '.' in cleaned:
            # Format like "1,234.56" - comma is thousands separator
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned and cleaned.count(',') == 1:
            # Check if comma is likely a decimal separator (2 digits or less after comma)
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Format like "46,50" - comma is decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Format like "1,234" - comma is thousands separator
                cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except ValueError:
            self.logger.warning(f"Could not parse price: {price_str}")
            return 0.0
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
            
        return text.strip().replace('\n', ' ').replace('\t', ' ')


class ScraperError(Exception):
    """Custom exception for scraper errors"""
    pass


class ValidationError(ScraperError):
    """Exception raised when input validation fails"""
    pass

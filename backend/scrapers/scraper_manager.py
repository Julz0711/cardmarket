"""
Scraper Manager
Centralized management for all portfolio scrapers
"""

from typing import Dict, List, Any, Optional, Type
import logging
from datetime import datetime

from .base_scraper import BaseScraper, ScraperError
from .trading_cards_scraper import TradingCardsScraper
from .steam_inventory_scraper import SteamInventoryScraper


class ScraperManager:
    """Central manager for all portfolio scrapers"""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize scraper manager with optional API keys
        
        Args:
            api_keys: Dictionary of API keys for various services
                     {
                         'alpha_vantage': 'key',
                         'coinmarketcap': 'key',
                         'steam': 'key'
                     }
        """
        self.api_keys = api_keys or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize scrapers
        self.scrapers: Dict[str, BaseScraper] = {
            'cards': TradingCardsScraper(),
            'steam': SteamInventoryScraper(),
        }
        
        self.logger.info("ScraperManager initialized with scrapers: %s", list(self.scrapers.keys()))
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper types"""
        return list(self.scrapers.keys())
    
    def get_scraper(self, scraper_type: str) -> Optional[BaseScraper]:
        """Get scraper instance by type"""
        return self.scrapers.get(scraper_type)
    
    def scrape_assets(self, scraper_type: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape assets using specified scraper
        
        Args:
            scraper_type: Type of scraper to use ('cards', 'stocks', 'etf', 'crypto', 'steam')
            **kwargs: Parameters to pass to the scraper
            
        Returns:
            List of asset dictionaries
            
        Raises:
            ScraperError: If scraper type is invalid or scraping fails
        """
        if scraper_type not in self.scrapers:
            available = ', '.join(self.scrapers.keys())
            raise ScraperError(f"Invalid scraper type '{scraper_type}'. Available: {available}")
        
        # Special handling for scrapers with custom parameters
        if scraper_type == 'cards' and 'headless' in kwargs:
            from .trading_cards_scraper import TradingCardsScraper
            headless = kwargs.pop('headless')
            card_language = kwargs.pop('card_language', None)  # Extract 'card_language'
            scraper = TradingCardsScraper(headless=headless)
            kwargs['card_language'] = card_language  # Pass 'card_language' to the scraper
        elif scraper_type == 'steam' and 'headless' in kwargs:
            from .steam_inventory_scraper import SteamInventoryScraper
            headless = kwargs.pop('headless', True)
            scraper = SteamInventoryScraper(headless=headless)
        else:
            scraper = self.scrapers[scraper_type]
        
        try:
            self.logger.info(f"Starting {scraper_type} scraping with params: {kwargs}")
            assets = scraper.scrape(**kwargs)
            self.logger.info(f"Completed {scraper_type} scraping. Found {len(assets)} assets")
            return assets
            
        except Exception as e:
            self.logger.error(f"Error in {scraper_type} scraping: {e}")
            raise ScraperError(f"Failed to scrape {scraper_type}: {e}")
        
        finally:
            # Clean up dynamically created scrapers
            if ((scraper_type == 'cards' or scraper_type == 'steam') and 
                scraper != self.scrapers.get(scraper_type) and hasattr(scraper, '_cleanup')):
                scraper._cleanup()
    
    def scrape_trading_cards(self, expansion: str, number_from: int, number_to: int) -> List[Dict[str, Any]]:
        """Scrape trading cards from CardMarket"""
        return self.scrape_assets('cards', 
                                expansion=expansion, 
                                number_from=number_from, 
                                number_to=number_to)
    
    def get_scraper_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all scrapers, including running state"""
        status = {}
        for scraper_type, scraper in self.scrapers.items():
            running = getattr(scraper, 'is_running', False)
            status[scraper_type] = {
                'name': scraper.name,
                'available': True,
                'requires_api_key': self._requires_api_key(scraper_type),
                'has_api_key': self._has_required_api_key(scraper_type),
                'last_used': getattr(scraper, 'last_used', None),
                'running': running
            }
        return status
    
    def _requires_api_key(self, scraper_type: str) -> bool:
        """Check if scraper type requires API key for full functionality"""
        api_key_requirements = {
            'cards': False,  # CardMarket scraping doesn't require API key
            'stocks': False,  # Yahoo Finance is primary, Alpha Vantage is fallback
            'etf': False,     # Yahoo Finance is primary, Alpha Vantage is fallback
            'crypto': False,  # CoinGecko is primary, CoinMarketCap is fallback
            'steam': True     # Steam API key required for inventory access
        }
        return api_key_requirements.get(scraper_type, False)
    
    def _has_required_api_key(self, scraper_type: str) -> bool:
        """Check if required API key is available for scraper type"""
        if not self._requires_api_key(scraper_type):
            return True
        
        key_mappings = {
            'steam': 'steam'
        }
        
        required_key = key_mappings.get(scraper_type)
        return required_key in self.api_keys if required_key else True
    
    def validate_scraper_config(self) -> Dict[str, List[str]]:
        """
        Validate scraper configuration and return any issues
        
        Returns:
            Dictionary with 'warnings' and 'errors' lists
        """
        issues = {
            'warnings': [],
            'errors': []
        }
        
        # Only cards scraper is active, no API keys needed for basic functionality
        issues['warnings'].append("Cards scraper ready - no external API keys required for basic functionality")
        
        return issues
    
    def get_supported_assets(self) -> Dict[str, Dict[str, Any]]:
        """Get information about supported asset types"""
        return {
            'cards': {
                'name': 'Trading Cards',
                'description': 'Pokemon, Yu-Gi-Oh, Magic: The Gathering, and other TCG cards from CardMarket',
                'parameters': ['tcg', 'expansion', 'numbers'],
                'example': {'tcg': 'Pokemon', 'expansion': 'Stellar Crown', 'numbers': [1, 2, 3, 4, 5]}
            }
        }

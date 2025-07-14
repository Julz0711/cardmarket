"""
Steam Inventory Scraper
Handles scraping of Steam inventory data using Steam API and CSFloat for pricing
"""

from typing import List, Dict, Any, Optional
import requests
import json
import time

from .base_scraper import BaseScraper, ScraperError, ValidationError


class SteamInventoryScraper(BaseScraper):
    """Scraper for Steam inventory data"""
    
    def __init__(self):
        super().__init__("SteamInventory")
        self.steam_api_base = "https://steamcommunity.com/inventory"
        self.csfloat_api_base = "https://csfloat.com/api/v1"
        
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters for Steam inventory scraping"""
        required_fields = ['steam_id']
        
        for field in required_fields:
            if field not in kwargs:
                raise ValidationError(f"Missing required field: {field}")
        
        steam_id = kwargs.get('steam_id')
        app_id = kwargs.get('app_id', '730')  # Default to CS2
        
        if not steam_id or not isinstance(steam_id, str):
            raise ValidationError("Steam ID must be a non-empty string")
        
        # Validate Steam ID format (basic check)
        if not steam_id.isdigit() and not steam_id.startswith('STEAM_'):
            raise ValidationError("Invalid Steam ID format")
        
        return True
    
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape Steam inventory data
        
        Args:
            steam_id (str): Steam ID or profile URL
            app_id (str): Steam App ID (default: 730 for CS2)
            
        Returns:
            List of Steam item dictionaries
        """
        self.validate_input(**kwargs)
        self.log_scraping_start(**kwargs)
        
        steam_id = kwargs['steam_id']
        app_id = kwargs.get('app_id', '730')  # Default to CS2
        
        items = []
        
        try:
            # Convert profile URL to Steam ID if needed
            steam_id = self._resolve_steam_id(steam_id)
            
            # Get inventory data
            inventory_data = self._get_inventory(steam_id, app_id)
            
            # Process each item
            for item_data in inventory_data:
                try:
                    item = self._process_item(item_data, app_id)
                    if item:
                        items.append(item)
                        self.logger.info(f"Processed item: {item.get('name', 'Unknown')}")
                        
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    self.logger.error(f"Error processing item: {e}")
                    continue
            
            self.log_scraping_complete(len(items))
            return items
            
        except Exception as e:
            self.log_error(e)
            raise ScraperError(f"Steam inventory scraping failed: {e}")
    
    def _resolve_steam_id(self, steam_input: str) -> str:
        """Convert profile URL to Steam ID if needed"""
        if steam_input.startswith('http'):
            # Extract Steam ID from URL
            if '/id/' in steam_input:
                # Custom URL, need to resolve via Steam API
                username = steam_input.split('/id/')[-1].rstrip('/')
                return self._resolve_vanity_url(username)
            elif '/profiles/' in steam_input:
                # Direct Steam ID in URL
                return steam_input.split('/profiles/')[-1].rstrip('/')
        
        return steam_input
    
    def _resolve_vanity_url(self, vanity_url: str) -> str:
        """Resolve vanity URL to Steam ID using Steam API"""
        # Note: This would require a Steam API key in production
        # For now, return the vanity URL and handle it in the inventory request
        self.logger.warning("Vanity URL resolution requires Steam API key")
        return vanity_url
    
    def _get_inventory(self, steam_id: str, app_id: str) -> List[Dict]:
        """Get inventory data from Steam API"""
        try:
            # Steam inventory endpoint
            url = f"{self.steam_api_base}/{steam_id}/{app_id}/2"
            
            # Add parameters
            params = {
                'l': 'english',
                'count': 5000
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('success'):
                raise ScraperError("Steam API returned unsuccessful response")
            
            # Combine assets and descriptions
            assets = data.get('assets', [])
            descriptions = data.get('descriptions', [])
            
            # Create lookup for descriptions
            desc_lookup = {}
            for desc in descriptions:
                key = f"{desc['classid']}_{desc['instanceid']}"
                desc_lookup[key] = desc
            
            # Combine assets with descriptions
            inventory_items = []
            for asset in assets:
                key = f"{asset['classid']}_{asset['instanceid']}"
                if key in desc_lookup:
                    item_data = {**asset, **desc_lookup[key]}
                    inventory_items.append(item_data)
            
            return inventory_items
            
        except requests.RequestException as e:
            raise ScraperError(f"Failed to fetch Steam inventory: {e}")
        except json.JSONDecodeError as e:
            raise ScraperError(f"Invalid JSON response from Steam API: {e}")
    
    def _process_item(self, item_data: Dict, app_id: str) -> Optional[Dict[str, Any]]:
        """Process a single Steam inventory item"""
        try:
            # Extract basic item info
            name = item_data.get('market_hash_name', 'Unknown Item')
            item_type = item_data.get('type', '')
            rarity = self._extract_rarity(item_data)
            
            # Get game name
            game_name = self._get_game_name(app_id)
            
            # Extract wear/exterior for CS2 items
            exterior = self._extract_exterior(name)
            
            # Get pricing data
            price_data = self._get_item_pricing(name, app_id)
            
            # Extract additional CS2-specific data
            float_value = None
            stickers = []
            
            if app_id == '730':  # CS2
                float_value = self._get_float_value(item_data)
                stickers = self._extract_stickers(item_data)
            
            return {
                'type': 'steam',
                'name': self.clean_text(name),
                'item_name': self.clean_text(name),
                'game': game_name,
                'quality': self.clean_text(rarity),
                'exterior': exterior,
                'float_value': float_value,
                'stickers': stickers,
                'current_price': price_data.get('current_price', 0.0),
                'price_bought': 0.0,  # To be set by user
                'quantity': 1,
                'last_updated': self.format_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing item {item_data.get('market_hash_name', 'Unknown')}: {e}")
            return None
    
    def _extract_rarity(self, item_data: Dict) -> str:
        """Extract item rarity/quality"""
        tags = item_data.get('tags', [])
        
        for tag in tags:
            if tag.get('category') == 'Rarity':
                return tag.get('localized_tag_name', 'Unknown')
            elif tag.get('category') == 'Quality':
                return tag.get('localized_tag_name', 'Unknown')
        
        return 'Unknown'
    
    def _extract_exterior(self, name: str) -> Optional[str]:
        """Extract wear/exterior from item name"""
        exteriors = ['Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred']
        
        for exterior in exteriors:
            if exterior in name:
                return exterior
        
        return None
    
    def _get_game_name(self, app_id: str) -> str:
        """Get game name from app ID"""
        game_names = {
            '730': 'Counter-Strike 2',
            '570': 'Dota 2',
            '440': 'Team Fortress 2',
            '252490': 'Rust',
            '304930': 'Unturned'
        }
        
        return game_names.get(app_id, f'App {app_id}')
    
    def _get_item_pricing(self, item_name: str, app_id: str) -> Dict[str, float]:
        """Get item pricing from various sources"""
        try:
            # For CS2 items, try CSFloat API
            if app_id == '730':
                return self._get_csfloat_pricing(item_name)
            else:
                # For other games, use Steam Community Market
                return self._get_steam_market_pricing(item_name, app_id)
                
        except Exception as e:
            self.logger.warning(f"Could not get pricing for {item_name}: {e}")
            return {'current_price': 0.0}
    
    def _get_csfloat_pricing(self, item_name: str) -> Dict[str, float]:
        """Get pricing from CSFloat API"""
        try:
            # Note: This is a placeholder for CSFloat API integration
            # The actual implementation would require proper API endpoints and authentication
            self.logger.info(f"Getting CSFloat pricing for: {item_name}")
            
            # Placeholder pricing logic
            return {'current_price': 0.0}
            
        except Exception as e:
            self.logger.warning(f"CSFloat pricing failed for {item_name}: {e}")
            return {'current_price': 0.0}
    
    def _get_steam_market_pricing(self, item_name: str, app_id: str) -> Dict[str, float]:
        """Get pricing from Steam Community Market"""
        try:
            # Steam Market API endpoint
            url = "https://steamcommunity.com/market/priceoverview/"
            params = {
                'appid': app_id,
                'currency': 3,  # EUR
                'market_hash_name': item_name
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success'):
                price_str = data.get('lowest_price', '€0.00')
                price = self.clean_price(price_str)
                return {'current_price': price}
            else:
                return {'current_price': 0.0}
                
        except Exception as e:
            self.logger.warning(f"Steam Market pricing failed for {item_name}: {e}")
            return {'current_price': 0.0}
    
    def _get_float_value(self, item_data: Dict) -> Optional[float]:
        """Get float value for CS2 items"""
        # Note: Getting float values requires additional API calls or inspection
        # This would need CSFloat API or similar service
        return None
    
    def _extract_stickers(self, item_data: Dict) -> List[str]:
        """Extract sticker information for CS2 items"""
        stickers = []
        
        # Parse item description for sticker information
        descriptions = item_data.get('descriptions', [])
        
        for desc in descriptions:
            if 'Sticker:' in desc.get('value', ''):
                # Extract sticker names from description
                sticker_text = desc['value']
                # Parse sticker information
                # This would need proper parsing logic based on Steam's format
                pass
        
        return stickers

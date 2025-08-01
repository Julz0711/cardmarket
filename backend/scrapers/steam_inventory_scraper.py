"""
Steam Inventory Scraper for CS2 Items
Handles scraping of Steam inventory data for Counter-Strike 2 items

Features:
- Extracts basic item information (name, rarity, condition, category)
- Steam inventory API integration
- Item categorization and type detection
- Image URL extraction
- Clean, simple implementation without pricing or float values

Usage:
    scraper = SteamInventoryScraper()
    items = scraper.scrape(steam_id="76561198123456789")
"""

from typing import List, Dict, Any, Optional
import requests
import json
from datetime import datetime
from scrapers.skinsearch_scraper import SkinSearchScraper
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, ScraperError, ValidationError

# Import CSFloat scraper for float and pattern data
try:
    from .csfloat_scraper import CSFloatScraper
    CSFLOAT_AVAILABLE = True
except ImportError:
    CSFLOAT_AVAILABLE = False

# Try to import webdriver_manager, fallback if not available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False


# Removed SteamMarketPricer class - no pricing functionality


class SteamInventoryScraper(BaseScraper):
    """Steam CS2 inventory scraper - simplified without pricing"""
    
    def __init__(self, headless: bool = True):
        super().__init__("SteamInventory")
        self.driver = None
        self.headless = headless
        self.steam_api_base = "https://steamcommunity.com/inventory"
        self.is_running = False
        self.last_used = None
        self._setup_driver()
        
    def _setup_driver(self):
        """Setup Chrome WebDriver for CS2 inventory inspection"""
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
                self.logger.warning(f"Could not initialize WebDriver: {e2}. Float values and pattern index will not be available.")
                self.driver = None
        
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters for Steam inventory scraping"""
        required_fields = ['steam_id']
        
        for field in required_fields:
            if field not in kwargs:
                raise ValidationError(f"Missing required field: {field}")
        
        steam_id = kwargs.get('steam_id')
        app_id = kwargs.get('app_id', '730')  # Default to CS2
        user_id = kwargs.get('user_id')  # Optional user_id for association
        
        if not steam_id or not isinstance(steam_id, str):
            raise ValidationError("Steam ID must be a non-empty string")
        
        # Validate Steam ID format (basic check)
        if not steam_id.isdigit() and not steam_id.startswith('STEAM_') and not steam_id.startswith('http'):
            raise ValidationError("Invalid Steam ID format")
        
        # Log user association info
        if user_id:
            self.logger.info(f"Steam scraping will associate items with user_id: {user_id}")
        else:
            self.logger.warning("No user_id provided - items will not be associated with a specific user")
        
        return True
    
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape Steam CS2 inventory data
        """
        self.is_running = True
        self.last_used = datetime.now().isoformat()
        try:
            self.validate_input(**kwargs)
            self.log_scraping_start(**kwargs)
            steam_id = kwargs['steam_id']
            app_id = kwargs.get('app_id', '730')  # Default to CS2
            include_floats = kwargs.get('include_floats', False)
            include_prices = kwargs.get('include_prices', False)  # Include prices is optional
            user_id = kwargs.get('user_id')  # Extract user_id parameter
            items = []
            skinsearch = SkinSearchScraper()
            # Extract Steam ID from URL if provided
            steam_id = self._extract_steam_id_from_url(steam_id)
            # Get inventory data
            inventory_data = self._get_inventory(steam_id, app_id)
            self.logger.info(f"Found {len(inventory_data)} items in inventory")
            # Process each CS2 item
            for i, item_data in enumerate(inventory_data):
                try:
                    item_name = item_data.get('market_hash_name', 'Unknown')
                    # Only process CS2 items
                    if self._is_cs2_item(item_data):
                        item = self._process_cs2_item(item_data, steam_id, include_floats, user_id)
                        if item:
                            # Fetch price info from SkinSearchScraper if requested
                            if include_prices:
                                price_result = skinsearch.scrape_steam_item(item)
                                if price_result and isinstance(price_result, dict):
                                    if price_result.get('success') and price_result.get('cheapest_price'):
                                        item['current_price'] = price_result['cheapest_price']['price']
                                        item['price_currency'] = price_result['cheapest_price']['currency']
                                        item['price_details'] = price_result['prices']
                                        item['skinsearch_url'] = price_result.get('url')
                                    else:
                                        item['current_price'] = 0
                                        item['price_details'] = []
                                        item['skinsearch_url'] = price_result.get('url') if price_result.get('url') else None
                                else:
                                    item['current_price'] = 0
                                    item['price_details'] = []
                                    item['skinsearch_url'] = None
                            else:
                                # Set default price data when prices not requested
                                item['current_price'] = 0
                                item['price_details'] = []
                                item['skinsearch_url'] = None
                            items.append(item)
                            self.logger.info(f"Processed item {i+1}/{len(inventory_data)}: {item.get('name', 'Unknown')} (Category: {item.get('item_category', 'unknown')})")
                        else:
                            self.logger.warning(f"Failed to process CS2 item: {item_name}")
                    else:
                        self.logger.debug(f"Skipped non-CS2 item: {item_name}")
                    # Rate limiting to avoid being blocked
                    if include_floats and self.driver:
                        time.sleep(1)  # Slower when fetching float values
                    else:
                        time.sleep(0.1)
                except Exception as e:
                    self.logger.error(f"Error processing item {item_data.get('market_hash_name', 'Unknown')}: {e}")
                    continue
            self.log_scraping_complete(len(items))
            return items
        except Exception as e:
            self.log_error(e)
            raise ScraperError(f"Steam inventory scraping failed: {e}")
        finally:
            self.is_running = False
            self._cleanup()
    
    def _extract_steam_id_from_url(self, steam_input: str) -> str:
        """Extract Steam ID from various formats"""
        if steam_input.startswith('http'):
            # Extract from full URL like: https://steamcommunity.com/profiles/76561198205836117/inventory/
            if '/profiles/' in steam_input:
                # Extract the Steam ID number
                match = re.search(r'/profiles/(\d+)', steam_input)
                if match:
                    return match.group(1)
            elif '/id/' in steam_input:
                # Handle custom URLs - would need Steam API to resolve
                self.logger.warning("Custom Steam URLs not fully supported, please use numeric Steam ID")
                return steam_input.split('/id/')[-1].rstrip('/')
        
        return steam_input
    
    def _get_inventory(self, steam_id: str, app_id: str) -> List[Dict]:
        """Get inventory data from Steam API"""
        try:
            # Steam inventory endpoint
            url = f"{self.steam_api_base}/{steam_id}/{app_id}/2"
            
            # Make request without problematic parameters
            response = requests.get(url, timeout=30)
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
    
    def _is_cs2_item(self, item_data: Dict) -> bool:
        """Check if item is a CS2 item (includes all relevant item types)"""
        name = item_data.get('market_hash_name', '').lower()
        item_type = item_data.get('type', '').lower()
        
        # Check for CS2 item types based on tags
        tags = item_data.get('tags', [])
        
        # Look for CS2-specific item categories
        cs2_categories = [
            'weapon',           # Weapon skins
            'knife',            # Knives
            'gloves',           # Gloves
            'agent',            # Agent skins
            'sticker',          # Stickers
            'container',        # Cases
            'tool',             # Keys, name tags, etc.
            'graffiti',         # Sprays/graffiti
            'musickit',         # Music kits
            'collectible',      # Coins, charms
            'base',             # Default items
        ]
        
        # Check tags for CS2 item types
        for tag in tags:
            tag_category = tag.get('category', '').lower()
            tag_name = tag.get('internal_name', '').lower()
            tag_localized = tag.get('localized_tag_name', '').lower()
            
            # Check if it's a CS2 item category
            if tag_category in ['type', 'itemset', 'quality', 'exterior']:
                if any(cs2_cat in tag_name or cs2_cat in tag_localized for cs2_cat in cs2_categories):
                    return True
            
            # Special checks for specific item types that might be missed
            if 'key' in tag_name or 'key' in tag_localized:
                return True
            if 'gloves' in tag_name or 'gloves' in tag_localized or 'glove' in tag_name:
                return True
        
        # Additional checks for specific item types
        cs2_item_indicators = [
            # Weapons with conditions
            'factory new', 'minimal wear', 'field-tested', 'well-worn', 'battle-scarred',
            # Weapon types
            'ak-47', 'awp', 'm4a4', 'm4a1-s', 'glock', 'usp', 'deagle', 'knife', 'karambit', 'bayonet',
            # Item types
            'sticker', 'key', 'case', 'capsule', 'music kit', 'graffiti', 'spray', 'agent',
            'charm', 'coin', 'gloves', 'pin',
            # CS2 specific terms
            'souvenir', 'stattrak', 'operation'
        ]
        
        # Check if name contains CS2 indicators
        if any(indicator in name for indicator in cs2_item_indicators):
            return True
        
        # Check item type for CS2 categories
        if any(cs2_cat in item_type for cs2_cat in cs2_categories):
            return True
        
        # Default to including items if we're unsure (better to include too many than miss items)
        return True
    
    def _process_cs2_item(self, item_data: Dict, steam_id: str, include_floats: bool = True, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Process a single CS2 inventory item with optional float data"""
        try:
            # Extract basic item info
            name = item_data.get('market_hash_name', 'Unknown Item')
            item_type = item_data.get('type', '')
            
            # Extract CS2-specific data
            rarity = self._extract_cs2_rarity(item_data)
            condition = self._extract_condition(name)
            
            # Determine item category
            item_category = self._get_item_category(item_data, name)
            
            # Get image URL
            image_url = item_data.get('icon_url', '')
            if image_url:
                image_url = f"https://community.akamai.steamstatic.com/economy/image/{image_url}"
            
            # Initialize float and pattern data
            float_value = None
            paint_seed = None
            
            # Get float data if requested and available
            if include_floats and CSFLOAT_AVAILABLE and self._has_inspect_link(item_data):
                float_data = self._get_csfloat_data(item_data)
                if float_data and float_data.success:
                    float_value = float_data.float_value
                    paint_seed = float_data.paint_seed
                    self.logger.info(f"CSFloat data for {name}: Float={float_value}, Pattern={paint_seed}")
            
            # Build the item data
            item_result = {
                'type': 'steam',
                'name': self.clean_text(name),
                'rarity': rarity,
                'condition': condition or 'N/A',
                'float_value': float_value,
                'paint_seed': paint_seed,
                'current_price': 0.0,
                'price_bought': 0.0,
                'quantity': int(item_data.get('amount', 1)),
                'game': 'Counter-Strike 2',
                'asset_id': item_data.get('assetid'),
                'image_url': image_url,
                'market_hash_name': name,
                'item_category': item_category,
                'item_type': item_type,
                'steam_id': steam_id,
                'user_id': user_id,  # Add user_id to the scraped item
                'last_updated': self.format_timestamp()
            }
            
            return item_result
            
        except Exception as e:
            self.logger.error(f"Error processing CS2 item {item_data.get('market_hash_name', 'Unknown')}: {e}")
            return None
    
    # Removed _parse_price and _estimate_float_from_condition methods - no pricing functionality
    
    def _extract_cs2_rarity(self, item_data: Dict) -> str:
        """Extract CS2 item rarity (Contraband, Covert, etc.)"""
        tags = item_data.get('tags', [])
        
        # Look for rarity tag first
        for tag in tags:
            if tag.get('category') == 'Rarity':
                rarity_name = tag.get('localized_tag_name', 'Unknown')
                rarity_internal = tag.get('internal_name', '').lower()
                
                # Standard weapon/item rarity mapping
                rarity_mapping = {
                    'contraband': 'Contraband',
                    'covert': 'Covert',
                    'classified': 'Classified', 
                    'restricted': 'Restricted',
                    'mil-spec': 'Mil-Spec',
                    'milspec': 'Mil-Spec',
                    'industrial': 'Industrial',
                    'consumer': 'Consumer',
                    # Gloves and knives
                    'extraordinary': 'Extraordinary',
                    # Agent rarities (CS2 specific)
                    'master': 'Master Agent',
                    'superior': 'Superior Agent',
                    'distinguished': 'Distinguished Agent',
                    'exceptional': 'Exceptional Agent',
                    # Other special rarities
                    'industrial grade': 'Industrial Grade',
                    'rare': 'Industrial Grade',
                    'uncommon': 'Uncommon',
                    'common': 'Common',
                    'legendary': 'Legendary',
                    'mythical': 'Mythical',
                    'immortal': 'Immortal',
                    'arcana': 'Arcana'
                }
                
                for key, value in rarity_mapping.items():
                    if key in rarity_internal or key in rarity_name.lower():
                        return value
                    
                return rarity_name
        
        # Look for quality tag as fallback
        for tag in tags:
            if tag.get('category') == 'Quality':
                quality_name = tag.get('localized_tag_name', 'Unknown')
                quality_internal = tag.get('internal_name', '').lower()
                
                quality_mapping = {
                    'normal': 'Normal',
                    'genuine': 'Genuine',
                    'vintage': 'Vintage',
                    'unusual': 'Unusual',
                    'unique': 'Unique',
                    'strange': 'Strange',
                    'haunted': 'Haunted',
                    'collectors': 'Collector\'s',
                    'decorated': 'Decorated'
                }
                
                for key, value in quality_mapping.items():
                    if key in quality_internal or key in quality_name.lower():
                        return value
                        
                return quality_name
        
        return 'Unknown'
    
    def _extract_condition(self, name: str) -> Optional[str]:
        """Extract condition/wear from item name"""
        conditions = {
            'Factory New': 'FN',
            'Minimal Wear': 'MW', 
            'Field-Tested': 'FT',
            'Well-Worn': 'WW',
            'Battle-Scarred': 'BS'
        }
        
        for full_name, short_name in conditions.items():
            if full_name in name:
                return short_name
        
        return None
    
    def _cleanup(self):
        """Clean up WebDriver resources"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error during driver cleanup: {e}")
        
        # Clean up CSFloat scraper if it exists
        if hasattr(self, 'csfloat_scraper') and self.csfloat_scraper is not None:
            try:
                self.csfloat_scraper._cleanup()
            except Exception as e:
                self.logger.warning(f"Error during CSFloat scraper cleanup: {e}")
    
    def _has_inspect_link(self, item_data: Dict) -> bool:
        """Check if the item has an inspect link available"""
        actions = item_data.get('actions', [])
        for action in actions:
            if 'inspect' in action.get('name', '').lower():
                return True
        return False
    
    def _get_inspect_link(self, item_data: Dict) -> Optional[str]:
        """Extract inspect link from item actions"""
        actions = item_data.get('actions', [])
        for action in actions:
            if 'inspect' in action.get('name', '').lower():
                return action.get('link', '')
        return None
    
    def _get_csfloat_data(self, item_data: Dict) -> Optional[Any]:
        """Get float and pattern data from CSFloat"""
        if not CSFLOAT_AVAILABLE:
            self.logger.warning("CSFloat scraper not available")
            return None
        
        inspect_link = self._get_inspect_link(item_data)
        if not inspect_link:
            self.logger.debug(f"No inspect link found for item: {item_data.get('market_hash_name', 'Unknown')}")
            return None
        
        try:
            # Create CSFloat scraper instance (will reuse driver if possible)
            if not hasattr(self, 'csfloat_scraper') or self.csfloat_scraper is None:
                self.csfloat_scraper = CSFloatScraper(headless=self.headless)
            
            # Get float data
            float_data = self.csfloat_scraper.get_float_data(inspect_link)
            return float_data
            
        except Exception as e:
            self.logger.error(f"Error getting CSFloat data: {e}")
            return None
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self._cleanup()
    
    def _get_item_category(self, item_data: Dict, name: str) -> str:
        """Determine the category of a CS2 item"""
        name_lower = name.lower()
        item_type = item_data.get('type', '').lower()
        
        # Check tags for more accurate categorization
        tags = item_data.get('tags', [])
        for tag in tags:
            tag_category = tag.get('category', '').lower()
            tag_name = tag.get('internal_name', '').lower()
            tag_localized = tag.get('localized_tag_name', '').lower()
            
            # Direct category matches
            if 'weapon' in tag_name or 'weapon' in tag_localized:
                return 'weapon'
            elif 'knife' in tag_name or 'knife' in tag_localized:
                return 'knife'
            elif 'gloves' in tag_name or 'gloves' in tag_localized:
                return 'gloves'
            elif 'agent' in tag_name or 'agent' in tag_localized:
                return 'agent'
            elif 'sticker' in tag_name or 'sticker' in tag_localized:
                return 'sticker'
            elif 'container' in tag_name or 'container' in tag_localized:
                return 'case'
            elif 'tool' in tag_name or 'tool' in tag_localized:
                if 'key' in name_lower:
                    return 'key'
                elif 'charm' in name_lower:
                    return 'charm'
                return 'tool'
            elif 'graffiti' in tag_name or 'graffiti' in tag_localized:
                return 'spray'
            elif 'musickit' in tag_name or 'music kit' in tag_localized:
                return 'music_kit'
            elif 'collectible' in tag_name or 'collectible' in tag_localized:
                if 'coin' in name_lower:
                    return 'coin'
                elif 'charm' in name_lower:
                    return 'charm'
                elif 'pin' in name_lower:
                    return 'pin'
                return 'collectible'
            elif 'patch' in tag_name or 'patch' in tag_localized:
                return 'patch'
        
        # Enhanced fallback to name-based detection with all categories
        if 'knife' in name_lower or 'karambit' in name_lower or 'bayonet' in name_lower:
            return 'knife'
        elif 'gloves' in name_lower or 'glove' in name_lower or 'wraps' in name_lower:
            return 'gloves'
        elif 'sticker' in name_lower:
            return 'sticker'
        elif 'case' in name_lower and ('weapon case' in name_lower or 'container' in name_lower):
            return 'case'
        elif 'capsule' in name_lower:
            if 'sticker capsule' in name_lower:
                return 'sticker_capsule'
            elif 'autograph capsule' in name_lower:
                return 'autograph_capsule'
            elif 'collectible capsule' in name_lower:
                return 'collectible_capsule'
            return 'capsule'
        elif 'souvenir package' in name_lower:
            return 'souvenir_package'
        elif 'collection package' in name_lower:
            return 'collection_package'
        elif 'patch pack' in name_lower:
            return 'patch_pack'
        elif 'graffiti box' in name_lower:
            return 'graffiti_box'
        elif 'music kit box' in name_lower:
            return 'music_kit_box'
        elif 'key' in name_lower or ' key' in name_lower:
            return 'key'
        elif 'music kit' in name_lower:
            return 'music_kit'
        elif 'graffiti' in name_lower or 'spray' in name_lower:
            return 'spray'
        elif 'agent' in name_lower:
            return 'agent'
        elif 'coin' in name_lower:
            return 'coin'
        elif 'charm' in name_lower:
            return 'charm'
        elif 'patch' in name_lower:
            return 'patch'
        elif 'pin' in name_lower:
            return 'pin'
        elif 'pass' in name_lower:
            return 'pass'
        elif 'gift' in name_lower:
            return 'gift'
        elif 'collectible' in name_lower:
            return 'collectible'
        elif 'tag' in name_lower:
            return 'tag'
        elif any(weapon in name_lower for weapon in ['ak-47', 'awp', 'm4a4', 'm4a1-s', 'glock', 'usp', 'deagle']):
            return 'weapon'
        
        return 'unknown'
    
    # Removed _estimate_float_from_condition method - no float estimation

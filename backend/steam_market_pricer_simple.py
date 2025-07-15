#!/usr/bin/env python3
"""
Simplified Steam Market Pricing Service - No Pricing Logic
"""

from typing import Optional, Dict, Any

class SteamMarketPricer:
    """Simplified Steam Market Pricer without actual pricing functionality"""
    
    def __init__(self):
        self.enabled = False  # Disable pricing functionality
    
    def get_item_price(self, item_name: str, currency: str = 'USD', appid: int = 730) -> Optional[Dict[str, Any]]:
        """
        Simplified method that returns None (no pricing)
        
        Args:
            item_name: Market hash name of the item
            currency: Currency code (USD, EUR, etc.)
            appid: Steam app ID (730 for CS2)
            
        Returns:
            None (no pricing data)
        """
        # Return None to indicate no pricing available
        return None
    
    def get_multiple_prices(self, item_names: list, currency: str = 'USD', appid: int = 730) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Simplified method that returns empty pricing for multiple items
        
        Args:
            item_names: List of market hash names
            currency: Currency code
            appid: Steam app ID
            
        Returns:
            Dict mapping item names to None
        """
        return {name: None for name in item_names}

# Create a global instance for backward compatibility
steam_pricer = SteamMarketPricer()

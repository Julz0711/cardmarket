"""
Cryptocurrency Scraper
Handles scraping of cryptocurrency data from various crypto APIs
"""

from typing import List, Dict, Any, Optional
import requests
import json
import time

from .base_scraper import BaseScraper, ScraperError, ValidationError


class CryptocurrencyScraper(BaseScraper):
    """Scraper for cryptocurrency market data"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("Cryptocurrency")
        self.api_key = api_key
        self.coinmarketcap_base = "https://pro-api.coinmarketcap.com/v1"
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters for crypto scraping"""
        required_fields = ['symbols']
        
        for field in required_fields:
            if field not in kwargs:
                raise ValidationError(f"Missing required field: {field}")
        
        symbols = kwargs.get('symbols')
        
        if not symbols or not isinstance(symbols, list) or len(symbols) == 0:
            raise ValidationError("Symbols must be a non-empty list")
        
        # Validate symbol format
        for symbol in symbols:
            if not isinstance(symbol, str) or len(symbol) < 1:
                raise ValidationError(f"Invalid symbol: {symbol}")
        
        return True
    
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape cryptocurrency market data
        
        Args:
            symbols (List[str]): List of crypto symbols to scrape (e.g., ['BTC', 'ETH'])
            
        Returns:
            List of cryptocurrency dictionaries
        """
        self.validate_input(**kwargs)
        self.log_scraping_start(**kwargs)
        
        symbols = kwargs['symbols']
        
        cryptos = []
        
        try:
            # Try CoinGecko first (free API)
            crypto_data = self._get_coingecko_data(symbols)
            
            if not crypto_data and self.api_key:
                # Fallback to CoinMarketCap if API key is available
                crypto_data = self._get_coinmarketcap_data(symbols)
            
            for crypto in crypto_data:
                try:
                    processed_crypto = self._process_crypto_data(crypto)
                    if processed_crypto:
                        cryptos.append(processed_crypto)
                        self.logger.info(f"Successfully scraped crypto: {crypto.get('symbol', 'Unknown')}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing crypto data: {e}")
                    continue
            
            self.log_scraping_complete(len(cryptos))
            return cryptos
            
        except Exception as e:
            self.log_error(e)
            raise ScraperError(f"Cryptocurrency scraping failed: {e}")
    
    def _get_coingecko_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get cryptocurrency data from CoinGecko API"""
        try:
            # Convert symbols to CoinGecko IDs
            crypto_ids = self._symbols_to_coingecko_ids(symbols)
            
            if not crypto_ids:
                return []
            
            # CoinGecko coins endpoint
            url = f"{self.coingecko_base}/coins/markets"
            params = {
                'vs_currency': 'eur',
                'ids': ','.join(crypto_ids),
                'order': 'market_cap_desc',
                'per_page': 250,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Add source information
            for item in data:
                item['data_source'] = 'coingecko'
            
            return data
            
        except requests.RequestException as e:
            self.logger.error(f"CoinGecko request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"CoinGecko data parsing failed: {e}")
            return []
    
    def _symbols_to_coingecko_ids(self, symbols: List[str]) -> List[str]:
        """Convert crypto symbols to CoinGecko IDs"""
        try:
            # Common symbol to ID mappings
            symbol_to_id = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'SOL': 'solana',
                'MATIC': 'polygon',
                'AVAX': 'avalanche-2',
                'ATOM': 'cosmos',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'LTC': 'litecoin',
                'BCH': 'bitcoin-cash',
                'XRP': 'ripple',
                'DOGE': 'dogecoin',
                'SHIB': 'shiba-inu'
            }
            
            # Get IDs for known symbols
            crypto_ids = []
            unknown_symbols = []
            
            for symbol in symbols:
                symbol_upper = symbol.upper()
                if symbol_upper in symbol_to_id:
                    crypto_ids.append(symbol_to_id[symbol_upper])
                else:
                    unknown_symbols.append(symbol)
            
            # For unknown symbols, try to fetch from CoinGecko coins list
            if unknown_symbols:
                additional_ids = self._resolve_unknown_symbols(unknown_symbols)
                crypto_ids.extend(additional_ids)
            
            return crypto_ids
            
        except Exception as e:
            self.logger.warning(f"Error converting symbols to IDs: {e}")
            return []
    
    def _resolve_unknown_symbols(self, symbols: List[str]) -> List[str]:
        """Resolve unknown symbols using CoinGecko coins list"""
        try:
            # Get coins list from CoinGecko
            url = f"{self.coingecko_base}/coins/list"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            coins_list = response.json()
            
            # Create symbol to ID mapping
            resolved_ids = []
            for symbol in symbols:
                for coin in coins_list:
                    if coin.get('symbol', '').upper() == symbol.upper():
                        resolved_ids.append(coin['id'])
                        break
            
            return resolved_ids
            
        except Exception as e:
            self.logger.warning(f"Could not resolve unknown symbols: {e}")
            return []
    
    def _get_coinmarketcap_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get cryptocurrency data from CoinMarketCap API"""
        if not self.api_key:
            self.logger.warning("CoinMarketCap API key not provided")
            return []
        
        try:
            # CoinMarketCap quotes endpoint
            url = f"{self.coinmarketcap_base}/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json'
            }
            params = {
                'symbol': ','.join(symbols),
                'convert': 'EUR'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status', {}).get('error_code') != 0:
                raise ScraperError(f"CoinMarketCap error: {data.get('status', {}).get('error_message')}")
            
            # Convert to list format
            crypto_list = []
            for symbol, crypto_data in data.get('data', {}).items():
                crypto_data['data_source'] = 'coinmarketcap'
                crypto_list.append(crypto_data)
            
            return crypto_list
            
        except requests.RequestException as e:
            self.logger.error(f"CoinMarketCap request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"CoinMarketCap data parsing failed: {e}")
            return []
    
    def _process_crypto_data(self, crypto_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process cryptocurrency data from API response"""
        try:
            data_source = crypto_data.get('data_source', 'unknown')
            
            if data_source == 'coingecko':
                return self._process_coingecko_data(crypto_data)
            elif data_source == 'coinmarketcap':
                return self._process_coinmarketcap_data(crypto_data)
            else:
                self.logger.warning(f"Unknown data source: {data_source}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing crypto data: {e}")
            return None
    
    def _process_coingecko_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process CoinGecko API data"""
        return {
            'type': 'crypto',
            'symbol': data.get('symbol', '').upper(),
            'name': data.get('name', 'Unknown'),
            'current_price': data.get('current_price', 0.0),
            'market_cap': data.get('market_cap'),
            'volume_24h': data.get('total_volume'),
            'change_24h': data.get('price_change_percentage_24h'),
            'rank': data.get('market_cap_rank'),
            'quantity': 1,  # Default quantity
            'price_bought': 0.0,  # To be set by user
            'last_updated': self.format_timestamp()
        }
    
    def _process_coinmarketcap_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process CoinMarketCap API data"""
        quote = data.get('quote', {}).get('EUR', {})
        
        return {
            'type': 'crypto',
            'symbol': data.get('symbol', '').upper(),
            'name': data.get('name', 'Unknown'),
            'current_price': quote.get('price', 0.0),
            'market_cap': quote.get('market_cap'),
            'volume_24h': quote.get('volume_24h'),
            'change_24h': quote.get('percent_change_24h'),
            'rank': data.get('cmc_rank'),
            'quantity': 1,  # Default quantity
            'price_bought': 0.0,  # To be set by user
            'last_updated': self.format_timestamp()
        }

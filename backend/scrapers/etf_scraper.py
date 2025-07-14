"""
ETF Scraper
Handles scraping of ETF (Exchange-Traded Fund) data from various financial APIs
"""

from typing import List, Dict, Any, Optional
import requests
import json
import time

from .base_scraper import BaseScraper, ScraperError, ValidationError


class ETFScraper(BaseScraper):
    """Scraper for ETF market data"""
    
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        super().__init__("ETF")
        self.alpha_vantage_key = alpha_vantage_key
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        # Yahoo Finance doesn't require API key
        self.yahoo_base = "https://query1.finance.yahoo.com/v8/finance/chart"
        
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters for ETF scraping"""
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
        Scrape ETF market data
        
        Args:
            symbols (List[str]): List of ETF symbols to scrape (e.g., ['MSCI', 'SPY'])
            
        Returns:
            List of ETF dictionaries
        """
        self.validate_input(**kwargs)
        self.log_scraping_start(**kwargs)
        
        symbols = kwargs['symbols']
        
        etfs = []
        
        try:
            for symbol in symbols:
                try:
                    # Add .DE suffix for German ETFs if not present
                    etf_symbol = self._format_etf_symbol(symbol)
                    
                    # Try Yahoo Finance first (free)
                    etf_data = self._get_yahoo_data(etf_symbol)
                    
                    if not etf_data and self.alpha_vantage_key:
                        # Fallback to Alpha Vantage
                        etf_data = self._get_alpha_vantage_data(symbol)
                    
                    if etf_data:
                        processed_etf = self._process_etf_data(etf_data, symbol)
                        if processed_etf:
                            etfs.append(processed_etf)
                            self.logger.info(f"Successfully scraped ETF: {symbol}")
                    else:
                        self.logger.warning(f"No data found for ETF: {symbol}")
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error scraping ETF {symbol}: {e}")
                    continue
            
            self.log_scraping_complete(len(etfs))
            return etfs
            
        except Exception as e:
            self.log_error(e)
            raise ScraperError(f"ETF scraping failed: {e}")
    
    def _format_etf_symbol(self, symbol: str) -> str:
        """Format ETF symbol for different exchanges"""
        symbol = symbol.strip().upper()
        
        # Common ETF symbols and their exchanges
        german_etfs = [
            'LYXOR', 'ISHARES', 'VANGUARD', 'XTRACKERS', 'AMUNDI',
            'MSCI', 'FTSE', 'DAX', 'EURO', 'STOXX'
        ]
        
        # Check if it's likely a German ETF and add .DE suffix
        if any(german_etf in symbol for german_etf in german_etfs):
            if not symbol.endswith('.DE'):
                symbol += '.DE'
        # Check if it's likely a US ETF and add no suffix or .US
        elif not '.' in symbol:
            # Keep as is for US ETFs (Yahoo Finance handles them without suffix)
            pass
            
        return symbol
    
    def _get_yahoo_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ETF data from Yahoo Finance"""
        try:
            # Yahoo Finance chart API
            url = f"{self.yahoo_base}/{symbol}"
            params = {
                'period1': 0,
                'period2': int(time.time()),
                'interval': '1d',
                'includePrePost': True,
                'events': 'div,splits'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or not data['chart'].get('result'):
                return None
            
            chart_data = data['chart']['result'][0]
            meta = chart_data.get('meta', {})
            
            # Get additional data from Yahoo Finance quote API
            quote_data = self._get_yahoo_quote(symbol)
            
            result = {
                'symbol': symbol,
                'data_source': 'yahoo',
                'meta': meta,
                'quote': quote_data
            }
            
            return result
            
        except requests.RequestException as e:
            self.logger.error(f"Yahoo Finance request failed for {symbol}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Yahoo Finance data parsing failed for {symbol}: {e}")
            return None
    
    def _get_yahoo_quote(self, symbol: str) -> Dict[str, Any]:
        """Get additional quote data from Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/quote"
            params = {'symbols': symbol}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'quoteResponse' in data and data['quoteResponse'].get('result'):
                return data['quoteResponse']['result'][0]
            
            return {}
            
        except Exception as e:
            self.logger.warning(f"Could not get Yahoo quote data for {symbol}: {e}")
            return {}
    
    def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ETF data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
        
        try:
            # Alpha Vantage Global Quote endpoint
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(self.alpha_vantage_base, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Global Quote' not in data:
                return None
            
            result = {
                'symbol': symbol,
                'data_source': 'alpha_vantage',
                'global_quote': data['Global Quote']
            }
            
            return result
            
        except requests.RequestException as e:
            self.logger.error(f"Alpha Vantage request failed for {symbol}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Alpha Vantage data parsing failed for {symbol}: {e}")
            return None
    
    def _process_etf_data(self, etf_data: Dict[str, Any], original_symbol: str) -> Optional[Dict[str, Any]]:
        """Process ETF data from API response"""
        try:
            data_source = etf_data.get('data_source', 'unknown')
            
            if data_source == 'yahoo':
                return self._process_yahoo_data(etf_data, original_symbol)
            elif data_source == 'alpha_vantage':
                return self._process_alpha_vantage_data(etf_data, original_symbol)
            else:
                self.logger.warning(f"Unknown data source: {data_source}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing ETF data: {e}")
            return None
    
    def _process_yahoo_data(self, data: Dict[str, Any], original_symbol: str) -> Dict[str, Any]:
        """Process Yahoo Finance API data"""
        meta = data.get('meta', {})
        quote = data.get('quote', {})
        
        # Extract price information
        current_price = meta.get('regularMarketPrice') or quote.get('regularMarketPrice', 0.0)
        previous_close = meta.get('previousClose') or quote.get('previousClose', 0.0)
        
        # Calculate change
        change = current_price - previous_close if current_price and previous_close else 0.0
        change_percent = (change / previous_close * 100) if previous_close else 0.0
        
        return {
            'type': 'etf',
            'symbol': original_symbol,
            'name': quote.get('longName') or quote.get('shortName') or meta.get('symbol', original_symbol),
            'current_price': current_price,
            'previous_close': previous_close,
            'change': change,
            'change_percent': change_percent,
            'volume': quote.get('regularMarketVolume') or meta.get('regularMarketVolume'),
            'market_cap': quote.get('marketCap'),
            'expense_ratio': quote.get('expenseRatio'),
            'yield': quote.get('yield'),
            'currency': meta.get('currency', 'EUR'),
            'exchange': meta.get('exchangeName') or quote.get('fullExchangeName'),
            'quantity': 1,  # Default quantity
            'price_bought': 0.0,  # To be set by user
            'last_updated': self.format_timestamp()
        }
    
    def _process_alpha_vantage_data(self, data: Dict[str, Any], original_symbol: str) -> Dict[str, Any]:
        """Process Alpha Vantage API data"""
        global_quote = data.get('global_quote', {})
        
        current_price = self.clean_price(global_quote.get('05. price', '0'))
        previous_close = self.clean_price(global_quote.get('08. previous close', '0'))
        change = self.clean_price(global_quote.get('09. change', '0'))
        change_percent = self.clean_price(global_quote.get('10. change percent', '0').replace('%', ''))
        
        return {
            'type': 'etf',
            'symbol': original_symbol,
            'name': global_quote.get('01. symbol', original_symbol),
            'current_price': current_price,
            'previous_close': previous_close,
            'change': change,
            'change_percent': change_percent,
            'volume': int(global_quote.get('06. volume', 0)),
            'market_cap': None,  # Not available in Global Quote
            'expense_ratio': None,
            'yield': None,
            'currency': 'EUR',  # Assumed
            'exchange': None,
            'quantity': 1,  # Default quantity
            'price_bought': 0.0,  # To be set by user
            'last_updated': self.format_timestamp()
        }

"""
Stock Data Scraper
Handles scraping of stock market data from various financial APIs
"""

from typing import List, Dict, Any, Optional
import requests
import json
import time

from .base_scraper import BaseScraper, ScraperError, ValidationError


class StocksScraper(BaseScraper):
    """Scraper for stock market data"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("Stocks")
        self.api_key = api_key
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        self.yahoo_finance_base = "https://query1.finance.yahoo.com/v8/finance/chart"
        
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters for stock scraping"""
        required_fields = ['symbols']
        
        for field in required_fields:
            if field not in kwargs:
                raise ValidationError(f"Missing required field: {field}")
        
        symbols = kwargs.get('symbols')
        market = kwargs.get('market', 'NYSE')
        
        if not symbols or not isinstance(symbols, list) or len(symbols) == 0:
            raise ValidationError("Symbols must be a non-empty list")
        
        # Validate symbol format
        for symbol in symbols:
            if not isinstance(symbol, str) or len(symbol) < 1:
                raise ValidationError(f"Invalid symbol: {symbol}")
        
        return True
    
    def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape stock market data
        
        Args:
            symbols (List[str]): List of stock symbols to scrape
            market (str): Market/exchange name (default: NYSE)
            
        Returns:
            List of stock dictionaries
        """
        self.validate_input(**kwargs)
        self.log_scraping_start(**kwargs)
        
        symbols = kwargs['symbols']
        market = kwargs.get('market', 'NYSE')
        
        stocks = []
        
        try:
            for symbol in symbols:
                try:
                    stock_data = self._scrape_single_stock(symbol, market)
                    if stock_data:
                        stocks.append(stock_data)
                        self.logger.info(f"Successfully scraped stock: {symbol}")
                    else:
                        self.logger.warning(f"No data found for stock: {symbol}")
                        
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    self.logger.error(f"Error scraping stock {symbol}: {e}")
                    continue
            
            self.log_scraping_complete(len(stocks))
            return stocks
            
        except Exception as e:
            self.log_error(e)
            raise ScraperError(f"Stock scraping failed: {e}")
    
    def _scrape_single_stock(self, symbol: str, market: str) -> Optional[Dict[str, Any]]:
        """Scrape data for a single stock"""
        try:
            # Try Yahoo Finance first (free)
            stock_data = self._get_yahoo_finance_data(symbol)
            
            if not stock_data and self.api_key:
                # Fallback to Alpha Vantage if API key is available
                stock_data = self._get_alpha_vantage_data(symbol)
            
            if stock_data:
                # Add additional metadata
                stock_data.update({
                    'type': 'stocks',
                    'market': market,
                    'quantity': 1,  # Default quantity
                    'price_bought': 0.0,  # To be set by user
                    'last_updated': self.format_timestamp()
                })
                
                return stock_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping stock {symbol}: {e}")
            return None
    
    def _get_yahoo_finance_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data from Yahoo Finance API"""
        try:
            # Yahoo Finance chart API
            url = f"{self.yahoo_finance_base}/{symbol}"
            params = {
                'interval': '1d',
                'range': '1d'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('chart', {}).get('error'):
                raise ScraperError(f"Yahoo Finance API error: {data['chart']['error']}")
            
            result = data['chart']['result'][0]
            meta = result['meta']
            
            # Extract stock information
            current_price = meta.get('regularMarketPrice', 0.0)
            company_name = meta.get('longName', symbol)
            currency = meta.get('currency', 'USD')
            exchange = meta.get('exchangeName', 'Unknown')
            
            # Try to get additional company info
            company_info = self._get_company_info_yahoo(symbol)
            
            return {
                'symbol': symbol.upper(),
                'name': company_name,
                'company': company_name,
                'current_price': current_price,
                'currency': currency,
                'sector': company_info.get('sector', 'Unknown'),
                'market': exchange,
                'dividend_yield': company_info.get('dividend_yield'),
                'market_cap': company_info.get('market_cap')
            }
            
        except requests.RequestException as e:
            self.logger.error(f"Yahoo Finance request failed for {symbol}: {e}")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.logger.error(f"Yahoo Finance data parsing failed for {symbol}: {e}")
            return None
    
    def _get_company_info_yahoo(self, symbol: str) -> Dict[str, Any]:
        """Get additional company information from Yahoo Finance"""
        try:
            # Yahoo Finance summary API
            url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            params = {
                'modules': 'summaryProfile,defaultKeyStatistics,financialData'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('quoteSummary', {}).get('error'):
                return {}
            
            result = data['quoteSummary']['result'][0]
            
            # Extract additional info
            profile = result.get('summaryProfile', {})
            key_stats = result.get('defaultKeyStatistics', {})
            financial = result.get('financialData', {})
            
            return {
                'sector': profile.get('sector', 'Unknown'),
                'industry': profile.get('industry', 'Unknown'),
                'dividend_yield': key_stats.get('dividendYield', {}).get('raw'),
                'market_cap': key_stats.get('marketCap', {}).get('raw'),
                'pe_ratio': key_stats.get('trailingPE', {}).get('raw'),
                'revenue_growth': financial.get('revenueGrowth', {}).get('raw')
            }
            
        except Exception as e:
            self.logger.warning(f"Could not get additional info for {symbol}: {e}")
            return {}
    
    def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data from Alpha Vantage API"""
        if not self.api_key:
            self.logger.warning("Alpha Vantage API key not provided")
            return None
        
        try:
            # Alpha Vantage Global Quote endpoint
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.alpha_vantage_base, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                raise ScraperError(f"Alpha Vantage error: {data['Error Message']}")
            
            if 'Note' in data:
                raise ScraperError("Alpha Vantage API call frequency limit reached")
            
            quote = data.get('Global Quote', {})
            
            if not quote:
                return None
            
            # Get company overview for additional data
            company_data = self._get_alpha_vantage_overview(symbol)
            
            return {
                'symbol': symbol.upper(),
                'name': company_data.get('Name', symbol),
                'company': company_data.get('Name', symbol),
                'current_price': float(quote.get('05. price', 0)),
                'sector': company_data.get('Sector', 'Unknown'),
                'market': company_data.get('Exchange', 'Unknown'),
                'dividend_yield': self._safe_float(company_data.get('DividendYield')),
                'market_cap': self._safe_float(company_data.get('MarketCapitalization'))
            }
            
        except requests.RequestException as e:
            self.logger.error(f"Alpha Vantage request failed for {symbol}: {e}")
            return None
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            self.logger.error(f"Alpha Vantage data parsing failed for {symbol}: {e}")
            return None
    
    def _get_alpha_vantage_overview(self, symbol: str) -> Dict[str, Any]:
        """Get company overview from Alpha Vantage"""
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.alpha_vantage_base, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data or 'Note' in data:
                return {}
            
            return data
            
        except Exception as e:
            self.logger.warning(f"Could not get overview for {symbol}: {e}")
            return {}
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == 'None':
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import logging
import os

# Import the new modular scrapers
from scrapers import ScraperManager, ScraperError, ValidationError

# Flask app configuration
app = Flask(__name__)
CORS(app)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scraper manager with API keys from environment variables
api_keys = {
    'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
    'coinmarketcap': os.getenv('COINMARKETCAP_API_KEY'),
    'steam': os.getenv('STEAM_API_KEY')
}

# Remove None values
api_keys = {k: v for k, v in api_keys.items() if v is not None}

scraper_manager = ScraperManager(api_keys=api_keys)

# API Routes
@app.route('/api/scrapers/status', methods=['GET'])
def get_scrapers_status():
    """Get status of all available scrapers"""
    try:
        status = scraper_manager.get_scraper_status()
        supported_assets = scraper_manager.get_supported_assets()
        config_issues = scraper_manager.validate_scraper_config()
        
        return jsonify({
            'status': 'success',
            'scrapers': status,
            'supported_assets': supported_assets,
            'config_issues': config_issues
        })
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scrapers/available', methods=['GET'])
def get_available_scrapers():
    """Get list of available scraper types"""
    try:
        scrapers = scraper_manager.get_available_scrapers()
        return jsonify({
            'status': 'success',
            'scrapers': scrapers
        })
    except Exception as e:
        logger.error(f"Error getting available scrapers: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scrape/cards', methods=['POST'])
def scrape_trading_cards():
    """Scrape trading cards from CardMarket"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        expansion = data.get('expansion')
        number_from = data.get('number_from')
        number_to = data.get('number_to')
        
        if not all([expansion, number_from is not None, number_to is not None]):
            return jsonify({
                'status': 'error', 
                'message': 'Missing required fields: expansion, number_from, number_to'
            }), 400
        
        cards = scraper_manager.scrape_trading_cards(expansion, number_from, number_to)
        
        return jsonify({
            'status': 'success',
            'data': cards,
            'count': len(cards)
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in cards scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except ScraperError as e:
        logger.error(f"Scraper error in cards scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in cards scraping: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/scrape/stocks', methods=['POST'])
def scrape_stocks():
    """Scrape stock market data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        symbols = data.get('symbols')
        
        if not symbols or not isinstance(symbols, list):
            return jsonify({
                'status': 'error', 
                'message': 'Missing or invalid symbols field (must be array)'
            }), 400
        
        stocks = scraper_manager.scrape_stocks(symbols)
        
        return jsonify({
            'status': 'success',
            'data': stocks,
            'count': len(stocks)
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in stocks scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except ScraperError as e:
        logger.error(f"Scraper error in stocks scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in stocks scraping: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/scrape/etf', methods=['POST'])
def scrape_etfs():
    """Scrape ETF market data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        symbols = data.get('symbols')
        
        if not symbols or not isinstance(symbols, list):
            return jsonify({
                'status': 'error', 
                'message': 'Missing or invalid symbols field (must be array)'
            }), 400
        
        etfs = scraper_manager.scrape_etfs(symbols)
        
        return jsonify({
            'status': 'success',
            'data': etfs,
            'count': len(etfs)
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in ETF scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except ScraperError as e:
        logger.error(f"Scraper error in ETF scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in ETF scraping: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/scrape/crypto', methods=['POST'])
def scrape_cryptocurrency():
    """Scrape cryptocurrency market data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        symbols = data.get('symbols')
        
        if not symbols or not isinstance(symbols, list):
            return jsonify({
                'status': 'error', 
                'message': 'Missing or invalid symbols field (must be array)'
            }), 400
        
        cryptos = scraper_manager.scrape_cryptocurrency(symbols)
        
        return jsonify({
            'status': 'success',
            'data': cryptos,
            'count': len(cryptos)
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in crypto scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except ScraperError as e:
        logger.error(f"Scraper error in crypto scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in crypto scraping: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/scrape/steam', methods=['POST'])
def scrape_steam_inventory():
    """Scrape Steam inventory data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        steam_id = data.get('steam_id')
        
        if not steam_id:
            return jsonify({
                'status': 'error', 
                'message': 'Missing required field: steam_id'
            }), 400
        
        steam_items = scraper_manager.scrape_steam_inventory(steam_id)
        
        return jsonify({
            'status': 'success',
            'data': steam_items,
            'count': len(steam_items)
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in Steam scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except ScraperError as e:
        logger.error(f"Scraper error in Steam scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in Steam scraping: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """Get portfolio summary across all asset types"""
    try:
        # This would typically come from a database
        # For now, return a mock summary structure
        summary = {
            'total_value': 0.0,
            'total_cost': 0.0,
            'total_gain_loss': 0.0,
            'total_gain_loss_percent': 0.0,
            'asset_breakdown': {
                'cards': {'value': 0.0, 'count': 0},
                'stocks': {'value': 0.0, 'count': 0},
                'etf': {'value': 0.0, 'count': 0},
                'crypto': {'value': 0.0, 'count': 0},
                'steam': {'value': 0.0, 'count': 0}
            },
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Portfolio Manager API is running',
        'timestamp': datetime.now().isoformat(),
        'available_scrapers': scraper_manager.get_available_scrapers()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Portfolio Manager API...")
    logger.info(f"Available scrapers: {scraper_manager.get_available_scrapers()}")
    
    # Log configuration status
    config_issues = scraper_manager.validate_scraper_config()
    if config_issues['warnings']:
        logger.warning("Configuration warnings:")
        for warning in config_issues['warnings']:
            logger.warning(f"  - {warning}")
    
    if config_issues['errors']:
        logger.error("Configuration errors:")
        for error in config_issues['errors']:
            logger.error(f"  - {error}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

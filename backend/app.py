
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Import the new modular scrapers
from scrapers import ScraperManager, ScraperError, ValidationError

# Import MongoDB database models
from database import mongodb, card_model, steam_item_model, financial_asset_model

# Import yfinance service
from yfinance_service import yfinance_service

# Import authentication system
from auth import user_model, auth_required, JWTManager

# Load environment variables
load_dotenv()

# Flask app configuration

app = Flask(__name__)

# Allowed origins for CORS
ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174').split(',')


# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url}")
    if request.data:
        logger.info(f"Request data: {request.data}")

# Handle CORS preflight requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        origin = request.headers.get('Origin')
        if origin and origin in ALLOWED_ORIGINS:
            response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin and origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Accept,X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scraper manager
api_keys = {
    # Using CSGOSkins.gg and other services for pricing
}
scraper_manager = ScraperManager(api_keys=api_keys)

# Helper function to check MongoDB availability
def mongodb_required():
    if card_model is None:
        return jsonify({
            'error': 'MongoDB not available. Please set up MongoDB Atlas or install MongoDB locally.',
            'setup_instructions': {
                'atlas': 'Visit https://cloud.mongodb.com to create a free cluster',
                'local': 'Install MongoDB locally and ensure it\'s running on localhost:27017'
            }
        }), 503
    return None

# API Routes
@app.route('/api/scrapers/status', methods=['GET'])
@auth_required  # ADDED: Require authentication for scraper status
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
@auth_required  # ADDED: Require authentication for available scrapers
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
@auth_required  # ADDED: Require authentication for card scraping
def scrape_trading_cards():
    """Scrape trading cards from CardMarket"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        tcg = data.get('tcg', 'Pokemon')  # Default to Pokemon
        expansion = data.get('expansion')
        numbers = data.get('numbers', [])
        card_language = data.get('language', 'Western')  # Default to Western language
        headless = data.get('headless', True)  # Default to headless mode
        
        if not expansion:
            return jsonify({
                'status': 'error', 
                'message': 'Missing required field: expansion'
            }), 400
            
        if not numbers or not isinstance(numbers, list) or len(numbers) == 0:
            return jsonify({
                'status': 'error', 
                'message': 'Missing required field: numbers (must be a non-empty list)'
            }), 400
          # Convert to integers if they're strings
        try:
            numbers = [int(n) for n in numbers]
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error', 
                'message': 'Invalid card numbers - must be integers'
            }), 400
        
        # Check for existing cards and filter out duplicates
        user_id = request.current_user['user_id']
        existing_cards = []
        numbers_to_scrape = []
        
        for number in numbers:
            existing_card = card_model.find_existing_card(user_id, tcg, expansion, number, card_language)
            if existing_card:
                existing_cards.append({
                    'number': number,
                    'name': existing_card.get('name', f'Card #{number}'),
                    'message': 'Already exists in collection'
                })
                logger.info(f"Skipping card #{number} - already exists in collection")
            else:
                numbers_to_scrape.append(number)
        
        # If no new cards to scrape, return early
        if not numbers_to_scrape:
            return jsonify({
                'message': 'All requested cards already exist in your collection',
                'skipped_cards': existing_cards,
                'scraped_cards': [],
                'total_cards': len(card_model.get_cards(user_id=user_id))
            })

        # Call the scraper directly with the correct parameters including headless
        scraped_cards_data = scraper_manager.scrape_assets('cards', tcg=tcg, expansion=expansion, numbers=numbers_to_scrape, card_language=card_language, headless=headless)
        
        # Save scraped cards to MongoDB
        scraped_cards = []
        
        for card_info in scraped_cards_data:
            # Prepare card data for MongoDB
            card_data = {
                'user_id': request.current_user['user_id'],  # Use authenticated user's ID
                'type': 'cards',
                'tcg': card_info['tcg'],
                'expansion': card_info['expansion'],
                'card_language': card_info['card_language'],  # Ensure 'card_language' is used consistently
                'number': int(card_info['number']),
                'name': card_info['name'],
                'rarity': card_info['rarity'],
                'supply': int(card_info['supply']),
                'quantity': 1,  # Default to owning 1 card
                'current_price': float(card_info['current_price']),
                'price_bought': 0.0,  # Will be set by user later
                'psa': card_info['psa'],
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to MongoDB
            card_id = card_model.create_card(card_data)
            card_data['id'] = card_id
            card_data['_id'] = card_id
            
            scraped_cards.append(card_data)
        
        logger.info(f"Successfully scraped and saved {len(scraped_cards)} cards to MongoDB")
        
        # Prepare response message
        message_parts = []
        if scraped_cards:
            message_parts.append(f"Successfully scraped {len(scraped_cards)} new cards")
        if existing_cards:
            message_parts.append(f"skipped {len(existing_cards)} existing cards")
        
        response_message = f"{' and '.join(message_parts)} from {tcg} - {expansion}"
        
        return jsonify({
            'message': response_message,
            'scraped_cards': scraped_cards,
            'skipped_cards': existing_cards,
            'total_cards': len(card_model.get_cards(user_id=user_id))
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

@app.route('/api/cards', methods=['GET'])
@auth_required
def get_cards():
    """Get all cards with optional filtering"""
    try:
        # Get query parameters
        expansion = request.args.get('expansion')
        rarity = request.args.get('rarity')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        search = request.args.get('search', '').lower()
        
        # Get cards from MongoDB for current user
        cards = card_model.get_cards(user_id=request.current_user['user_id'])
        
        # Apply filters
        if expansion:
            cards = [card for card in cards if card['expansion'].lower() == expansion.lower()]
        
        if rarity:
            cards = [card for card in cards if card['rarity'].lower() == rarity.lower()]
        
        if min_price is not None:
            cards = [card for card in cards if card['current_price'] >= min_price]
        
        if max_price is not None:
            cards = [card for card in cards if card['current_price'] <= max_price]
        
        if search:
            cards = [
                card for card in cards 
                if search in card['name'].lower() or 
                   search in card['expansion'].lower() or
                   search in str(card['number']).lower()
            ]
        
        return jsonify({
            'items': cards,
            'total': len(cards),
            'timestamp': datetime.now().isoformat(),
            'user': request.current_user['user_id']
        })
        
    except Exception as e:
        logger.error(f"Error getting cards: {e}")
        return jsonify({'error': 'Failed to get cards'}), 500

@app.route('/api/cards/<card_id>', methods=['GET'])
def get_card(card_id):
    """Get a specific card by ID"""
    try:
        card = card_model.get_card_by_id(card_id)
        if not card:
            return jsonify({'error': 'Card not found'}), 404
        return jsonify(card)
    except Exception as e:
        logger.error(f"Error getting card {card_id}: {e}")
        return jsonify({'error': 'Failed to get card'}), 500

@app.route('/api/cards/<card_id>/buy-price', methods=['PUT'])
@auth_required  # ADDED: Require authentication for price updates
def update_card_buy_price(card_id):
    """Update only the buy price of a specific card"""
    try:
        data = request.get_json()
        if not data or 'buy_price' not in data:
            return jsonify({'error': 'Missing buy_price field'}), 400
        
        try:
            buy_price = float(data['buy_price'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid buy_price - must be a number'}), 400
        
        # Update the card in MongoDB
        result = card_model.update_card(card_id, {
            'price_bought': buy_price,
            'last_updated': datetime.now().isoformat()
        })
        
        if not result:
            return jsonify({'error': 'Card not found'}), 404
        
        # Get the updated card
        updated_card = card_model.get_card_by_id(card_id)
        
        return jsonify({
            'message': 'Buy price updated successfully',
            'card': updated_card
        })
        
    except Exception as e:
        logger.error(f"Error updating buy price for card {card_id}: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/cards/<card_id>', methods=['PUT'])
@auth_required  # ADDED: Require authentication for card updates
def update_card(card_id):
    """Update an existing card"""
    try:
        updated_data = request.get_json()
        updated_data['last_updated'] = datetime.now().isoformat()
        
        # Update the card in MongoDB
        result = card_model.update_card(card_id, updated_data)
        if not result:
            return jsonify({'error': 'Card not found'}), 404
        
        # Get the updated card
        updated_card = card_model.get_card_by_id(card_id)
        
        return jsonify({
            'message': 'Card updated successfully',
            'card': updated_card
        })
        
    except Exception as e:
        logger.error(f"Error updating card {card_id}: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/cards/<card_id>', methods=['DELETE'])
def delete_card(card_id):
    """Delete a card"""
    try:
        result = card_model.delete_card(card_id)
        if not result:
            return jsonify({'error': 'Card not found'}), 404
        
        logger.info(f"Deleted card {card_id}")
        return jsonify({'message': 'Card deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting card {card_id}: {e}")
        return jsonify({'error': 'Failed to delete card'}), 500

@app.route('/api/cards', methods=['DELETE'])
@auth_required
def delete_all_cards():
    """Delete all cards from the collection"""
    try:
        user_id = request.current_user['user_id']
        
        # Get current count before deletion
        cards = card_model.get_cards(user_id=user_id)
        cards_count = len(cards)
        
        # Delete all cards for the user
        result = card_model.delete_all_cards(user_id=user_id)
        
        logger.info(f"Deleted all {result} cards for user '{user_id}'")
        
        return jsonify({
            'message': f'Successfully deleted all {result} cards',
            'deleted_count': result,
            'total_cards': 0
        })
        
    except Exception as e:
        logger.error(f"Error deleting all cards: {e}")
        return jsonify({'error': 'Failed to delete all cards'}), 500

@app.route('/api/assets/<asset_type>', methods=['DELETE'])
@auth_required
def delete_all_assets(asset_type):
    """Delete all assets of a specific type"""
    try:
        user_id = request.current_user['user_id']
        
        if asset_type == 'cards':
            # Get current count before deletion
            cards = card_model.get_cards(user_id=user_id)
            cards_count = len(cards)
            
            # Delete all cards for the user
            deleted_count = card_model.delete_all_cards(user_id=user_id)
            
            logger.info(f"Deleted all {deleted_count} cards for user '{user_id}'")
            
            return jsonify({
                'message': f'Successfully deleted all {deleted_count} cards',
                'deleted_count': deleted_count,
                'total_cards': 0
            })
        else:
            # For other asset types, return empty success for now
            return jsonify({
                'message': f'Successfully deleted all {asset_type}',
                'deleted_count': 0,
                'total_cards': 0
            })
            
    except Exception as e:
        logger.error(f"Error deleting all {asset_type}: {e}")
        return jsonify({'error': f'Failed to delete all {asset_type}'}), 500

@app.route('/api/stats', methods=['GET'])
@auth_required
def get_stats():
    """Get statistics about the card collection"""
    try:
        cards = card_model.get_cards(user_id=request.current_user['user_id'])
        
        if not cards:
            return jsonify({
                'total_cards': 0,
                'total_value': 0,
                'average_price': 0,
                'expansions': [],
                'rarities': []
            })
        
        total_cards = len(cards)
        total_value = sum(card['current_price'] for card in cards)
        average_price = total_value / total_cards if total_cards > 0 else 0
        
        expansions = list(set(card['expansion'] for card in cards))
        rarities = list(set(card['rarity'] for card in cards))
        
        return jsonify({
            'total_cards': total_cards,
            'total_value': round(total_value, 2),
            'average_price': round(average_price, 2),
            'expansions': sorted(expansions),
            'rarities': sorted(rarities)
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500



@app.route('/api/portfolio/summary', methods=['GET'])
@auth_required
def get_portfolio_summary():
    """Get portfolio summary across all asset types"""
    try:
        logger.info("Portfolio summary endpoint called")
        
        user_id = request.current_user['user_id']
        
        # Use MongoDB aggregation for portfolio summary
        portfolio_summary = card_model.get_portfolio_summary(user_id=user_id)
        
        logger.info(f"Retrieved portfolio summary from MongoDB: {portfolio_summary}")
        
        # Get cards for top/worst performers
        cards = card_model.get_cards(user_id=user_id)
        
        # Calculate performers
        performers = []
        for card in cards:
            if card.get('price_bought', 0) > 0:
                profit_loss = card['current_price'] - card['price_bought']
                profit_loss_percentage = (profit_loss / card['price_bought']) * 100
                performers.append({
                    **card,
                    'profit_loss': profit_loss,
                    'profit_loss_percentage': profit_loss_percentage
                })
        
        # Sort by profit/loss
        performers.sort(key=lambda x: x['profit_loss'], reverse=True)
        
        top_performers = performers[:5]
        worst_performers = performers[-5:] if len(performers) > 5 else []
        
        summary = {
            'total_portfolio_value': portfolio_summary.get('total_portfolio_value', 0),
            'total_investment': portfolio_summary.get('total_investment', 0),
            'total_profit_loss': portfolio_summary.get('total_profit_loss', 0),
            'total_profit_loss_percentage': portfolio_summary.get('total_profit_loss_percentage', 0),
            'asset_breakdown': portfolio_summary.get('asset_breakdown', {}),
            'top_performers': top_performers,
            'worst_performers': worst_performers
        }
        
        logger.info("Returning portfolio summary successfully")
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    logger.info("Test endpoint called")
    return jsonify({"message": "Backend is working!", "timestamp": datetime.now().isoformat()})

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

# ============================================================================
# FINANCIAL ASSETS ENDPOINTS (Stocks, ETFs, Crypto) - YFinance Integration
# ============================================================================

@app.route('/api/financial/<asset_type>', methods=['GET'])
@auth_required
def get_financial_assets(asset_type):
    """Get all financial assets of a specific type for the current user"""
    try:
        # Validate asset type
        if asset_type not in ['stocks', 'etfs', 'crypto']:
            return jsonify({'status': 'error', 'message': 'Invalid asset type'}), 400
        
        if not financial_asset_model:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500
        
        user_id = request.current_user['user_id']
        assets = financial_asset_model.get_assets_by_type(user_id, asset_type)
        
        return jsonify({
            'status': 'success',
            'items': assets,
            'total': len(assets),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting {asset_type}: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/financial/<asset_type>', methods=['POST'])
@auth_required
def add_financial_asset(asset_type):
    """Add a new financial asset using yfinance data"""
    try:
        # Validate asset type
        if asset_type not in ['stocks', 'etfs', 'crypto']:
            return jsonify({'status': 'error', 'message': 'Invalid asset type'}), 400
        
        if not financial_asset_model:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500
        
        data = request.get_json()
        ticker = data.get('ticker', '').strip().upper()
        quantity = float(data.get('quantity', 1))
        
        if not ticker:
            return jsonify({'status': 'error', 'message': 'Ticker symbol is required'}), 400
        
        if quantity <= 0:
            return jsonify({'status': 'error', 'message': 'Quantity must be greater than 0'}), 400
        
        # Get asset info from yfinance
        asset_info = yfinance_service.get_asset_info(ticker, asset_type)
        
        if not asset_info:
            return jsonify({
                'status': 'error', 
                'message': f'Could not find asset data for {ticker}. Please check the symbol.'
            }), 404
        
        # Prepare asset data for database
        user_id = request.current_user['user_id']
        # Accept price_bought from client, fallback to yfinance price if not provided
        price_bought = float(data.get('price_bought', 0))
        if price_bought <= 0:
            price_bought = asset_info['current_price']
        asset_data = {
            'user_id': user_id,
            'asset_type': asset_type,
            'symbol': asset_info['symbol'],
            'name': asset_info['name'],
            'current_price': asset_info['current_price'],
            'currency': asset_info.get('currency', 'USD'),
            'price_bought': price_bought,
            'quantity': quantity,
            'change_24h': asset_info.get('change_24h', 0),
        }
        
        # Add type-specific fields
        if asset_type == 'stocks':
            asset_data.update({
                'company': asset_info.get('company', ''),
                'sector': asset_info.get('sector', ''),
                'market': asset_info.get('market', ''),
                'dividend_yield': asset_info.get('dividend_yield', 0)
            })
        elif asset_type == 'etfs':
            asset_data.update({
                'fund_name': asset_info.get('fund_name', ''),
                'expense_ratio': asset_info.get('expense_ratio', 0),
                'category': asset_info.get('category', ''),
                'dividend_yield': asset_info.get('dividend_yield', 0)
            })
        elif asset_type == 'crypto':
            asset_data.update({
                'market_cap': asset_info.get('market_cap', 0),
                'volume_24h': asset_info.get('volume_24h', 0)
            })
        
        # Save to database
        asset_id = financial_asset_model.create_asset(asset_data)
        
        # Get the created asset
        created_asset = financial_asset_model.get_asset_by_id(user_id, asset_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully added {ticker} to {asset_type}',
            'asset': created_asset
        })
        
    except ValueError as e:
        logger.warning(f"Validation error adding {asset_type}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding {asset_type}: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/financial/<asset_type>/<asset_id>/bought-price', methods=['PUT'])
@auth_required
def update_bought_price(asset_type, asset_id):
    """Update the bought price for a financial asset"""
    try:
        if asset_type not in ['stocks', 'etfs', 'crypto']:
            return jsonify({'status': 'error', 'message': 'Invalid asset type'}), 400
        
        if not financial_asset_model:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500
        
        data = request.get_json()
        price_bought = float(data.get('price_bought', 0))
        
        if price_bought <= 0:
            return jsonify({'status': 'error', 'message': 'Bought price must be greater than 0'}), 400
        
        user_id = request.current_user['user_id']
        
        # Update the asset
        success = financial_asset_model.update_asset(user_id, asset_id, {
            'price_bought': price_bought
        })
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Asset not found'}), 404
        
        # Get updated asset
        updated_asset = financial_asset_model.get_asset_by_id(user_id, asset_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Updated bought price to ${price_bought:.2f}',
            'asset': updated_asset
        })
        
    except Exception as e:
        logger.error(f"Error updating bought price: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/financial/<asset_type>/<asset_id>/quantity', methods=['PUT'])
@auth_required
def update_quantity(asset_type, asset_id):
    """Update the quantity for a financial asset"""
    try:
        if asset_type not in ['stocks', 'etfs', 'crypto']:
            return jsonify({'status': 'error', 'message': 'Invalid asset type'}), 400
        
        if not financial_asset_model:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500
        
        data = request.get_json()
        quantity = float(data.get('quantity', 0))
        
        if quantity <= 0:
            return jsonify({'status': 'error', 'message': 'Quantity must be greater than 0'}), 400
        
        user_id = request.current_user['user_id']
        
        # Update the asset
        success = financial_asset_model.update_asset(user_id, asset_id, {
            'quantity': quantity
        })
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Asset not found'}), 404
        
        # Get updated asset
        updated_asset = financial_asset_model.get_asset_by_id(user_id, asset_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Updated quantity to {quantity}',
            'asset': updated_asset
        })
        
    except Exception as e:
        logger.error(f"Error updating quantity: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/financial/<asset_type>/<asset_id>', methods=['DELETE'])
@auth_required
def delete_financial_asset(asset_type, asset_id):
    """Delete a financial asset"""
    try:
        if asset_type not in ['stocks', 'etfs', 'crypto']:
            return jsonify({'status': 'error', 'message': 'Invalid asset type'}), 400
        
        if not financial_asset_model:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500
        
        user_id = request.current_user['user_id']
        
        # Get asset info before deleting
        asset = financial_asset_model.get_asset_by_id(user_id, asset_id)
        if not asset:
            return jsonify({'status': 'error', 'message': 'Asset not found'}), 404
        
        # Delete the asset
        success = financial_asset_model.delete_asset(user_id, asset_id)
        
        if not success:
            return jsonify({'status': 'error', 'message': 'Failed to delete asset'}), 500
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully deleted {asset["symbol"]}'
        })
        
    except Exception as e:
        logger.error(f"Error deleting financial asset: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/financial/<asset_type>', methods=['DELETE'])
@auth_required
def delete_all_financial_assets(asset_type):
    """Delete all financial assets of a specific type"""
    try:
        if asset_type not in ['stocks', 'etfs', 'crypto']:
            return jsonify({'status': 'error', 'message': 'Invalid asset type'}), 400
        
        if not financial_asset_model:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500
        
        user_id = request.current_user['user_id']
        deleted_count = financial_asset_model.delete_all_assets(user_id, asset_type)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully deleted {deleted_count} {asset_type}',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error deleting all {asset_type}: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/financial/<asset_type>/refresh-prices', methods=['POST'])
@auth_required
def refresh_financial_asset_prices(asset_type):
    """Refresh prices for financial assets"""
    try:
        if asset_type not in ['stocks', 'etfs', 'crypto']:
            return jsonify({'status': 'error', 'message': 'Invalid asset type'}), 400
        
        if not financial_asset_model:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500
        
        data = request.get_json() or {}
        asset_ids = data.get('asset_ids', [])
        
        user_id = request.current_user['user_id']
        
        # Get assets to refresh
        if asset_ids:
            assets = []
            for asset_id in asset_ids:
                asset = financial_asset_model.get_asset_by_id(user_id, asset_id)
                if asset:
                    assets.append(asset)
        else:
            # Refresh all assets of this type
            assets = financial_asset_model.get_assets_by_type(user_id, asset_type)
        
        if not assets:
            return jsonify({'status': 'error', 'message': 'No assets to refresh'}), 400
        
        # Refresh prices using yfinance
        updated, failed = yfinance_service.refresh_prices(assets)
        
        # Update database with new prices
        updated_details = []
        failed_details = []
        
        for asset in updated:
            try:
                success = financial_asset_model.update_price(
                    user_id, 
                    asset['id'], 
                    asset['current_price'],
                    'yfinance'
                )
                
                if success:
                    updated_details.append({
                        'id': asset['id'],
                        'name': asset['name'],
                        'old_price': asset.get('old_price', 0),
                        'new_price': asset['current_price']
                    })
                else:
                    failed_details.append({
                        'id': asset['id'],
                        'name': asset['name'],
                        'error': 'Failed to update in database'
                    })
                    
            except Exception as e:
                failed_details.append({
                    'id': asset['id'],
                    'name': asset['name'],
                    'error': str(e)
                })
        
        for failure in failed:
            failed_details.append({
                'id': failure['asset'].get('id', 'unknown'),
                'name': failure['asset'].get('name', 'unknown'),
                'error': failure['error']
            })
        
        return jsonify({
            'status': 'success',
            'message': f'Refreshed {len(updated_details)} assets, {len(failed_details)} failed',
            'updated_count': len(updated_details),
            'failed_count': len(failed_details),
            'details': {
                'updated': updated_details,
                'failed': failed_details
            }
        })
        
    except Exception as e:
        logger.error(f"Error refreshing {asset_type} prices: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ============================================================================

@app.route('/api/cards/rescrape', methods=['POST'])
@auth_required
def rescrape_card_prices():
    """Rescrape prices for all existing cards"""
    try:
        cards = card_model.get_cards(user_id=request.current_user['user_id'])
        
        if not cards:
            return jsonify({'status': 'error', 'message': 'No cards to rescrape'}), 400
        
        logger.info(f"Starting rescrape for {len(cards)} cards")
        updated_cards = []
        errors = []
        
        for card in cards:
            try:
                # Rescrape individual card
                logger.info(f"Rescrap­ing card: {card['name']} ({card['tcg']} - {card['expansion']} #{card['number']})")
                result = scraper_manager.scrape_assets('cards', 
                    tcg=card['tcg'], 
                    expansion=card['expansion'], 
                    numbers=[card['number']], 
                    headless=True
                )
                
                if result:
                    # Update the existing card with new price data
                    new_data = result[0]  # scrape_assets returns a list directly
                    
                    # Update in MongoDB
                    updated_data = {
                        'current_price': float(new_data['current_price']),
                        'supply': int(new_data['supply']),
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    card_model.update_card(card['_id'], updated_data)
                    
                    # Update local card object for response
                    card.update(updated_data)
                    updated_cards.append(card)
                    logger.info(f"Updated {card['name']}: €{new_data['current_price']}")
                else:
                    errors.append(f"No data found for {card['name']}")
                    
            except Exception as e:
                error_msg = f"Failed to rescrape {card['name']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return jsonify({
            'status': 'success',
            'message': f'Rescraped {len(updated_cards)} cards',
            'updated_cards': updated_cards,
            'errors': errors,
            'total_updated': len(updated_cards),
            'total_errors': len(errors)
        })
        
    except Exception as e:
        logger.error(f"Error during rescrape: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/cards/test-data', methods=['POST'])
@auth_required
def add_test_cards():
    """Add some test cards with prices for testing"""
    try:
        test_cards_data = [
            {
                'user_id': request.current_user['user_id'],
                'type': 'cards',
                'tcg': 'Pokemon',
                'expansion': 'Test Set',
                'number': 1,
                'name': 'Test Pikachu',
                'rarity': 'Rare',
                'supply': 50,
                'quantity': 1,
                'current_price': 25.50,
                'price_bought': 20.00,
                'psa': 'PSA 9',
                'last_updated': datetime.now().isoformat()
            },
            {
                'user_id': request.current_user['user_id'],
                'type': 'cards',
                'tcg': 'Pokemon',
                'expansion': 'Test Set',
                'number': 2,
                'name': 'Test Charizard',
                'rarity': 'Secret Rare',
                'supply': 15,
                'quantity': 1,
                'current_price': 150.00,
                'price_bought': 120.00,
                'psa': 'PSA 10',
                'last_updated': datetime.now().isoformat()
            }
        ]
        
        # Remove existing test cards if they exist
        existing_cards = card_model.get_cards(user_id=request.current_user['user_id'])
        for card in existing_cards:
            if card.get('name') in ['Test Pikachu', 'Test Charizard']:
                card_model.delete_card(card['_id'])
        
        # Add new test cards to MongoDB
        added_cards = []
        for card_data in test_cards_data:
            card_id = card_model.create_card(card_data)
            card_data['id'] = card_id
            card_data['_id'] = card_id
            added_cards.append(card_data)
        
        total_cards = len(card_model.get_cards(user_id=request.current_user['user_id']))
        
        return jsonify({
            'message': f'Added {len(added_cards)} test cards',
            'test_cards': added_cards,
            'total_cards': total_cards
        })
        
    except Exception as e:
        logger.error(f"Error adding test cards: {e}")
        return jsonify({'error': 'Failed to add test cards'}), 500

@app.route('/api/cards/scrape-single', methods=['POST'])
@auth_required
def scrape_single_card():
    """Scrape a single card from CardMarket URL with price history tracking"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'message': 'CardMarket URL is required'
            }), 400
        
        url = data['url']
        
        # Validate URL format (basic check for CardMarket)
        if 'cardmarket.com' not in url and 'cardmarket.eu' not in url:
            return jsonify({
                'success': False,
                'message': 'Please provide a valid CardMarket URL'
            }), 400
        
        # Use scraper to get card data
        result = scraper_manager.scrape_cards([{'url': url}])
        
        if not result['scraped_cards']:
            return jsonify({
                'success': False,
                'message': 'Unable to scrape card data from the provided URL'
            }), 400
        
        scraped_card = result['scraped_cards'][0]
        current_time = datetime.now().isoformat()
        
        # Check if card already exists (by name and expansion)
        existing_cards = card_model.get_cards(user_id=request.current_user['user_id'])
        existing_card = None
        for card in existing_cards:
            if (card['name'] == scraped_card['name'] and 
                card['expansion'] == scraped_card['expansion'] and
                card['tcg'] == scraped_card['tcg']):
                existing_card = card
                break
        
        if existing_card:
            # Update existing card with new price and add to history
            old_price = existing_card['current_price']
            update_data = {
                'current_price': float(scraped_card['current_price']),
                'last_updated': current_time
            }
            
            # Update price history
            card_model.add_price_history(existing_card['_id'], {
                'price': float(scraped_card['current_price']),
                'timestamp': current_time,
                'source': 'scrape_update'
            })
            
            # Update the card in MongoDB
            card_model.update_card(existing_card['_id'], update_data)
            
            # Get updated card for response
            updated_card = card_model.get_card_by_id(existing_card['_id'])
            
            return jsonify({
                'success': True,
                'message': f'Card "{scraped_card["name"]}" updated successfully',
                'added': False,
                'card': updated_card
            })
        else:
            # Add new card with initial price history
            new_card_data = {
                'user_id': request.current_user['user_id'],
                'type': 'cards',
                'tcg': scraped_card.get('tcg', 'Unknown'),
                'expansion': scraped_card.get('expansion', 'Unknown'),
                'number': scraped_card.get('number', 0),
                'name': scraped_card.get('name', 'Unknown'),
                'rarity': scraped_card.get('rarity', 'Unknown'),
                'supply': scraped_card.get('supply', 0),
                'quantity': 1,
                'current_price': float(scraped_card['current_price']),
                'price_bought': 0.0,
                'psa': scraped_card.get('psa', ''),
                'last_updated': current_time
            }
            
            # Create the card in MongoDB
            card_id = card_model.create_card(new_card_data)
            new_card_data['id'] = card_id
            new_card_data['_id'] = card_id
            
            # Add initial price history
            card_model.add_price_history(card_id, {
                'price': float(scraped_card['current_price']),
                'timestamp': current_time,
                'source': 'initial_scrape'
            })
            
            return jsonify({
                'success': True,
                'message': f'Card "{scraped_card["name"]}" added successfully',
                'added': True,
                'card': new_card_data
            })
            
    except Exception as e:
        logger.error(f"Error scraping single card: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to scrape card: {str(e)}'
        }), 500

@app.route('/api/scrape/steam', methods=['POST'])
@auth_required  # ADDED: Require authentication for Steam scraping
def scrape_steam_inventory():
    """Scrape Steam CS2 inventory from Steam profile"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        steam_id = data.get('steam_id')
        app_id = data.get('app_id', '730')  # Default to CS2
        include_floats = data.get('include_floats', True)
        headless = data.get('headless', True)
        
        if not steam_id:
            return jsonify({
                'status': 'error', 
                'message': 'Missing required field: steam_id'
            }), 400
        
        # Get user ID
        user_id = request.current_user['user_id']
        
        # Call the scraper without pricing options, but with user_id for proper association
        scraped_items_data = scraper_manager.scrape_assets(
            'steam', 
            steam_id=steam_id, 
            app_id=app_id, 
            include_floats=include_floats,
            headless=headless,
            user_id=user_id  # Pass user_id to scraper for proper association
        )
        
        # Save scraped items to MongoDB using steam_item_model
        scraped_items = []
        skipped_items = []
        failed_items = []
        
        logger.info(f"Processing {len(scraped_items_data)} scraped items for user {user_id}")
        
        for i, item_info in enumerate(scraped_items_data):
            try:
                asset_id = item_info.get('asset_id')
                item_name = item_info.get('name', '')
                item_category = item_info.get('item_category', 'unknown')
                
                logger.info(f"Processing item {i+1}/{len(scraped_items_data)}: {item_name} ({item_category})")
                
                # Check if item already exists using asset_id
                existing_item = steam_item_model.find_existing_item(user_id, asset_id)
                
                if existing_item:
                    # Skip existing items
                    skipped_items.append({
                        'name': item_name,
                        'asset_id': asset_id,
                        'message': 'Already exists in Steam inventory'
                    })
                    logger.info(f"Skipping Steam item - already exists: {item_name}")
                    continue
            
                # Prepare item data for MongoDB
                item_data = {
                    'user_id': item_info.get('user_id', user_id),  # Use scraper's user_id or fallback to request user_id
                    'name': item_info['name'],
                    'rarity': item_info.get('rarity', 'Unknown'),
                    'condition': item_info.get('condition'),
                    'float_value': item_info.get('float_value'),
                    'current_price': 0.0,  # No pricing
                    'price_bought': 0.0,  # To be set by user later
                    'quantity': item_info.get('quantity', 1),
                    'game': item_info.get('game', 'Counter-Strike 2'),
                    'asset_id': asset_id,
                    'image_url': item_info.get('image_url', ''),
                    'market_hash_name': item_info.get('market_hash_name', ''),
                    'item_category': item_info.get('item_category', 'unknown'),
                    'item_type': item_info.get('item_type', ''),
                    'steam_id': steam_id
                }
                
                # Create Steam item
                created_item = steam_item_model.create_item(item_data)
                scraped_items.append(created_item)
                
                logger.info(f"Successfully added Steam item: {item_name} ({item_category})")
                
            except Exception as e:
                logger.error(f"Failed to save Steam item {item_name}: {e}")
                failed_items.append({
                    'name': item_name,
                    'asset_id': asset_id,
                    'error': str(e)
                })
                continue
        
        # Prepare response message
        message = f"Successfully scraped {len(scraped_items)} new CS2 items from Steam inventory"
        
        if skipped_items:
            message += f". Skipped {len(skipped_items)} existing items"
        
        if failed_items:
            message += f". Failed to save {len(failed_items)} items"
        
        logger.info(f"Steam scraping complete - Scraped: {len(scraped_items)}, Skipped: {len(skipped_items)}, Failed: {len(failed_items)}")
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': {
                'scraped_items': scraped_items,
                'skipped_items': skipped_items,
                'failed_items': failed_items,
                'total_scraped': len(scraped_items),
                'total_skipped': len(skipped_items),
                'total_failed': len(failed_items)
            }
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

# Steam Inventory Management Routes
@app.route('/api/steam/import', methods=['POST'])
@auth_required
def import_steam_inventory():
    """DEPRECATED: Use /api/scrape/steam instead. This endpoint doesn't save to database."""
    return jsonify({
        'status': 'error', 
        'message': 'This endpoint is deprecated. Please use /api/scrape/steam to properly save inventory to database.'
    }), 400
@app.route('/api/steam/items', methods=['GET'])
@auth_required
def get_steam_items():
    """Get user's Steam inventory items"""
    try:
        user_id = request.current_user['user_id']
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page
        
        # Get Steam items
        items = steam_item_model.get_items_by_user(user_id, limit=per_page, skip=skip)
        
        return jsonify({
            'status': 'success',
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': len(items)
        })
        
    except Exception as e:
        logger.error(f"Error getting Steam items: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to get Steam items'}), 500


@app.route('/api/steam/items/<item_id>', methods=['PUT'])
@auth_required
def update_steam_item(item_id):
    """Update a Steam inventory item (mainly for bought price)"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        # Update the item
        updated_item = steam_item_model.update_item(item_id, data)
        
        return jsonify({
            'status': 'success',
            'message': 'Steam item updated successfully',
            'item': updated_item
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404
    except Exception as e:
        logger.error(f"Error updating Steam item: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update Steam item'}), 500


@app.route('/api/steam/items/<item_id>', methods=['DELETE'])
@auth_required
def delete_steam_item(item_id):
    """Delete a Steam inventory item"""
    try:
        user_id = request.current_user['user_id']
        
        success = steam_item_model.delete_item(item_id, user_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Steam item deleted successfully'
            })
        else:
            return jsonify({'status': 'error', 'message': 'Steam item not found'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting Steam item: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete Steam item'}), 500


@app.route('/api/steam/items', methods=['DELETE'])
def delete_all_steam_items():
    """Delete all Steam inventory items for default user (admin function)"""
    try:
        user_id = 'default_user'  # Target the default user specifically
        
        if not steam_item_model:
            return jsonify({'status': 'error', 'message': 'Steam item model not available'}), 503
        
        # Get current count before deletion
        items = steam_item_model.get_items_by_user(user_id)
        items_count = len(items)
        
        # Delete all Steam items for the default user
        deleted_count = steam_item_model.delete_all_items(user_id)
        
        logger.info(f"Deleted all {deleted_count} Steam items for user '{user_id}'")
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully deleted all {deleted_count} Steam items for default user',
            'deleted_count': deleted_count,
            'total_steam_items': 0
        })
        
    except Exception as e:
        logger.error(f"Error deleting all Steam items: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete all Steam items'}), 500

@app.route('/api/steam/stats', methods=['GET'])
@auth_required
def get_steam_stats():
    """Get user's Steam inventory statistics"""
    try:
        user_id = request.current_user['user_id']
        
        stats = steam_item_model.get_user_stats(user_id)
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting Steam stats: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to get Steam stats'}), 500
        
    except ValidationError as e:
        logger.warning(f"Validation error in Steam scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except ScraperError as e:
        logger.error(f"Scraper error in Steam scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in Steam scraping: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# STEAM INVENTORY RESCRAPE ENDPOINT
@app.route('/api/steam/rescrape', methods=['POST'])
@auth_required
def rescrape_steam_inventory():
    """Rescrape Steam inventory: add new items, remove sold items, skip existing."""
    try:
        data = request.get_json()
        steam_id = data.get('steam_id')
        if not steam_id:
            return jsonify({'status': 'error', 'message': 'Missing steam_id'}), 400

        user_id = request.current_user['user_id']

        # Scrape current inventory (returns list of dicts)
        scraped_items_data = scraper_manager.scrape_assets(
            'steam',
            steam_id=steam_id,
            user_id=user_id,
            headless=True
        )

        # Get current items from DB
        db_items = steam_item_model.get_items_by_user(user_id)
        db_ids = {str(item.get('asset_id')) for item in db_items}
        scraped_ids = {str(item.get('asset_id')) for item in scraped_items_data}

        # Add new items
        added = 0
        for item in scraped_items_data:
            if str(item.get('asset_id')) not in db_ids:
                try:
                    # Prepare item data for DB
                    item_data = {
                        'user_id': user_id,
                        'name': item.get('name', ''),
                        'rarity': item.get('rarity', 'Unknown'),
                        'condition': item.get('condition'),
                        'float_value': item.get('float_value'),
                        'current_price': 0.0,
                        'price_bought': 0.0,
                        'quantity': item.get('quantity', 1),
                        'game': item.get('game', 'Counter-Strike 2'),
                        'asset_id': item.get('asset_id'),
                        'image_url': item.get('image_url', ''),
                        'market_hash_name': item.get('market_hash_name', ''),
                        'item_category': item.get('item_category', 'unknown'),
                        'item_type': item.get('item_type', ''),
                        'steam_id': steam_id
                    }
                    steam_item_model.create_item(item_data)
                    added += 1
                except Exception as e:
                    logger.error(f"Failed to add Steam item: {item.get('name', '')}: {e}")

        # Remove sold items
        removed = 0
        for item in db_items:
            if str(item.get('asset_id')) not in scraped_ids:
                try:
                    steam_item_model.delete_item(item['_id'], user_id)
                    removed += 1
                except Exception as e:
                    logger.error(f"Failed to remove Steam item: {item.get('name', '')}: {e}")

        skipped = len(scraped_items_data) - added

        return jsonify({
            'status': 'success',
            'message': f'Rescrape complete. Added: {added}, Removed: {removed}, Skipped: {skipped}',
            'items': scraped_items_data,
            'added': added,
            'removed': removed,
            'skipped': skipped
        })
    except Exception as e:
        logger.error(f"Error during Steam inventory rescrape: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        if user_model and user_model.get_user_by_email(data['email']):
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create user
        if not user_model:
            return jsonify({'error': 'Authentication system not available'}), 503
        
        user_id = user_model.create_user(data)
        if not user_id:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Generate token
        token = JWTManager.generate_token(user_id, data['username'], data['email'])
        if not token:
            return jsonify({'error': 'Failed to generate token'}), 500
        
        logger.info(f"User registered: {data['email']}")
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'user_id': user_id,
                'username': data['username'],
                'email': data['email']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        if not user_model:
            return jsonify({'error': 'Authentication system not available'}), 503
        
        # Authenticate user
        user = user_model.authenticate_user(data['email'], data['password'])
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = JWTManager.generate_token(user['user_id'], user['username'], user['email'])
        if not token:
            return jsonify({'error': 'Failed to generate token'}), 500
        
        logger.info(f"User logged in: {data['email']}")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'profile': user.get('profile', {})
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/me', methods=['GET'])
@auth_required
def get_current_user():
    """Get current user information"""
    try:
        if not user_model:
            return jsonify({'error': 'Authentication system not available'}), 503
        
        user = user_model.get_user_by_id(request.current_user['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'profile': user.get('profile', {}),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login')
            }
        })
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500

@app.route('/api/auth/profile', methods=['PUT'])
@auth_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        if not user_model:
            return jsonify({'error': 'Authentication system not available'}), 503
        
        # Prepare update data
        update_data = {}
        if 'display_name' in data:
            update_data['profile.display_name'] = data['display_name']
        if 'bio' in data:
            update_data['profile.bio'] = data['bio']
        if 'avatar_url' in data:
            update_data['profile.avatar_url'] = data['avatar_url']
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update user
        success = user_model.update_user(request.current_user['user_id'], update_data)
        if not success:
            return jsonify({'error': 'Failed to update profile'}), 500
        
        # Get updated user
        user = user_model.get_user_by_id(request.current_user['user_id'])
        
        logger.info(f"Profile updated for user: {request.current_user['email']}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'profile': user.get('profile', {})
            }
        })
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@app.route('/api/auth/users', methods=['GET'])
@auth_required
def get_all_users():
    """Get all users (admin endpoint)"""
    try:
        # Get all users from the database
        users = list(user_model.collection.find({}, {
            '_id': 1,
            'username': 1,
            'email': 1,
            'created_at': 1,
            'last_login': 1
            # Exclude password hash for security
        }))
        
        # Convert ObjectId to string for JSON serialization
        for user in users:
            user['_id'] = str(user['_id'])
            user['id'] = user['_id']  # Add id field for frontend compatibility
        
        return jsonify({
            'users': users,
            'total': len(users)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@app.route('/api/steam/update-floats', methods=['POST'])
@auth_required
def update_steam_floats():
    """Update Steam item float values and paint seeds using CSFloat"""
    try:
        user_id = request.current_user['user_id']
        items = steam_item_model.get_items_by_user(user_id)
        
        if not items:
            return jsonify({
                'status': 'error', 
                'message': 'No Steam items found to update'
            }), 400
        
        logger.info(f"Starting float update for {len(items)} Steam items")
        
        updated_items = []
        failed_items = []
        skipped_items = []
        
        # Import CSFloat scraper
        try:
            from scrapers.csfloat_scraper import CSFloatScraper
            csfloat_scraper = CSFloatScraper(headless=True)
        except ImportError:
            return jsonify({
                'status': 'error',
                'message': 'CSFloat scraper not available'
            }), 503
        
        try:
            for i, item in enumerate(items):
                try:
                    item_id = str(item['_id'])
                    item_name = item.get('name', 'Unknown')
                    
                    logger.info(f"Processing item {i+1}/{len(items)}: {item_name}")
                    
                    # Check if item has inspect link (only items with inspect links can have floats)
                    # For now, we'll simulate this check - in real implementation, 
                    # you'd need the inspect link from Steam inventory data
                    
                    # Skip items that already have float data
                    if item.get('float_value') is not None:
                        skipped_items.append({
                            'name': item_name,
                            'reason': 'Already has float data'
                        })
                        continue
                    
                    # For demo purposes, we'll skip items without weapon category
                    # In real implementation, you'd use the inspect link
                    if item.get('item_category', '').lower() not in ['weapon', 'knife', 'glove']:
                        skipped_items.append({
                            'name': item_name,
                            'reason': 'Item type does not support float values'
                        })
                        continue
                    
                    # TODO: Get actual inspect link from Steam inventory data
                    # For now, we'll simulate with a placeholder
                    inspect_link = item.get('inspect_link')
                    if not inspect_link:
                        skipped_items.append({
                            'name': item_name,
                            'reason': 'No inspect link available'
                        })
                        continue
                    
                    # Get float data from CSFloat
                    float_data = csfloat_scraper.get_float_data(inspect_link)
                    
                    if float_data and float_data.success:
                        # Update item in database
                        update_data = {
                            'float_value': float_data.float_value,
                            'paint_seed': float_data.paint_seed,
                            'last_updated': datetime.now().isoformat()
                        }
                        
                        update_result = steam_item_model.update_item(item_id, update_data)
                        if update_result:
                            item.update(update_data)
                            updated_items.append(item)
                            logger.info(f"Updated float for {item_name}: Float={float_data.float_value}, Pattern={float_data.paint_seed}")
                        else:
                            failed_items.append({
                                'name': item_name,
                                'error': 'Database update failed'
                            })
                    else:
                        error_msg = float_data.error if float_data else "Unknown error"
                        failed_items.append({
                            'name': item_name,
                            'error': f'CSFloat error: {error_msg}'
                        })
                        
                except Exception as e:
                    logger.error(f"Error updating float for item {item.get('name', 'Unknown')}: {e}")
                    failed_items.append({
                        'name': item.get('name', 'Unknown'),
                        'error': str(e)
                    })
                    
        finally:
            csfloat_scraper._cleanup()
        
        # Prepare response
        message_parts = []
        if updated_items:
            message_parts.append(f"Updated float data for {len(updated_items)} items")
        if skipped_items:
            message_parts.append(f"skipped {len(skipped_items)} items")
        if failed_items:
            message_parts.append(f"failed to update {len(failed_items)} items")
            
        response_message = " and ".join(message_parts) if message_parts else "No items were processed"
        status = 'success' if updated_items else 'warning'
        
        return jsonify({
            'status': status,
            'message': response_message,
            'updated_items': len(updated_items),
            'skipped_items': len(skipped_items),
            'failed_items': len(failed_items),
            'details': {
                'updated': [
                    {
                        'name': item['name'], 
                        'float_value': item.get('float_value'),
                        'paint_seed': item.get('paint_seed')
                    } 
                    for item in updated_items
                ],
                'skipped': skipped_items,
                'failed': failed_items
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating Steam floats: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to update float data: {str(e)}'
        }), 500

@app.route('/api/steam/update-prices', methods=['POST'])
@auth_required
def update_steam_prices():
    user_id = request.current_user['user_id']
    items = steam_item_model.get_items_by_user(user_id)
    """Update Steam item prices using SkinSnipe.com market data"""
    try:
        # --- SkinSearch logic start ---
        updated_items = []
        failed_items = []
        skipped_items = []
        from scrapers.skinsearch_scraper import SkinSearchScraper
        scraper = SkinSearchScraper()
        for item in items:
            try:
                item_id = str(item['_id'])
                price_info = scraper.scrape_steam_item(item)
                if price_info and hasattr(price_info, 'price') and price_info.price and price_info.price > 0:
                    update_result = steam_item_model.update_item(item_id, {
                        'current_price': price_info.price,
                        'price_source': 'skinsearch.com',
                        'last_updated': datetime.now().isoformat()
                    })
                    if update_result:
                        item['current_price'] = price_info.price
                        item['price_source'] = 'skinsearch.com'
                        updated_items.append(item)
                        logger.info(f"Updated price for {item['name']}: {price_info.price} {price_info.currency}")
                    else:
                        failed_items.append({
                            'name': item['name'],
                            'error': 'Database update failed'
                        })
                else:
                    # Log full error response if available
                    logger.warning(f"SkinSearch price not found for item: {item['name']}. Full item: {item}")
                    skipped_items.append({
                        'name': item['name'],
                        'reason': 'No price found on SkinSearch'
                    })
            except Exception as e:
                logger.error(f"Error updating item {item.get('name', 'Unknown')}: {e}")
                failed_items.append({
                    'name': item.get('name', 'Unknown'),
                    'error': str(e)
                })
        # --- SkinSearch logic end ---
        # Prepare response
        message_parts = []
        if updated_items:
            message_parts.append(f"Updated prices for {len(updated_items)} items")
        if skipped_items:
            message_parts.append(f"skipped {len(skipped_items)} items (no price found)")
        if failed_items:
            message_parts.append(f"failed to update {len(failed_items)} items")
        response_message = " and ".join(message_parts) if message_parts else "No items were processed"
        # If no prices were updated, return a warning status
        status = 'success' if updated_items else 'warning'
        return jsonify({
            'status': status,
            'message': response_message,
            'updated_items': len(updated_items),
            'skipped_items': len(skipped_items),
            'failed_items': len(failed_items),
            'details': {
                'updated': [{'name': item['name'], 'price': item['current_price']} for item in updated_items],
                'skipped': skipped_items,
                'failed': failed_items
            }
        })
    except Exception as e:
        logger.error(f"Error updating Steam prices: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to update Steam prices: {str(e)}'
        }), 500

@app.route('/api/scrape/bulk-parallel', methods=['POST'])
@auth_required  # Require authentication for bulk parallel scraping
def bulk_parallel_scrape():
    """Bulk parallel scraping with multiple instances for CSGOSkins items"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        if not items:
            return jsonify({'error': 'No items provided'}), 400
        
        if len(items) > 20:  # Limit bulk requests
            return jsonify({'error': 'Maximum 20 items per bulk request'}), 400
        
        logger.info(f"Starting bulk parallel scrape for {len(items)} items")
        
        # Import the working scraper
        from parallel_scraper import ParallelCSGOSkinsScraper
        
        # Use 3 instances for bulk operations
        parallel_scraper = ParallelCSGOSkinsScraper(num_instances=3)
        
        try:
            results = parallel_scraper.scrape_parallel(items)
            
            # Format results for API response
            formatted_results = []
            for result in results:
                if result and 'price' in result:
                    formatted_results.append({
                        'name': result['name'],
                        'price': result['price'],
                        'source': result.get('source', 'csgoskins.gg'),
                        'timestamp': datetime.now().isoformat(),
                        'instance_id': result.get('instance_id')
                    })
            
            success_rate = len(formatted_results) / len(items) * 100 if items else 0
            
            return jsonify({
                'status': 'success',
                'results': formatted_results,
                'total_items': len(items),
                'successful_items': len(formatted_results),
                'success_rate': round(success_rate, 1),
                'message': f'Bulk parallel scraping completed: {len(formatted_results)}/{len(items)} items'
            })
                
        finally:
            parallel_scraper.cleanup()
        
    except Exception as e:
        logger.error(f"Bulk parallel scrape error: {str(e)}")
        return jsonify({'error': f'Bulk scraping failed: {str(e)}'}), 500

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

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

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url}")
    if request.data:
        logger.info(f"Request data: {request.data}")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scraper manager (only for cards scraping)
scraper_manager = ScraperManager(api_keys={})

# In-memory storage for scraped cards
card_data = []

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
        
        tcg = data.get('tcg', 'Pokemon')  # Default to Pokemon
        expansion = data.get('expansion')
        numbers = data.get('numbers', [])
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
        
        # Call the scraper directly with the correct parameters including headless
        scraped_cards_data = scraper_manager.scrape_assets('cards', tcg=tcg, expansion=expansion, numbers=numbers, headless=headless)
        
        # Convert scraped data to card_data format and add to collection
        global card_data
        scraped_cards = []
        
        for card_info in scraped_cards_data:
            # Generate new ID
            new_id = max([card['id'] for card in card_data], default=0) + 1
            
            card = {
                'id': new_id,
                'type': 'cards',
                'tcg': card_info['tcg'],
                'expansion': card_info['expansion'],
                'number': int(card_info['number']),
                'name': card_info['name'],
                'rarity': card_info['rarity'],
                'supply': int(card_info['supply']),
                'quantity': 1,  # Default to owning 1 card
                'current_price': float(card_info['current_price']),
                'price_bought': 0.0,  # Will be set by user later
                'psa': card_info['psa'],
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            card_data.append(card)
            scraped_cards.append(card)
        
        logger.info(f"Successfully scraped and saved {len(scraped_cards)} cards")
        
        return jsonify({
            'message': f'Successfully scraped {len(scraped_cards)} cards from {tcg} - {expansion}',
            'scraped_cards': scraped_cards,
            'total_cards': len(card_data)
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
def get_cards():
    """Get all cards with optional filtering"""
    # Get query parameters
    expansion = request.args.get('expansion')
    rarity = request.args.get('rarity')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search = request.args.get('search', '').lower()
    
    filtered_cards = card_data.copy()
    
    # Apply filters
    if expansion:
        filtered_cards = [card for card in filtered_cards if card['expansion'].lower() == expansion.lower()]
    
    if rarity:
        filtered_cards = [card for card in filtered_cards if card['rarity'].lower() == rarity.lower()]
    
    if min_price is not None:
        filtered_cards = [card for card in filtered_cards if card['current_price'] >= min_price]
    
    if max_price is not None:
        filtered_cards = [card for card in filtered_cards if card['current_price'] <= max_price]
    
    if search:
        filtered_cards = [
            card for card in filtered_cards 
            if search in card['name'].lower() or 
               search in card['expansion'].lower() or
               search in str(card['number']).lower()
        ]
    
    return jsonify({
        'items': filtered_cards,
        'total': len(filtered_cards),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    """Get a specific card by ID"""
    card = next((card for card in card_data if card['id'] == card_id), None)
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    return jsonify(card)

@app.route('/api/cards/<int:card_id>/buy-price', methods=['PUT'])
def update_card_buy_price(card_id):
    """Update only the buy price of a specific card"""
    try:
        card_index = next((i for i, card in enumerate(card_data) if card['id'] == card_id), None)
        if card_index is None:
            return jsonify({'error': 'Card not found'}), 404
        
        data = request.get_json()
        if not data or 'buy_price' not in data:
            return jsonify({'error': 'Missing buy_price field'}), 400
        
        try:
            buy_price = float(data['buy_price'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid buy_price - must be a number'}), 400
        
        # Update only the buy price
        card_data[card_index]['price_bought'] = buy_price
        card_data[card_index]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        return jsonify({
            'message': 'Buy price updated successfully',
            'card': card_data[card_index]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cards/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    """Update an existing card"""
    try:
        card_index = next((i for i, card in enumerate(card_data) if card['id'] == card_id), None)
        if card_index is None:
            return jsonify({'error': 'Card not found'}), 404
        
        updated_data = request.get_json()
        updated_data['id'] = card_id  # Ensure ID doesn't change
        updated_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        card_data[card_index] = updated_data
        
        return jsonify({
            'message': 'Card updated successfully',
            'card': updated_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    """Delete a card"""
    card_index = next((i for i, card in enumerate(card_data) if card['id'] == card_id), None)
    if card_index is None:
        return jsonify({'error': 'Card not found'}), 404
    
    deleted_card = card_data.pop(card_index)
    
    return jsonify({
        'message': 'Card deleted successfully',
        'card': deleted_card
    })

@app.route('/api/cards', methods=['DELETE'])
def delete_all_cards():
    """Delete all cards from the collection"""
    global card_data
    cards_count = len(card_data)
    card_data = []
    
    return jsonify({
        'message': f'Successfully deleted all {cards_count} cards',
        'deleted_count': cards_count,
        'total_cards': 0
    })

@app.route('/api/assets/<asset_type>', methods=['DELETE'])
def delete_all_assets(asset_type):
    """Delete all assets of a specific type"""
    global card_data
    
    if asset_type == 'cards':
        cards_count = len(card_data)
        card_data = []
        return jsonify({
            'message': f'Successfully deleted all {cards_count} cards',
            'deleted_count': cards_count,
            'total_cards': 0
        })
    else:
        # For other asset types, return empty success for now
        return jsonify({
            'message': f'Successfully deleted all {asset_type}',
            'deleted_count': 0,
            'total_cards': 0
        })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the card collection"""
    if not card_data:
        return jsonify({
            'total_cards': 0,
            'total_value': 0,
            'average_price': 0,
            'expansions': [],
            'rarities': []
        })
    
    total_cards = len(card_data)
    total_value = sum(card['current_price'] for card in card_data)
    average_price = total_value / total_cards if total_cards > 0 else 0
    
    expansions = list(set(card['expansion'] for card in card_data))
    rarities = list(set(card['rarity'] for card in card_data))
    
    return jsonify({
        'total_cards': total_cards,
        'total_value': round(total_value, 2),
        'average_price': round(average_price, 2),
        'expansions': sorted(expansions),
        'rarities': sorted(rarities)
    })



@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """Get portfolio summary across all asset types"""
    try:
        logger.info("Portfolio summary endpoint called")
        logger.info(f"Total cards in storage: {len(card_data)}")
        
        # Calculate real portfolio data from stored cards
        total_cards = len(card_data)
        total_value = sum(card['current_price'] for card in card_data) if card_data else 0.0
        total_investment = sum(card.get('price_bought', 0) for card in card_data) if card_data else 0.0
        total_profit_loss = total_value - total_investment
        total_profit_loss_percentage = (total_profit_loss / total_investment * 100) if total_investment > 0 else 0.0
        
        logger.info(f"Calculated values: value={total_value}, investment={total_investment}, P&L={total_profit_loss}")
        
        # Get top and worst performers
        sorted_cards = sorted(card_data, key=lambda x: x['current_price'] - x.get('price_bought', 0), reverse=True) if card_data else []
        top_performers = sorted_cards[:5]
        worst_performers = sorted_cards[-5:] if len(sorted_cards) > 5 else []
        
        summary = {
            'total_portfolio_value': round(total_value, 2),
            'total_investment': round(total_investment, 2),
            'total_profit_loss': round(total_profit_loss, 2),
            'total_profit_loss_percentage': round(total_profit_loss_percentage, 2),
            'asset_breakdown': {
                'cards': {'value': round(total_value, 2), 'percentage': 100.0, 'count': total_cards}
            },
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

@app.route('/api/cards/rescrape', methods=['POST'])
def rescrape_card_prices():
    """Rescrape prices for all existing cards"""
    try:
        if not card_data:
            return jsonify({'status': 'error', 'message': 'No cards to rescrape'}), 400
        
        logger.info(f"Starting rescrape for {len(card_data)} cards")
        updated_cards = []
        errors = []
        
        for card in card_data:
            try:
                # Rescrape individual card
                scrape_params = {
                    'tcg': card['tcg'],
                    'expansion': card['expansion'],
                    'numbers': [card['number']],
                    'headless': True
                }
                
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
                    card.update({
                        'current_price': new_data['current_price'],
                        'supply': new_data['supply'],
                        'last_updated': datetime.now().isoformat()
                    })
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
def add_test_cards():
    """Add some test cards with prices for testing"""
    global card_data
    
    test_cards = [
        {
            'id': 999,
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
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 998,
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
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
    ]
    
    # Remove existing test cards
    card_data = [card for card in card_data if card['id'] not in [999, 998]]
    
    # Add new test cards
    card_data.extend(test_cards)
    
    return jsonify({
        'message': f'Added {len(test_cards)} test cards',
        'test_cards': test_cards,
        'total_cards': len(card_data)
    })

@app.route('/api/cards/scrape-single', methods=['POST'])
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
        existing_card = None
        for card in card_data:
            if (card['name'] == scraped_card['name'] and 
                card['expansion'] == scraped_card['expansion'] and
                card['tcg'] == scraped_card['tcg']):
                existing_card = card
                break
        
        if existing_card:
            # Update existing card with new price and add to history
            old_price = existing_card['current_price']
            existing_card['current_price'] = scraped_card['current_price']
            existing_card['last_updated'] = current_time
            
            # Initialize price history if it doesn't exist
            if 'price_history' not in existing_card:
                existing_card['price_history'] = [{
                    'price': old_price,
                    'timestamp': existing_card.get('last_updated', current_time),
                    'source': 'initial'
                }]
            
            # Add new price to history
            existing_card['price_history'].append({
                'price': scraped_card['current_price'],
                'timestamp': current_time,
                'source': 'scrape_update'
            })
            
            return jsonify({
                'success': True,
                'message': f'Card "{scraped_card["name"]}" updated successfully',
                'added': False,
                'card': existing_card
            })
        else:
            # Add new card with initial price history
            new_card = scraped_card.copy()
            new_card['id'] = len(card_data) + 1
            new_card['last_updated'] = current_time
            new_card['price_history'] = [{
                'price': scraped_card['current_price'],
                'timestamp': current_time,
                'source': 'initial_scrape'
            }]
            
            # Set default values if not present
            if 'price_bought' not in new_card:
                new_card['price_bought'] = 0.0
            if 'quantity' not in new_card:
                new_card['quantity'] = 1
            
            card_data.append(new_card)
            
            return jsonify({
                'success': True,
                'message': f'Card "{scraped_card["name"]}" added successfully',
                'added': True,
                'card': new_card
            })
            
    except Exception as e:
        logger.error(f"Error scraping single card: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to scrape card: {str(e)}'
        }), 500

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

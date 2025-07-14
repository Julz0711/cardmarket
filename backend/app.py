from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import re

# Try to import webdriver_manager, fallback if not available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

class CardMarketScraper:
    """Simplified CardMarket scraper integrated into Flask app"""
    
    def __init__(self, headless=True):
        self.driver = None
        self.setup_driver(headless)
    
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver with optimal settings"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            if WEBDRIVER_MANAGER_AVAILABLE:
                # Use webdriver-manager if available
                service = Service(ChromeDriverManager().install())
            else:
                # Fallback to system chromedriver or let selenium find it
                service = Service()
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            # If Chrome with service fails, try without service (let selenium auto-detect)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
            except Exception as e2:
                raise Exception(f"Failed to initialize Chrome WebDriver. Make sure Chrome browser and chromedriver are installed. Error: {e2}")
    
    def scrape_cards(self, tcg, expansion, numbers):
        """
        Scrape card entries from CardMarket using the original working logic
        
        Args:
            tcg: Trading Card Game (e.g., "Pokemon")
            expansion: Set/expansion name
            numbers: List of card numbers to scrape
        
        Returns:
            List of card dictionaries
        """
        cards = []
        try:
            # Navigate to CardMarket search page
            url = f"https://www.cardmarket.com/en/{tcg}/Products/Search?category=-1"
            logging.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(2)
            
            # Select expansion
            try:
                # Click expansion dropdown (index 1 based on original code)
                expansion_elements = self.driver.find_elements(By.XPATH, "//option[contains(@value, '51')]")
                if len(expansion_elements) > 1:
                    expansion_elements[1].click()
                else:
                    logging.warning("Could not find expansion dropdown")
                    return cards
                
                # Select specific expansion
                expansion_option = self.driver.find_element(By.XPATH, f"//option[normalize-space(.)='{expansion}']")
                expansion_option.click()
                
                # Click search button
                search_buttons = self.driver.find_elements(By.XPATH, "//input[contains(@class, 'btn btn-primary')]")
                if search_buttons:
                    search_buttons[0].click()
                    time.sleep(2)
                else:
                    logging.warning("Could not find search button")
                    return cards
                    
            except NoSuchElementException as e:
                logging.error(f"Could not navigate to expansion '{expansion}': {e}")
                return cards
            
            # Save the search URL for reuse
            spec_url = self.driver.current_url
            logging.info(f"Base search URL: {spec_url}")
            
            # Scrape each card number
            for number in numbers:
                try:
                    logging.info(f"Scraping card number: {number}")
                    
                    # Navigate back to search page
                    self.driver.get(spec_url)
                    time.sleep(1)
                    
                    # Enter card number in search
                    search_inputs = self.driver.find_elements(By.NAME, "searchString")
                    if len(search_inputs) > 1:
                        search_inputs[1].clear()
                        search_inputs[1].send_keys(str(number))
                    else:
                        logging.warning(f"Could not find search input for card {number}")
                        continue
                    
                    # Click search
                    search_buttons = self.driver.find_elements(By.XPATH, "//input[contains(@class, 'btn btn-primary')]")
                    if search_buttons:
                        search_buttons[0].click()
                        time.sleep(2)
                    else:
                        logging.warning(f"Could not find search button for card {number}")
                        continue
                    
                    # Extract card data
                    card_data = self._extract_card_data(tcg, expansion, number)
                    if card_data:
                        cards.append(card_data)
                        logging.info(f"Successfully scraped: {card_data['name']} (#{card_data['number']})")
                    else:
                        logging.warning(f"Failed to extract data for card {number}")
                        
                except Exception as e:
                    logging.error(f"Error scraping card {number}: {e}")
                    continue
            
            return cards
            
        except Exception as e:
            logging.error(f"Error in scrape_cards: {e}")
            return cards
    
    def _extract_card_data(self, tcg, expansion, target_number):
        """Extract card data from current page using original logic"""
        try:
            # Extract number
            number_elements = self.driver.find_elements(
                By.XPATH, 
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col')]//div[contains(@class, 'row g-0')]//div"
            )
            if len(number_elements) > 3:
                number_text = number_elements[3].text.strip()
                number = int(''.join(filter(str.isdigit, number_text)))
            else:
                logging.warning("Could not find card number")
                number = target_number
            
            # Extract name
            name_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col')]//div[contains(@class, 'row g-0')]//a"
            )
            if name_elements:
                name = name_elements[0].text.strip()
            else:
                logging.warning("Could not find card name")
                name = f"Card #{target_number}"
            
            # Extract rarity using BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            rarity_element = soup.find("svg", attrs={"aria-label": True})
            if rarity_element:
                rarity = rarity_element["aria-label"]
            else:
                logging.warning("Could not find rarity")
                rarity = "Unknown"
            
            # Extract supply
            supply_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col-availability')]"
            )
            if supply_elements:
                supply_text = supply_elements[0].text.strip()
                supply = int(''.join(filter(str.isdigit, supply_text)))
            else:
                logging.warning("Could not find supply")
                supply = 0
            
            # Extract current price
            price_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'table-body')]//div//div[contains(@class, 'col-price')]"
            )
            if price_elements:
                price_text = price_elements[0].text.strip()
                # Remove currency symbol and convert comma to dot
                price_clean = price_text[:-2].replace(",", ".")
                current_price = float(price_clean)
            else:
                logging.warning("Could not find price")
                current_price = 0.0
            
            return {
                "tcg": tcg,
                "expansion": expansion,
                "number": str(number),
                "name": name,
                "rarity": rarity,
                "supply": supply,
                "current_price": current_price,
                "price_bought": "-",
                "psa": "raw"
            }
            
        except Exception as e:
            logging.error(f"Error extracting card data: {e}")
            return None
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for scraped cards
card_data = []

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
        'cards': filtered_cards,
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
        'expansions': expansions,
        'rarities': rarities
    })

@app.route('/api/scrape', methods=['POST'])
def scrape_cards():
    """Scrape cards from CardMarket and add to collection"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['tcg', 'expansion', 'numbers']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        tcg = data['tcg']
        expansion = data['expansion']
        numbers = data['numbers']
        headless = data.get('headless', True)
        
        logger.info(f"Starting scrape for {tcg} - {expansion}, numbers: {numbers}")
        
        # Initialize scraper
        scraper = CardMarketScraper(headless=headless)
        
        try:
            # Scrape data using your scraper
            scraped_cards_data = scraper.scrape_cards(tcg, expansion, numbers)
            
            if not scraped_cards_data:
                return jsonify({'error': 'No data was scraped'}), 400
            
            # Convert scraped data to card_data format and add to collection
            global card_data
            scraped_cards = []
            
            for card_info in scraped_cards_data:
                # Generate new ID
                new_id = max([card['id'] for card in card_data], default=0) + 1
                
                card = {
                    'id': new_id,
                    'tcg': card_info['tcg'],
                    'expansion': card_info['expansion'],
                    'number': int(card_info['number']),
                    'name': card_info['name'],
                    'rarity': card_info['rarity'],
                    'supply': int(card_info['supply']),
                    'current_price': float(card_info['current_price']),
                    'price_bought': card_info['price_bought'],
                    'psa': card_info['psa'],
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                
                card_data.append(card)
                scraped_cards.append(card)
            
            logger.info(f"Successfully scraped {len(scraped_cards)} cards")
            
            return jsonify({
                'message': f'Successfully scraped {len(scraped_cards)} cards',
                'scraped_cards': scraped_cards,
                'total_cards': len(card_data)
            })
            
        finally:
            scraper.close()
            
    except Exception as e:
        logger.error(f"Error in scrape_cards: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape/status', methods=['GET'])
def scraper_status():
    """Check if scraper dependencies are available"""
    try:
        # Try to import selenium and beautifulsoup
        from selenium import webdriver
        from bs4 import BeautifulSoup
        
        return jsonify({
            'status': 'ready',
            'selenium_available': True,
            'beautifulsoup_available': True,
            'message': 'Scraper is ready to use'
        })
        
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'selenium_available': False,
            'beautifulsoup_available': False,
            'message': f'Missing dependencies: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("🎴 CardMarket Scraper API Starting...")
    print("📊 Ready to scrape cards from CardMarket.com")
    print("🌐 Server will be available at http://localhost:5000")
    print("📖 API Documentation:")
    print("  GET    /api/cards              - Get all scraped cards (with optional filters)")
    print("  GET    /api/cards/:id          - Get specific card")
    print("  PUT    /api/cards/:id          - Update card")
    print("  DELETE /api/cards/:id          - Delete card")
    print("  DELETE /api/cards              - Delete all cards")
    print("  GET    /api/stats              - Get collection statistics")
    print("  POST   /api/scrape             - Scrape cards from CardMarket")
    print("  GET    /api/scrape/status      - Check scraper status")
    print("  GET    /api/health             - Health check")
    print("")
    print("🤖 CardMarket Scraper Integration:")
    print("  - Selenium WebDriver for automated browsing")
    print("  - BeautifulSoup for HTML parsing")
    print("  - Real-time price and availability data")
    print("  - No hardcoded data - everything is scraped live!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

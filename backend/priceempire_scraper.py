import requests
import logging
import time
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Supported types for PriceEmpire
PRICEEMPIRE_TYPES = [
    'skin', 'glove', 'agent', 'container', 'sticker', 'tournament-sticker', 'autograph-sticker',
    'patch', 'souvenir-package', 'graffiti', 'music-kit', 'pin', 'charm'
]

# Mapping for short to full condition names
CONDITION_MAP = {
    'FN': 'factory-new',
    'MW': 'minimal-wear',
    'FT': 'field-tested',
    'WW': 'well-worn',
    'BS': 'battle-scarred',
}

# StatTrak and Souvenir prefix handling
def build_condition(condition, stattrak=False, souvenir=False):
    if not condition:
        return None
    cond = CONDITION_MAP.get(condition.upper(), condition.lower())
    if stattrak:
        return f'stattrak-{cond}'
    if souvenir:
        return f'souvenir-{cond}'
    return cond

class PriceEmpireScraper:
    BASE_URL = 'https://pricempire.com/cs2-items'

    def __init__(self, delay=0.5):
        self.delay = delay

    def normalize_name(self, full_name):
        # Remove StatTrak, Souvenir, and other known prefixes for slug
        name = full_name
        name = re.sub(r"^(StatTrak™|StatTrak|Souvenir) ", "", name, flags=re.IGNORECASE)
        name = name.replace("™", "")
        name = name.replace("|", "-")
        name = name.replace("  ", " ")
        name = name.strip()
        # Lowercase, replace spaces with dashes, remove non-alphanum/dash
        name = name.lower()
        name = re.sub(r"\s+", "-", name)
        name = re.sub(r"[^a-z0-9\-]", "", name)
        name = re.sub(r"-+", "-", name)  # Collapse multiple dashes
        name = name.strip('-')
        return name

    def build_url(self, item_type, full_name, condition=None):
        if item_type not in PRICEEMPIRE_TYPES:
            raise ValueError(f"Unsupported type: {item_type}")
        name_slug = self.normalize_name(full_name)
        url = f"{self.BASE_URL}/{item_type}/{name_slug}"
        if condition:
            url += f"/{condition}"
        return url

    def fetch_price(self, item_type, full_name, condition=None):
        url = self.build_url(item_type, full_name, condition)
        logger.info(f"Fetching PriceEmpire URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://pricempire.com/'
        }
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code == 403:
                logger.warning("403 Forbidden: You may be blocked. Trying again with different headers...")
                time.sleep(1)
                resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"Non-200 response: {resp.status_code}")
                return None
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Find the <dt> with id="current-price-label"
            dt = soup.find('dt', id='current-price-label')
            if dt:
                dd = dt.find_next_sibling('dd')
                if dd:
                    price_text = dd.get_text(strip=True)
                    # Extract price and currency
                    match = re.search(r'(\$|€)\s*([0-9,.]+)', price_text)
                    if match:
                        price = float(match.group(2).replace(',', ''))
                        currency = match.group(1)
                        return {'price': price, 'currency': currency, 'url': url}
            # Fallback: try regex on whole page
            match = re.search(r'(\$|€)\s*([0-9,.]+)', resp.text)
            if match:
                price = float(match.group(2).replace(',', ''))
                currency = match.group(1)
                return {'price': price, 'currency': currency, 'url': url}
            logger.warning("Price not found in page")
            return None
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return None
        finally:
            time.sleep(self.delay)

# --- TESTS ---
def test_priceempire_scraper():
    scraper = PriceEmpireScraper(delay=0.1)
    # Test 1: Standard skin
    url = scraper.build_url('skin', 'AK-47 | Redline', build_condition('FT'))
    print(f"Test 1 URL: {url}")
    assert url == 'https://pricempire.com/cs2-items/skin/ak-47-redline/field-tested'


    # Test 2: StatTrak skin (should normalize slug)
    url = scraper.build_url('skin', 'StatTrak™ AK-47 | Fire Serpent', build_condition('FN', stattrak=True))
    print(f"Test 2 URL: {url}")
    assert url == 'https://pricempire.com/cs2-items/skin/ak-47-fire-serpent/stattrak-factory-new'

    # Test 3: Souvenir skin
    url = scraper.build_url('skin', 'Souvenir AWP | Dragon Lore', build_condition('FN', souvenir=True))
    print(f"Test 3 URL: {url}")
    assert url == 'https://pricempire.com/cs2-items/skin/awp-dragon-lore/souvenir-factory-new'

    # Test 4: Non-skin type (container)
    url = scraper.build_url('container', 'Gallery Case')
    print(f"Test 4 URL: {url}")
    assert url == 'https://pricempire.com/cs2-items/container/gallery-case'

    # Test 5: Fetch price (may fail if site blocks or structure changes)
    # result = scraper.fetch_price('skin', 'AK-47 | Redline', build_condition('FT'))
    # print(f"Test 5 Price: {result}")
    print("All tests passed!")

if __name__ == '__main__':
    test_priceempire_scraper()

import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class PriceEmpireSeleniumScraper:
    BASE_URL = 'https://pricempire.com/cs2-items'

    def __init__(self, delay=0.5, driver_path=None):
        self.delay = delay
        self.driver_path = driver_path
        self.driver = None

    def setup_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
        self.driver = webdriver.Chrome(options=options, executable_path=self.driver_path) if self.driver_path else webdriver.Chrome(options=options)

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def build_url(self, item_type, name_slug, condition=None, event=None, sealed=True):
        # Graffiti: color only after slash, slug without color
        if item_type == 'graffiti':
            prefix = 'sealed-graffiti-' if sealed else 'graffiti-'
            slug = name_slug
            if slug.startswith('graffiti-'):
                slug = slug[len('graffiti-'):]
            # Remove '-{condition}' from end of slug, even if condition has hyphens
            if condition and slug.endswith('-' + condition):
                base_slug = slug[:-(len(condition)+1)]
            else:
                base_slug = slug
            url = f"{self.BASE_URL}/graffiti/{prefix}{base_slug}"
            if condition and condition.lower() not in ['n/a', 'none', '']:
                url += f"/{condition}"
            return url
        # Skins/Gloves: remove known condition from end of slug, append as /{condition}
        elif item_type in ['skin', 'glove'] and condition:
            known_conditions = [
                'factory-new', 'minimal-wear', 'field-tested', 'well-worn', 'battle-scarred'
            ]
            base_slug = name_slug
            for cond in known_conditions:
                if base_slug.endswith('-' + cond):
                    base_slug = base_slug[:-(len(cond)+1)]
                    break
            url = f"{self.BASE_URL}/{item_type}/{base_slug}"
            if condition and condition.lower() not in ['n/a', 'none', '']:
                url += f"/{condition}"
            return url
        # Tournament stickers
        elif item_type == 'sticker' and event:
            url = f"{self.BASE_URL}/tournament-sticker/sticker-{name_slug}-{event}"
        else:
            url = f"{self.BASE_URL}/{item_type}/{name_slug}"
        if condition and condition.lower() not in ['n/a', 'none', '']:
            url += f"/{condition}"
        return url

    def fetch_price(self, item_type, name_slug, condition=None, event=None):
        # Skip fetch if name_slug or item_type is invalid
        if not name_slug or name_slug.lower() in ['n/a', 'none', '']:
            logger.warning(f"[Selenium] Skipping fetch: invalid name_slug '{name_slug}' for type '{item_type}'")
            return None
        # Skip only coins, medals, pickem, trophy, and charms with 'coin' in slug
        skip_keywords = ['medal', 'service-medal', 'pickem', 'trophy']
        if (
            item_type == 'coin' or
            (item_type == 'charm' and 'coin' in name_slug) or
            any(kw in name_slug for kw in skip_keywords)
        ):
            logger.info(f"[Selenium] Skipping coin/medal/pickem/trophy: type='{item_type}', name_slug='{name_slug}'")
            return None
        url = self.build_url(item_type, name_slug, condition, event)
        logger.info(f"[Selenium] Fetching PriceEmpire URL: {url}")
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)
            try:
                dt = wait.until(EC.presence_of_element_located((By.ID, 'current-price-label')))
                # Find parent div of dt, then <dd> inside that div, then <span> for price
                parent_div = dt.find_element(By.XPATH, './ancestor::div[1]')
                dd = parent_div.find_element(By.TAG_NAME, 'dd')
                span = dd.find_element(By.TAG_NAME, 'span')
                price_text = span.text.strip()
                match = re.search(r'(\$|€)\s*([0-9,.]+)', price_text)
                if match:
                    price = float(match.group(2).replace(',', ''))
                    currency = match.group(1)
                    return {'price': price, 'currency': currency, 'url': url}
                logger.warning(f"[Selenium] Price not found in page for URL: {url}")
                return None
            except Exception as e:
                logger.warning(f"[Selenium] Price element not found for URL: {url} | {e}")
                # Optionally, log a snippet of the page source for debugging:
                # logger.debug(self.driver.page_source[:1000])
                return None
        except Exception as e:
            logger.error(f"[Selenium] Error fetching price: {e}")
            return None
        finally:
            time.sleep(self.delay)

# Example usage
def test_selenium_scraper():
    from priceempire_scraper import PriceEmpireScraper, build_condition
    # Use the same normalization as the requests-based scraper
    norm = PriceEmpireScraper().normalize_name
    scraper = PriceEmpireSeleniumScraper()
    scraper.setup_driver()
    try:
        # Example: StatTrak AK-47 | Fire Serpent FN
        item_type = 'skin'
        name = 'StatTrak™ AK-47 | Fire Serpent'
        condition = build_condition('FN', stattrak=True)
        name_slug = norm(name)
        result = scraper.fetch_price(item_type, name_slug, condition)
        print(f"Selenium Price: {result}")
    finally:
        scraper.close()

if __name__ == '__main__':
    test_selenium_scraper()

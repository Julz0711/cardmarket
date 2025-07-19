import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class SkinSearchSeleniumScraper:
    def fetch_price(self, item_type: str, url: str) -> Optional[Dict[str, str]]:
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)
            # Weapons, Knives, Gloves, Cases, Packages, Capsules
            if item_type in ['weapon', 'knife', 'glove', 'case', 'souvenir_package', 'capsule']:
                prices_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'prices')))
                price_elems = prices_div.find_elements(By.TAG_NAME, 'a')
                prices = []
                for a in price_elems:
                    price_text = a.text.strip()
                    match = re.search(r'([0-9,.]+)€', price_text)
                    if match:
                        price = float(match.group(1).replace(',', ''))
                        prices.append(price)
                if prices:
                    return {'price': str(min(prices)), 'currency': '€', 'url': url}
                logger.warning(f"[SkinSearch] No price found in <div class='prices'> for URL: {url}")
                return None
            # Stickers, Charms, Agents, Patches, Pins, Graffiti
            else:
                try:
                    td = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'price')))
                    a = td.find_element(By.TAG_NAME, 'a')
                    price_text = a.text.strip()
                except Exception:
                    # Sometimes price is in <span> inside <td class='price'>
                    span = td.find_element(By.TAG_NAME, 'span')
                    price_text = span.text.strip()
                match = re.search(r'([0-9,.]+)€', price_text)
                if match:
                    price = float(match.group(1).replace(',', ''))
                    return {'price': str(price), 'currency': '€', 'url': url}
                logger.warning(f"[SkinSearch] No price found in <td class='price'> for URL: {url}")
                return None
        except Exception as e:
            logger.error(f"[SkinSearch] Error fetching price: {e}")
            return None
        finally:
            time.sleep(self.delay)
    BASE_URL = 'https://skinsearch.com'

    def __init__(self, delay: float = 0.5, driver_path: Optional[str] = None):
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

    def build_url(self, item_type: str, **kwargs) -> str:
        # Weapons
        if item_type == 'weapon':
            weapon = kwargs.get('weapon')
            skin = kwargs.get('skin')
            condition = kwargs.get('condition', 'FN')
            variant = kwargs.get('variant', 'normal')
            url = f"{self.BASE_URL}/item/{weapon}/{skin}/{condition}/{variant}"
            return url
        # Gloves
        elif item_type == 'glove':
            glove_type = kwargs.get('glove_type')
            skin = kwargs.get('skin')
            condition = kwargs.get('condition', 'FN')
            url = f"{self.BASE_URL}/item/{glove_type}/{skin}/{condition}/normal"
            return url
        # Knives
        elif item_type == 'knife':
            knife_type = kwargs.get('knife_type')
            skin = kwargs.get('skin')
            condition = kwargs.get('condition', 'FN')
            variant = kwargs.get('variant', 'normal')
            url = f"{self.BASE_URL}/item/{knife_type}/{skin}/{condition}/{variant}"
            return url
        # Cases, Souvenir Packages
        elif item_type in ['case', 'souvenir_package']:
            case_name = kwargs.get('case_name')
            url = f"{self.BASE_URL}/crate/{case_name}"
            return url
        # Capsules
        elif item_type == 'capsule':
            capsule_name = kwargs.get('capsule_name')
            url = f"{self.BASE_URL}/capsule/{capsule_name}"
            return url
        # Stickers
        elif item_type == 'sticker':
            sticker_name = kwargs.get('sticker_name')
            url = f"{self.BASE_URL}/item/sticker/{sticker_name}"
            return url
        # Charms
        elif item_type == 'charm':
            charm_name = kwargs.get('charm_name')
            url = f"{self.BASE_URL}/item/charm/{charm_name}"
            return url
        # Music Kits
        elif item_type == 'music_kit':
            music_kit_name = kwargs.get('music_kit_name')
            url = f"{self.BASE_URL}/item/music_kit/{music_kit_name}"
            return url
        # Agents
        elif item_type == 'agent':
            agent_name = kwargs.get('agent_name')
            url = f"{self.BASE_URL}/item/agent/{agent_name}"
            return url
        # Patches, Pins, Graffiti
        elif item_type in ['patch', 'pin', 'graffiti']:
            item_name = kwargs.get('item_name')
            url = f"{self.BASE_URL}/item/{item_type}/{item_name}"
            return url
        else:
            raise ValueError(f"Unknown item_type: {item_type}")

def map_steam_item_to_skinsearch_args(item: dict) -> tuple:
    """Map a steam item dict to SkinSearch item_type and build_url kwargs."""
    category = item.get('item_category', '').lower()
    name = item.get('name', '')
    condition = item.get('condition', 'FN')
    import re as _re
    def norm(s):
        s = s.lower()
        s = s.replace('’', '').replace("'", '').replace('"', '')
        s = s.replace('™', '').replace('★', '').replace('|', '').replace('(', '').replace(')', '')
        s = _re.sub(r'[^a-z0-9_ ]', '', s)
        s = s.replace(' ', '_').replace('-', '_').replace('__', '_')
        return s.strip('_')
    def fetch_price(self, item_type: str, url: str) -> Optional[Dict[str, str]]:
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)
            # Weapons, Knives, Gloves, Cases, Packages, Capsules
            if item_type in ['weapon', 'knife', 'glove', 'case', 'souvenir_package', 'capsule']:
                prices_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'prices')))
                price_elems = prices_div.find_elements(By.TAG_NAME, 'a')
                prices = []
                for a in price_elems:
                    price_text = a.text.strip()
                    match = re.search(r'([0-9,.]+)€', price_text)
                    if match:
                        price = float(match.group(1).replace(',', ''))
                        prices.append(price)
                if prices:
                    return {'price': str(min(prices)), 'currency': '€', 'url': url}
                logger.warning(f"[SkinSearch] No price found in <div class='prices'> for URL: {url}")
                return None
            # Stickers, Charms, Agents, Patches, Pins, Graffiti
            else:
                td = None
                try:
                    td = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'price')))
                    a = td.find_element(By.TAG_NAME, 'a')
                    price_text = a.text.strip()
                except Exception:
                    if td:
                        try:
                            span = td.find_element(By.TAG_NAME, 'span')
                            price_text = span.text.strip()
                        except Exception:
                            price_text = ''
                    else:
                        price_text = ''
                match = re.search(r'([0-9,.]+)€', price_text)
                if match:
                    price = float(match.group(1).replace(',', ''))
                    return {'price': str(price), 'currency': '€', 'url': url}
                logger.warning(f"[SkinSearch] No price found in <td class='price'> for URL: {url}")
                return None
        except Exception as e:
            logger.error(f"[SkinSearch] Error fetching price: {e}")
            return None
        finally:
            time.sleep(self.delay)
    args = {}
    if category == 'weapon':
        weapon, skin = '', ''
        if '|' in name:
            parts = name.split('|')
            weapon = norm(parts[0])
            skin = norm(parts[1])
        else:
            weapon = norm(name)
            skin = ''
        variant = 'normal'
        if 'stattrak' in name.lower():
            variant = 'stattrak'
        elif 'souvenir' in name.lower():
            variant = 'souvenir'
        args = {'weapon': weapon, 'skin': skin, 'condition': condition, 'variant': variant}
    elif category == 'glove':
        glove_type, skin = '', ''
        if '|' in name:
            parts = name.split('|')
            glove_type = norm(parts[0])
            skin = norm(parts[1])
        else:
            glove_type = norm(name)
            skin = ''
        args = {'glove_type': glove_type, 'skin': skin, 'condition': condition}
    elif category == 'knife':
        knife_type, skin = '', ''
        if '|' in name:
            parts = name.split('|')
            knife_type = norm(parts[0])
            skin = norm(parts[1])
        else:
            knife_type = norm(name)
            skin = ''
        variant = 'normal'
        if 'stattrak' in name.lower():
            variant = 'stattrak'
        args = {'knife_type': knife_type, 'skin': skin, 'condition': condition, 'variant': variant}
    elif category == 'case':
        args = {'case_name': norm(name)}
    elif category == 'souvenir_package':
        args = {'case_name': norm(name)}
    elif category == 'capsule':
        args = {'capsule_name': norm(name)}
    elif category == 'sticker':
        args = {'sticker_name': norm(name)}
    elif category == 'charm':
        args = {'charm_name': norm(name)}
    elif category == 'music_kit':
        args = {'music_kit_name': norm(name)}
    elif category == 'agent':
        args = {'agent_name': norm(name)}
    elif category in ['patch', 'pin', 'graffiti']:
        args = {'item_name': norm(name)}
    else:
        return None, None
    return category, args

def batch_update_steam_prices(steam_items):
    """Example: Update prices for a list of steam items from the database."""
    scraper = SkinSearchSeleniumScraper()
    scraper.setup_driver()
    try:
        for item in steam_items:
            item_type, url_args = map_steam_item_to_skinsearch_args(item)
            if item_type and url_args:
                url = scraper.build_url(item_type, **url_args)
                price_result = scraper.fetch_price(item_type, url)
                print(f"{item['name']} | {url} | Price: {price_result}")
                # Here you could update the database with price_result['price']
    finally:
        scraper.close()
    BASE_URL = 'https://skinsearch.com'

    def __init__(self, delay: float = 0.5, driver_path: Optional[str] = None):
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

    def build_url(self, item_type: str, **kwargs) -> str:
        # Weapons
        if item_type == 'weapon':
            weapon = kwargs.get('weapon')
            skin = kwargs.get('skin')
            condition = kwargs.get('condition', 'FN')
            variant = kwargs.get('variant', 'normal')
            url = f"{self.BASE_URL}/item/{weapon}/{skin}/{condition}/{variant}"
            return url
        # Gloves
        elif item_type == 'glove':
            glove_type = kwargs.get('glove_type')
            skin = kwargs.get('skin')
            condition = kwargs.get('condition', 'FN')
            url = f"{self.BASE_URL}/item/{glove_type}/{skin}/{condition}/normal"
            return url
        # Knives
        elif item_type == 'knife':
            knife_type = kwargs.get('knife_type')
            skin = kwargs.get('skin')
            condition = kwargs.get('condition', 'FN')
            variant = kwargs.get('variant', 'normal')
            url = f"{self.BASE_URL}/item/{knife_type}/{skin}/{condition}/{variant}"
            return url
        # Cases, Souvenir Packages
        elif item_type in ['case', 'souvenir_package']:
            case_name = kwargs.get('case_name')
            url = f"{self.BASE_URL}/crate/{case_name}"
            return url
        # Capsules
        elif item_type == 'capsule':
            capsule_name = kwargs.get('capsule_name')
            url = f"{self.BASE_URL}/capsule/{capsule_name}"
            return url
        # Stickers
        elif item_type == 'sticker':
            sticker_name = kwargs.get('sticker_name')
            url = f"{self.BASE_URL}/item/sticker/{sticker_name}"
            return url
        # Charms
        elif item_type == 'charm':
            charm_name = kwargs.get('charm_name')
            url = f"{self.BASE_URL}/item/charm/{charm_name}"
            return url
        # Music Kits
        elif item_type == 'music_kit':
            music_kit_name = kwargs.get('music_kit_name')
            url = f"{self.BASE_URL}/item/music_kit/{music_kit_name}"
            return url
        # Agents
        elif item_type == 'agent':
            agent_name = kwargs.get('agent_name')
            url = f"{self.BASE_URL}/item/agent/{agent_name}"
            return url
        # Patches, Pins, Graffiti
        elif item_type in ['patch', 'pin', 'graffiti']:
            item_name = kwargs.get('item_name')
            url = f"{self.BASE_URL}/item/{item_type}/{item_name}"
            return url
        else:
            raise ValueError(f"Unknown item_type: {item_type}")

    def fetch_price(self, item_type: str, url: str) -> Optional[Dict[str, str]]:
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)
            # Weapons, Knives, Gloves, Cases, Packages, Capsules
            if item_type in ['weapon', 'knife', 'glove', 'case', 'souvenir_package', 'capsule']:
                prices_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'prices')))
                price_elems = prices_div.find_elements(By.TAG_NAME, 'a')
                prices = []
                for a in price_elems:
                    price_text = a.text.strip()
                    match = re.search(r'([0-9,.]+)€', price_text)
                    if match:
                        price = float(match.group(1).replace(',', ''))
                        prices.append(price)
                if prices:
                    return {'price': str(min(prices)), 'currency': '€', 'url': url}
                logger.warning(f"[SkinSearch] No price found in <div class='prices'> for URL: {url}")
                return None
            # Stickers, Charms, Agents, Patches, Pins, Graffiti
            else:
                try:
                    td = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'price')))
                    a = td.find_element(By.TAG_NAME, 'a')
                    price_text = a.text.strip()
                except Exception:
                    # Sometimes price is in <span> inside <td class='price'>
                    span = td.find_element(By.TAG_NAME, 'span')
                    price_text = span.text.strip()
                match = re.search(r'([0-9,.]+)€', price_text)
                if match:
                    price = float(match.group(1).replace(',', ''))
                    return {'price': str(price), 'currency': '€', 'url': url}
                logger.warning(f"[SkinSearch] No price found in <td class='price'> for URL: {url}")
                return None
        except Exception as e:
            logger.error(f"[SkinSearch] Error fetching price: {e}")
            return None
        finally:
            time.sleep(self.delay)

# Example usage
def test_skinsearch_scraper():
    scraper = SkinSearchSeleniumScraper()
    scraper.setup_driver()
    try:
        # Example: weapon
        url = scraper.build_url('weapon', weapon='ak-47', skin='redline', condition='FN', variant='normal')
        result = scraper.fetch_price('weapon', url)
        print(f"SkinSearch Price: {result}")
    finally:
        scraper.close()

if __name__ == '__main__':
    test_skinsearch_scraper()

import requests
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict
# Playwright imports
import asyncio
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class PriceInfo:
    price: Optional[float]
    currency: str = '€'
    url: Optional[str] = None
    market: Optional[str] = None

class SkinSearchScraper:
    name = "SkinSearch"
    def __init__(self):
        self.is_running = False
        self.last_used = None
    def map_steam_item_to_skinsearch_args(self, item: dict) -> tuple:
        category = item.get('item_category', '').lower()
        name = item.get('name', '')
        condition = item.get('condition', 'FN')
        args = {}
        item_type = item.get('item_type', '').lower()

        # --- Prioritize mapping for capsules, cases, and souvenir packages regardless of category ---
        if 'capsule' in name.lower():
            args = {'capsule_name': self.norm(name, remove_condition=True)}
            return 'capsule', args
        if (
            'autograph capsule' in item_type
            or 'patch pack' in item_type
            or 'sticker capsule' in item_type
            or 'capsule' in item_type
            or ('foil' in item_type and 'capsule' in item_type)
        ):
            args = {'capsule_name': self.norm(name, remove_condition=True)}
            return 'capsule', args
        if 'souvenir package' in item_type:
            args = {'case_name': self.norm(name, remove_condition=True)}
            return 'souvenir_package', args
        if 'base grade container' in item_type or item_type in ['case', 'container'] or category == 'case':
            args = {'case_name': self.norm(name, remove_condition=True)}
            return 'case', args
        if category == 'weapon':
            if item_type in ['base grade container', 'case', 'container']:
                return None, None
            weapon, skin = '', ''
            clean_name = name
            if name.lower().startswith('souvenir '):
                clean_name = name[len('souvenir '):]
            if name.lower().startswith('stattrak™ '):
                clean_name = name[len('stattrak™ '):]
            is_doppler, doppler_type = self.is_doppler_item(clean_name)
            if is_doppler:
                if '|' in clean_name:
                    parts = clean_name.split('|')
                    weapon = self.norm(parts[0], remove_condition=True)
                    detected_phase = self.detect_doppler_phase(item)
                    if detected_phase:
                        if doppler_type == 'gamma_doppler':
                            skin = f"gamma_doppler/{detected_phase}"
                        else:
                            skin = f"doppler/{detected_phase}"
                    else:
                        if doppler_type == 'gamma_doppler':
                            skin = f"gamma_doppler/phase_1"
                        else:
                            skin = f"doppler/phase_1"
                        args = {'weapon': weapon, 'skin': skin, 'condition': condition, 'variant': 'normal', '_doppler_fallback': True, '_doppler_type': doppler_type}
                else:
                    weapon = self.norm(clean_name, remove_condition=True)
                    skin = 'doppler/phase_1'
            else:
                if '|' in clean_name:
                    parts = clean_name.split('|')
                    weapon = self.norm(parts[0], remove_condition=True)
                    raw_skin = parts[1].strip()
                    skin_no_cond = re.sub(r'\s*\b(factory new|minimal wear|field-tested|well-worn|battle-scarred|fn|mw|ft|ww|bs)\b', '', raw_skin, flags=re.IGNORECASE)
                    skin_no_cond = re.sub(r'(_factory_new|_minimal_wear|_field_tested|_well_worn|_battle_scarred|_fn|_mw|_ft|_ww|_bs)$', '', skin_no_cond.lower())
                    skin = self.norm(skin_no_cond, remove_condition=True)
                else:
                    weapon = self.norm(clean_name, remove_condition=True)
                    skin = ''
            variant = 'normal'
            if 'stattrak' in name.lower():
                variant = 'stattrak'
            elif 'souvenir' in name.lower():
                variant = 'souvenir'
            if 'args' not in locals() or not args:
                args = {'weapon': weapon, 'skin': skin, 'condition': condition, 'variant': variant}
        elif category == 'glove' or category == 'gloves':
            glove_type, skin = '', ''
            if '|' in name:
                parts = name.split('|')
                glove_type = self.norm(parts[0], remove_condition=True)
                raw_skin = parts[1].strip()
                skin_no_cond = re.sub(r'\s*\([^)]+\)$', '', raw_skin)
                skin_no_cond = re.sub(r'\s*\b(factory new|minimal wear|field-tested|well-worn|battle-scarred|fn|mw|ft|ww|bs)\b', '', skin_no_cond, flags=re.IGNORECASE)
                skin = self.norm(skin_no_cond, remove_condition=True)
            else:
                glove_type = self.norm(name, remove_condition=True)
                skin = ''
            args = {'glove_type': glove_type, 'skin': skin, 'condition': condition}
        elif category == 'knife':
            knife_type, skin = '', ''
            is_doppler, doppler_type = self.is_doppler_item(name)
            if is_doppler:
                if '|' in name:
                    parts = name.split('|')
                    knife_type = self.norm(parts[0], remove_condition=True)
                    detected_phase = self.detect_doppler_phase(item)
                    if detected_phase:
                        if doppler_type == 'gamma_doppler':
                            skin = f"gamma_doppler/{detected_phase}"
                        else:
                            skin = f"doppler/{detected_phase}"
                    else:
                        if doppler_type == 'gamma_doppler':
                            skin = f"gamma_doppler/phase_1"
                        else:
                            skin = f"doppler/phase_1"
                        variant = 'normal'
                        if 'stattrak' in name.lower():
                            variant = 'stattrak'
                        args = {'knife_type': knife_type, 'skin': skin, 'condition': condition, 'variant': variant, '_doppler_fallback': True, '_doppler_type': doppler_type}
                else:
                    knife_type = self.norm(name, remove_condition=True)
                    skin = 'doppler/phase_1'
            else:
                if '|' in name:
                    parts = name.split('|')
                    knife_type = self.norm(parts[0], remove_condition=True)
                    skin = self.norm(parts[1], remove_condition=True)
                else:
                    knife_type = self.norm(name, remove_condition=True)
                    skin = ''
            variant = 'normal'
            if 'stattrak' in name.lower():
                variant = 'stattrak'
            if 'args' not in locals() or not args:
                args = {'knife_type': knife_type, 'skin': skin, 'condition': condition, 'variant': variant}
        elif category == 'case':
            args = {'case_name': self.norm(name, remove_condition=True)}
        elif category == 'souvenir_package':
            args = {'case_name': self.norm(name, remove_condition=True)}
        elif category == 'capsule':
            args = {'capsule_name': self.norm(name, remove_condition=True)}
        elif category == 'sticker':
            args = {'sticker_name': self.norm(name, remove_condition=True, remove_prefix='sticker_')}
        elif category == 'charm':
            args = {'charm_name': self.norm(name, remove_condition=True, remove_prefix='charm_')}
        elif category == 'music_kit':
            args = {'music_kit_name': self.norm(name, remove_condition=True, remove_prefix='music_kit_')}
        elif category == 'agent':
            args = {'agent_name': self.norm(name, remove_condition=True)}
        elif category in ['patch', 'pin', 'graffiti']:
            args = {'item_name': self.norm(name, remove_condition=True, remove_prefix=f'{category}_')}
        else:
            return None, None
        if category == 'gloves':
            category = 'glove'
        return category, args
    BASE_URL = 'https://skinsearch.com'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    def get_eur_conversion_rate(self, from_currency: str = 'USD') -> float:
        """
        Fetches the conversion rate from the given currency to EUR using CDN currency API.
        Returns 1.0 if the API fails or the currency is already EUR.
        """
        if from_currency.upper() == 'EUR':
            return 1.0
        try:
            url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                rate = data.get('usd', {}).get('eur')
                if rate:
                    logger.info(f"[SkinSearch] Conversion rate USD->EUR: {rate}")
                    return float(rate)
        except Exception as e:
            logger.warning(f"[SkinSearch] Error fetching EUR conversion rate: {e}")
        logger.warning(f"[SkinSearch] Using fallback conversion rate 1.0 for USD->EUR")
        return 1.0
    
    # Doppler phase mappings based on finish catalog IDs
    DOPPLER_PHASES = {
        # Regular Doppler finish catalogs
        418: "phase_1",
        419: "phase_2", 
        420: "phase_3",
        421: "phase_4",
        415: "ruby",
        416: "sapphire",
        417: "black_pearl",
        
        # Gamma Doppler finish catalogs  
        569: "phase_1", 
        570: "phase_2",
        571: "phase_3", 
        572: "phase_4",
        568: "emerald"
    }

    def norm(self, s: str, remove_condition: bool = False, remove_prefix: str = None, for_api_url: bool = False) -> str:
        s = s.lower()
        
        if for_api_url:
            # For API URLs, preserve apostrophes and let URL encoding handle them
            s = s.replace('™', '').replace('★', '').replace('|', '').replace('(', '').replace(')', '')
            # Remove non-alphanumeric except apostrophes, underscores, and hyphens
            s = re.sub(r'[^a-z0-9\' _-]', '', s)
        else:
            # Original normalization for display/comparison purposes
            s = s.replace('"', '')
            s = s.replace('™', '').replace('★', '').replace('|', '').replace('(', '').replace(')', '')
            # Only remove non-alphanumeric except _ and -
            s = re.sub(r"[^a-z0-9_' -]", '', s)
        
        s = s.replace(' ', '_')  # Only replace spaces with underscores
        # Do NOT replace hyphens
        if remove_prefix and s.startswith(remove_prefix):
            s = s[len(remove_prefix):]
        # Remove condition suffix from skin/sticker names if needed
        if remove_condition:
            s = re.sub(r'_(factory_new|minimal_wear|field_tested|well_worn|battle_scarred|fn|mw|ft|ww|bs)$', '', s)
        s = re.sub(r'__+', '_', s)
        s = s.strip('_')
        return s

    def is_doppler_item(self, item_name: str) -> tuple[bool, str]:
        """
        Check if an item is a Doppler or Gamma Doppler
        Returns: (is_doppler, doppler_type)
        """
        name_lower = item_name.lower()
        if 'doppler' in name_lower:
            if 'gamma doppler' in name_lower:
                return True, 'gamma_doppler'
            else:
                return True, 'doppler'
        return False, ''

    def detect_doppler_phase(self, item: dict) -> Optional[str]:
        """
        Detect Doppler phase using multiple strategies
        
        Args:
            item: Steam item dict with all available data
            
        Returns:
            Phase string (e.g., 'phase_1', 'ruby', 'emerald') or None
        """
        # Strategy 1: Check if finish_catalog_id is available in item data
        finish_catalog = item.get('finish_catalog_id')
        if finish_catalog and finish_catalog in self.DOPPLER_PHASES:
            phase = self.DOPPLER_PHASES[finish_catalog]
            logger.info(f"[SkinSearch] Detected Doppler phase from finish catalog {finish_catalog}: {phase}")
            return phase
        
        # Strategy 2: Check inspect link for phase information (placeholder for future implementation)
        inspect_link = None
        actions = item.get('actions', [])
        for action in actions:
            if 'inspect' in action.get('name', '').lower():
                inspect_link = action.get('link')
                break
        
        if inspect_link:
            phase = self._extract_phase_from_inspect_link(inspect_link)
            if phase:
                logger.info(f"[SkinSearch] Detected Doppler phase from inspect link: {phase}")
                return phase
        
        # Strategy 3: Use external float API (placeholder for future implementation)
        # This would integrate with CSFloat API or similar services
        # phase = self._get_phase_from_float_api(item)
        
        # Strategy 4: Pattern matching from item description/icon
        phase = self._detect_phase_from_description(item)
        if phase:
            logger.info(f"[SkinSearch] Detected Doppler phase from description: {phase}")
            return phase
        
        logger.warning(f"[SkinSearch] Could not detect Doppler phase for item: {item.get('name', 'Unknown')}")
        return None

    def _extract_phase_from_inspect_link(self, inspect_link: str) -> Optional[str]:
        """
        Extract Doppler phase from Steam inspect link
        This is a placeholder for future implementation
        """
        # TODO: Implement inspect link parsing
        # This would require decoding the Steam inspect link format
        return None

    def _detect_phase_from_description(self, item: dict) -> Optional[str]:
        """
        Try to detect Doppler phase from item description or other metadata
        This is a heuristic approach and may not be 100% accurate
        """
        # Check icon URL for phase patterns (some phases have distinctive patterns)
        icon_url = item.get('icon_url', '')
        
        # This is a very basic heuristic - in practice you'd need more sophisticated detection
        # based on actual icon analysis or other metadata
        
        # For now, return None to indicate we couldn't detect the phase
        return None

    def get_doppler_skin_variants(self, knife_type: str, condition: str, doppler_type: str) -> list:
        """
        Get all possible Doppler variants to try when phase detection fails
        
        Args:
            knife_type: e.g., 'bayonet'
            condition: e.g., 'FN'
            doppler_type: 'doppler' or 'gamma_doppler'
            
        Returns:
            List of possible URL variants to try
        """
        if doppler_type == 'gamma_doppler':
            phases = ['phase_1', 'phase_2', 'phase_3', 'phase_4', 'emerald']
        else:  # regular doppler
            phases = ['phase_1', 'phase_2', 'phase_3', 'phase_4', 'ruby', 'sapphire', 'black_pearl']
        
        variants = []
        for phase in phases:
            if doppler_type == 'gamma_doppler':
                skin = f"gamma_doppler/{phase}"
            else:
                skin = f"doppler/{phase}"
            variants.append(skin)
        
        return variants

    def build_url(self, item_type: str, **kwargs) -> Optional[str]:
        # Helper to skip N/A or empty segments
        def is_invalid(*args):
            return any(a is None or a == '' or a == 'n/a' for a in args)

        # Weapons
        if item_type == 'weapon':
            weapon = self.norm(kwargs.get('weapon'), remove_condition=True)
            # Always strip condition from skin name, even if input includes it
            raw_skin = kwargs.get('skin') or ''
            
            # Special handling for Doppler skins - don't normalize the slash
            if 'doppler/' in raw_skin:
                # Handle Doppler skins: doppler/phase_1, gamma_doppler/emerald, etc.
                parts = raw_skin.split('/')
                if len(parts) == 2:
                    doppler_base, phase = parts
                    skin = f"{self.norm(doppler_base)}/{self.norm(phase)}"
                else:
                    # Remove condition suffix manually if present (e.g., _field-tested)
                    skin = self.norm(re.sub(r'_(factory_new|minimal_wear|field_tested|well_worn|battle_scarred|fn|mw|ft|ww|bs)$', '', raw_skin.lower()), remove_condition=True)
            else:
                # Remove condition suffix manually if present (e.g., _field-tested)
                skin = self.norm(re.sub(r'_(factory_new|minimal_wear|field_tested|well_worn|battle_scarred|fn|mw|ft|ww|bs)$', '', raw_skin.lower()), remove_condition=True)
            
            condition = kwargs.get('condition', 'FN')
            variant = kwargs.get('variant', 'normal')
            if is_invalid(weapon, condition):
                return None
            if skin == '' or skin == 'n/a':
                return None
            # List of weapons that support souvenir
            souvenir_weapons = [
                'ak_47', 'aug', 'awp', 'cz75_auto', 'deagle', 'elite', 'famas', 'five_seven', 'galil_ar', 'glock_18',
                'm249', 'm4a1_s', 'm4a4', 'mac_10', 'mag_7', 'mp5_sd', 'mp7', 'mp9', 'negev', 'nova', 'p2000',
                'p250', 'p90', 'pp_bizon', 'scar_20', 'sg_553', 'ssg_08', 'tec_9', 'ump_45', 'usp_s', 'xm1014'
            ]
            # Only knives and gloves use /item/weapons/...
            # All other weapons use /item/{weapon}/...
            if weapon.startswith('bayonet') or weapon.startswith('karambit') or weapon.startswith('m9_bayonet') or weapon.startswith('butterfly') or weapon.startswith('falchion') or weapon.startswith('shadow_daggers') or weapon.startswith('bowie_knife') or weapon.startswith('huntsman') or weapon.startswith('talon_knife') or weapon.startswith('ursus_knife') or weapon.startswith('paracord_knife') or weapon.startswith('survival_knife') or weapon.startswith('classic_knife') or weapon.startswith('nomad_knife') or weapon.startswith('stiletto_knife') or weapon.startswith('skeleton_knife') or weapon.startswith('glove'):
                # Knives and gloves
                if variant == 'stattrak':
                    url = f"{self.BASE_URL}/item/weapons/{weapon}/{skin}/{condition}/stattrak"
                elif variant == 'souvenir' and weapon in souvenir_weapons:
                    url = f"{self.BASE_URL}/item/weapons/{weapon}/{skin}/{condition}/souvenir"
                else:
                    url = f"{self.BASE_URL}/item/weapons/{weapon}/{skin}/{condition}/normal"
            else:
                # All other weapons
                if variant == 'stattrak':
                    url = f"{self.BASE_URL}/item/{weapon}/{skin}/{condition}/stattrak"
                elif variant == 'souvenir' and weapon in souvenir_weapons:
                    url = f"{self.BASE_URL}/item/{weapon}/{skin}/{condition}/souvenir"
                else:
                    url = f"{self.BASE_URL}/item/{weapon}/{skin}/{condition}/normal"
            return url
        # Gloves
        elif item_type == 'glove':
            glove_type = self.norm(kwargs.get('glove_type'), remove_condition=True)
            skin = self.norm(kwargs.get('skin'), remove_condition=True)
            condition = kwargs.get('condition', 'FN')
            if is_invalid(glove_type, skin, condition):
                return None
            # Gloves use the /item/weapons/... pattern like knives
            url = f"{self.BASE_URL}/item/weapons/{glove_type}/{skin}/{condition}/normal"
            return url
        # Knives
        elif item_type == 'knife':
            knife_type = self.norm(kwargs.get('knife_type'), remove_condition=True)
            raw_skin = kwargs.get('skin', '')
            condition = kwargs.get('condition', 'FN')
            variant = kwargs.get('variant', 'normal')
            
            if is_invalid(knife_type, condition):
                return None
            
            # Special handling for Doppler skins - don't normalize the slash
            if 'doppler/' in raw_skin:
                # Handle Doppler skins: doppler/phase_1, gamma_doppler/emerald, etc.
                parts = raw_skin.split('/')
                if len(parts) == 2:
                    doppler_base, phase = parts
                    skin = f"{self.norm(doppler_base)}/{self.norm(phase)}"
                else:
                    skin = self.norm(raw_skin, remove_condition=True)
            else:
                skin = self.norm(raw_skin, remove_condition=True)
            
            if skin == '' or skin == 'n/a':
                return None
                
            # Only stattrak is valid for knives
            if variant == 'stattrak':
                url = f"{self.BASE_URL}/item/weapons/{knife_type}/{skin}/{condition}/stattrak"
            else:
                url = f"{self.BASE_URL}/item/weapons/{knife_type}/{skin}/{condition}/normal"
            return url
        # Cases
        elif item_type == 'case':
            case_name = self.norm(kwargs.get('case_name'), remove_condition=True)
            if is_invalid(case_name):
                return None
            url = f"{self.BASE_URL}/crate/{case_name}"
            return url
        # Souvenir Packages
        elif item_type == 'souvenir_package':
            case_name = self.norm(kwargs.get('case_name'), remove_condition=True)
            if is_invalid(case_name):
                return None
            url = f"{self.BASE_URL}/crate/{case_name}"
            return url
        # Capsules
        elif item_type == 'capsule':
            capsule_name = self.norm(kwargs.get('capsule_name'), remove_condition=True)
            if is_invalid(capsule_name):
                return None
            url = f"{self.BASE_URL}/capsule/{capsule_name}"
            return url
        # Stickers
        elif item_type == 'sticker':
            sticker_name_raw = kwargs.get('sticker_name') or ''
            # Remove hyphens for sticker names (edge case: hunter-)
            sticker_name = self.norm(sticker_name_raw.replace('-', ''), remove_condition=True, remove_prefix='sticker_')
            if is_invalid(sticker_name):
                return None
            url = f"{self.BASE_URL}/item/sticker/{sticker_name}"
            return url
        # Charms
        elif item_type == 'charm':
            charm_name = self.norm(kwargs.get('charm_name'), remove_condition=True, remove_prefix='charm_')
            if is_invalid(charm_name):
                return None
            url = f"{self.BASE_URL}/item/charm/{charm_name}"
            return url
        # Music Kits
        elif item_type == 'music_kit':
            music_kit_name = self.norm(kwargs.get('music_kit_name'), remove_condition=True, remove_prefix='music_kit_')
            if is_invalid(music_kit_name):
                return None
            url = f"{self.BASE_URL}/item/music_kit/{music_kit_name}"
            return url
        # Agents
        elif item_type == 'agent':
            agent_name = self.norm(kwargs.get('agent_name'), remove_condition=True)
            if is_invalid(agent_name):
                return None
            url = f"{self.BASE_URL}/item/agent/{agent_name}"
            return url
        # Patches, Pins, Graffiti
        elif item_type in ['patch', 'pin', 'graffiti']:
            item_name = self.norm(kwargs.get('item_name'), remove_condition=True, remove_prefix=f'{item_type}_')
            if is_invalid(item_name):
                return None
            url = f"{self.BASE_URL}/item/{item_type}/{item_name}"
            return url
        else:
            raise ValueError(f"Unknown item_type: {item_type}")

    def fetch_price(self, item_type: str, url: str) -> Optional[PriceInfo]:
        # Retry logic: up to 3 attempts, 15s timeout per attempt
        max_attempts = 3
        eur_rate = self.get_eur_conversion_rate('USD')
        for attempt in range(1, max_attempts + 1):
            try:
                # Build API endpoint from item URL
                parts = url.split('/')
                if item_type == 'weapon':
                    idx = parts.index('item') + 1
                    weapon = parts[idx]
                    skin = parts[idx+1] if len(parts) > idx+1 else ''
                    condition = parts[idx+2] if len(parts) > idx+2 else ''
                    variant = parts[idx+3] if len(parts) > idx+3 else 'normal'
                    api_url = f"{self.BASE_URL}/api/item/weapons/{weapon}/{skin}/{condition}/{variant}"
                elif item_type == 'knife':
                    if 'weapons' in parts:
                        idx = parts.index('weapons') + 1
                        knife = parts[idx] if len(parts) > idx else ''
                        skin_parts = []
                        current_idx = idx + 1
                        if current_idx < len(parts) and parts[current_idx] in ['doppler', 'gamma_doppler']:
                            doppler_base = parts[current_idx]
                            current_idx += 1
                            if current_idx < len(parts) and parts[current_idx] in ['phase_1', 'phase_2', 'phase_3', 'phase_4', 'ruby', 'sapphire', 'black_pearl', 'emerald']:
                                phase = parts[current_idx]
                                skin = f"{doppler_base}/{phase}"
                                current_idx += 1
                            else:
                                skin = doppler_base
                        else:
                            skin = parts[current_idx] if current_idx < len(parts) else ''
                            current_idx += 1
                        condition = parts[current_idx] if current_idx < len(parts) else ''
                        variant = parts[current_idx + 1] if current_idx + 1 < len(parts) else 'normal'
                        api_url = f"{self.BASE_URL}/api/item/weapons/{knife}/{skin}/{condition}/{variant}"
                    else:
                        idx = parts.index('item') + 1
                        knife = parts[idx]
                        skin = parts[idx+1] if len(parts) > idx+1 else ''
                        condition = parts[idx+2] if len(parts) > idx+2 else ''
                        variant = parts[idx+3] if len(parts) > idx+3 else 'normal'
                        api_url = f"{self.BASE_URL}/api/item/weapons/{knife}/{skin}/{condition}/{variant}"
                elif item_type == 'glove':
                    if 'weapons' in parts:
                        idx = parts.index('weapons') + 1
                        glove = parts[idx] if len(parts) > idx else ''
                        skin = parts[idx+1] if len(parts) > idx+1 else ''
                        condition = parts[idx+2] if len(parts) > idx+2 else ''
                        api_url = f"{self.BASE_URL}/api/item/weapons/{glove}/{skin}/{condition}/normal"
                    else:
                        idx = parts.index('item') + 1
                        glove = parts[idx] if len(parts) > idx else ''
                        skin = parts[idx+1] if len(parts) > idx+1 else ''
                        condition = parts[idx+2] if len(parts) > idx+2 else ''
                        api_url = f"{self.BASE_URL}/api/item/weapons/{glove}/{skin}/{condition}/normal"
                elif item_type == 'music_kit':
                    idx = parts.index('music_kit') + 1
                    music_kit_name = parts[idx]
                    api_url = f"{self.BASE_URL}/api/item/music_kits/{music_kit_name}"
                elif item_type == 'sticker':
                    idx = parts.index('sticker') + 1
                    sticker_name = parts[idx]
                    api_url = f"{self.BASE_URL}/api/item/stickers/{sticker_name}"
                elif item_type == 'case' or item_type == 'souvenir_package':
                    idx = parts.index('crate') + 1
                    case_name = parts[idx]
                    api_url = f"{self.BASE_URL}/api/item/crates/{case_name}"
                elif item_type == 'charm':
                    idx = parts.index('charm') + 1
                    charm_name = parts[idx]
                    api_url = f"{self.BASE_URL}/api/item/charms/{charm_name}"
                elif item_type == 'agent':
                    idx = parts.index('agent') + 1
                    agent_name = parts[idx]
                    api_url = f"{self.BASE_URL}/api/item/agents/{agent_name}"
                elif item_type == 'capsule':
                    idx = parts.index('capsule') + 1
                    capsule_name = parts[idx]
                    api_url = f"{self.BASE_URL}/api/item/capsules/{capsule_name}"
                else:
                    api_url = url.replace('/item/', '/api/item/')
                markets = ["csfloat","bitskins","csdeals","csmoney","skinport","skinbaron","dmarket","skinbid","buff163","tradeit","steam","pirateswap","skinsmonkey","skinvault"]
                import json
                api_url += f"/?l=en_US&m={json.dumps(markets)}"
                logger.info(f"[SkinSearch] Fetching price for item_type: {item_type}, API URL: {api_url} (attempt {attempt})")
                resp = requests.get(api_url, headers=self.HEADERS, timeout=15)
                if resp.status_code != 200:
                    logger.warning(f"[SkinSearch] Non-200 response for API URL: {api_url} (attempt {attempt})")
                    continue
                if not resp.text or resp.text.strip() == "":
                    logger.warning(f"[SkinSearch] Empty response for API URL: {api_url} (attempt {attempt})")
                    continue
                market_url = None
                resp_text = resp.text.strip()
                if resp_text and (resp_text.startswith('{') or resp_text.startswith('[')):
                    try:
                        data = resp.json()
                    except Exception as e:
                        import re
                        match = re.search(r'"market":"csfloat","price":(\d+)', resp.text)
                        if match:
                            price = int(match.group(1))
                            price_eur = round(price * eur_rate, 2)
                            return PriceInfo(price=price_eur, url=None, market="csfloat")
                        logger.error(f"[SkinSearch] Error parsing JSON and extracting price: {e} (attempt {attempt})")
                        continue
                else:
                    continue
                if "item" in data and "listings" in data["item"]:
                    listings = data["item"].get("listings", [])
                    for entry in listings:
                        market_val = str(entry.get("market", "")).lower()
                        if market_val == "csfloat" and "price" in entry:
                            price = entry["price"]
                            market_url = None
                            logger.info(f"[SkinSearch] Found csfloat price: {price} for {api_url}")
                            break
                if price is None and "markets" in data:
                    csfloat = data["markets"].get("csfloat")
                    if csfloat and "price" in csfloat:
                        price = csfloat["price"]
                        market_url = csfloat.get("url")
                        logger.info(f"[SkinSearch] Found csfloat price in markets: {price} for {api_url}")
                if price is None and "prices" in data:
                    import re
                    m = re.search(r'/([A-Z]{2})(?:/|$)', url)
                    requested_quality = m.group(1) if m else None
                    for entry in data["prices"]:
                        if entry.get("quality") == requested_quality:
                            price = entry.get("price")
                            market_url = None
                            logger.info(f"[SkinSearch] Found price in prices array: {price} for quality {requested_quality}")
                            break
                if price is not None:
                    # Always treat integer price as cents
                    if isinstance(price, int):
                        price = price / 100.0
                    price_eur = round(float(price) * eur_rate, 2)
                    logger.info(f"[SkinSearch] Successfully extracted price: {price_eur} EUR from {api_url}")
                    return PriceInfo(price=price_eur, url=market_url, market="csfloat")
                logger.warning(f"[SkinSearch] No csfloat price found for API URL: {api_url} (attempt {attempt})")
                logger.debug(f"[SkinSearch] API response structure for {api_url} (attempt {attempt}):")
                logger.debug(f"[SkinSearch] - Has 'item' key: {'item' in data}")
                logger.debug(f"[SkinSearch] - Has 'markets' key: {'markets' in data}")
                logger.debug(f"[SkinSearch] - Has 'prices' key: {'prices' in data}")
                if "item" in data and "listings" in data["item"]:
                    listings = data["item"]["listings"]
                    available_markets = [entry.get("market", "unknown") for entry in listings[:5]]
                    logger.debug(f"[SkinSearch] - Available markets in listings (first 5): {available_markets}")
                logger.debug(f"[SkinSearch] Full API response for {api_url} (attempt {attempt}):\n{resp.text[:1000]}...")
            except Exception as e:
                logger.error(f"[SkinSearch] Error fetching price: {e} (attempt {attempt})")
                continue
        return None

    def scrape_steam_item(self, item: dict) -> Optional[PriceInfo]:
        self.is_running = True
        self.last_used = datetime.now().isoformat()
        logger.info(f"[SkinSearch] Status set to running at {self.last_used}")
        try:
            item_type, url_args = self.map_steam_item_to_skinsearch_args(item)
            if item_type and url_args:
                # Check if this is a Doppler item that needs fallback handling
                if url_args.get('_doppler_fallback'):
                    result = self._scrape_doppler_with_fallback(item, item_type, url_args)
                    return result
                url = self.build_url(item_type, **url_args)
                if url is None:
                    logger.info(f"[SkinSearch] Skipping item due to missing or N/A segments: {item}")
                    return None
                result = self.fetch_price(item_type, url)
                return result
            return None
        finally:
            self.is_running = False
            self.last_used = datetime.now().isoformat()
            logger.info(f"[SkinSearch] Status set to idle at {self.last_used}")

    def _scrape_doppler_with_fallback(self, item: dict, item_type: str, base_url_args: dict) -> Optional[PriceInfo]:
        """
        Handle Doppler items when phase detection failed by trying all possible phases
        """
        doppler_type = base_url_args.get('_doppler_type', 'doppler')
        weapon_or_knife = base_url_args.get('weapon') or base_url_args.get('knife_type')
        condition = base_url_args.get('condition', 'FN')
        variant = base_url_args.get('variant', 'normal')
        
        logger.info(f"[SkinSearch] Trying Doppler fallback for {weapon_or_knife} ({doppler_type})")
        
        # Get all possible phase variants to try
        phase_variants = self.get_doppler_skin_variants(weapon_or_knife, condition, doppler_type)
        
        # Try each phase variant until we find one with a price
        for phase_skin in phase_variants:
            try:
                # Create clean url_args without the fallback markers
                clean_args = {k: v for k, v in base_url_args.items() if not k.startswith('_')}
                clean_args['skin'] = phase_skin
                
                url = self.build_url(item_type, **clean_args)
                if url:
                    logger.info(f"[SkinSearch] Trying Doppler phase: {phase_skin}")
                    price_info = self.fetch_price(item_type, url)
                    if price_info:
                        logger.info(f"[SkinSearch] Found price for Doppler phase {phase_skin}: {price_info.price} EUR")
                        return price_info
                    else:
                        logger.debug(f"[SkinSearch] No price found for phase: {phase_skin}")
            except Exception as e:
                logger.warning(f"[SkinSearch] Error trying Doppler phase {phase_skin}: {e}")
                continue
        
        logger.warning(f"[SkinSearch] No price found for any Doppler phase of {weapon_or_knife}")
        return None

    def batch_update_steam_prices(self, steam_items):
        self.is_running = True
        self.last_used = datetime.now().isoformat()
        logger.info(f"[SkinSearch] Status set to running at {self.last_used}")
        results = []
        try:
            for item in steam_items:
                # Log the raw item
                logger.info(f"[SkinSearch] Processing item: {item}")
                # Log mapping result
                item_type, url_args = self.map_steam_item_to_skinsearch_args(item)
                logger.info(f"[SkinSearch] Mapping result: item_type={item_type}, url_args={url_args}")
                # Skip patch packs (not present on SkinSearch)
                if item_type == 'capsule' and 'patch_pack' in item.get('item_type', '').lower():
                    logger.info(f"[SkinSearch] Skipping patch pack (not present on SkinSearch): {item['name']}")
                    print(f"{item['name']} | Skipped (patch pack)")
                    continue
                price_info = self.scrape_steam_item(item)
                print(f"{item['name']} | Price: {price_info}")
                results.append({'name': item.get('name'), 'price_info': price_info})
                # Here you could update the database with price_info.price
        finally:
            self.is_running = False
            self.last_used = datetime.now().isoformat()
            logger.info(f"[SkinSearch] Status set to idle at {self.last_used}")
        return results

# Example usage
def test_skinsearch_scraper():
    scraper = SkinSearchScraper()
    # Example: weapon
    url = scraper.build_url('weapon', weapon='ak-47', skin='redline', condition='FN', variant='normal')
    result = scraper.fetch_price('weapon', url)
    print(f"SkinSearch Price: {result}")

if __name__ == '__main__':
    test_skinsearch_scraper()

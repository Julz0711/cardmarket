# Scraper Architecture Documentation

## **PRODUCTION SCRAPERS** (Currently Active)

### Core Infrastructure
- **`scrapers/base_scraper.py`** - Base class for all scrapers with common functionality
- **`scrapers/scraper_manager.py`** - Central manager that orchestrates all scrapers
- **`scrapers/__init__.py`** - Module exports for clean imports

### Active Scrapers (Used in Production)
- **`scrapers/trading_cards_scraper.py`** - CardMarket trading card scraper (Pokemon, etc.)
- **`scrapers/steam_inventory_scraper.py`** - Steam CS2 inventory scraper  
- **`scrapers/csgoskins_scraper.py`** - CSGOSkins.gg market price scraper
- **`parallel_scraper.py`** - Multi-instance parallel scraper for bulk operations

### Available Scrapers (Ready for Use)
- **`scrapers/stocks_scraper.py`** - Stock market data scraper
- **`scrapers/etf_scraper.py`** - ETF data scraper
- **`scrapers/crypto_scraper.py`** - Cryptocurrency data scraper

## **USAGE IN APP.PY**

```python
# Main imports
from scrapers import ScraperManager, ScraperError, ValidationError
from scrapers.csgoskins_scraper import CSGOSkinsGGScraper
from parallel_scraper import ParallelCSGOSkinsScraper

# ScraperManager handles: 'cards', 'steam'
# Direct imports for: CSGOSkins pricing, bulk parallel operations
```

## **API ENDPOINTS USING SCRAPERS**

### ScraperManager Routes
- `POST /api/scrape/cards` - Trading cards scraping
- `POST /api/scrape/steam` - Steam inventory scraping  
- `GET /api/scrapers/status` - Scraper health checks
- `GET /api/scrapers/available` - Available scraper types

### Direct Scraper Routes
- `POST /api/steam/update-prices` - Uses CSGOSkinsGGScraper
- `POST /api/scrape/bulk-parallel` - Uses ParallelCSGOSkinsScraper

## **FILES REMOVED IN CLEANUP**

### Test Files (Deleted)
- `test_scraper_auth.py`
- `test_scraper_v2.py` 
- `test_all_scraper_auth.py`
- `test_bulk_api.py`

### Experimental Files (Deleted)
- `ultrafast_scraper.py` - Ultra-aggressive optimization experiment
- `ultrafast_balanced_scraper.py` - Balanced optimization experiment
- `enhanced_scraper.py` - Enhanced error handling experiment
- `cloudflare_scraper.py` - Cloudflare bypass experiment
- `scraper.py` - Legacy/old scraper

### Analysis Tools (Deleted)
- `analyze_csgoskins.py` - Website structure analysis tool
- `analyze_post_cloudflare.py` - Post-Cloudflare analysis tool
- `csgoskins_page_source.html` - Analysis output
- `csgoskins_screenshot.png` - Analysis screenshot

### Unused/Duplicate (Deleted)
- `scrapers/steam_inventory_scraper_v2.py` - Duplicate/newer version
- `scrapers/csfloat_scraper.py` - Unused CSFloat integration

## **CURRENT ARCHITECTURE STATUS**

✅ **Clean and organized** - Only production and ready-to-use files remain
✅ **No test/experimental clutter** - All temporary files removed  
✅ **Clear separation** - Core scrapers in `/scrapers/`, specialized in root
✅ **Fully functional** - All active scrapers still work in app.py
✅ **Future-ready** - Additional scrapers (stocks, ETF, crypto) available when needed

## **NEXT STEPS**

1. **CSGOSkins.gg Challenge** - The main remaining issue is Cloudflare protection
2. **Alternative Data Sources** - Consider other CS2 pricing APIs
3. **Scraper Expansion** - Activate stocks/ETF/crypto scrapers when needed
4. **Performance Monitoring** - Add scraper performance metrics

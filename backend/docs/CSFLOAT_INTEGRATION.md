# CSFloat Steam Price Integration

This feature adds real-time pricing from CSFloat market to your Steam inventory items.

## How It Works

1. **Steam Inventory Import**: Import your Steam inventory as usual using the Steam scraper
2. **Price Update**: Click the "Update Prices" button to fetch current market prices from CSFloat
3. **Accurate Pricing**: Prices are fetched based on item name and condition (FN, MW, FT, WW, BS)

## Features

### 🎯 **Accurate Market Pricing**
- Fetches real prices from CSFloat market
- Matches items by name and condition
- Converts USD prices to EUR (approximate)

### 🔄 **Batch Updates**
- Updates all items at once
- Shows progress during update
- Detailed results with success/failure counts

### 📊 **Smart Matching**
- Extracts condition from item names automatically
- Cleans item names for better search results
- Handles various item name formats

## Usage

### 1. Update All Prices
```typescript
// Frontend - Click "Update Prices" button
// Backend API call
POST /api/steam/update-prices
{
  "headless": true
}
```

### 2. Update Specific Items
```typescript
POST /api/steam/update-prices
{
  "item_ids": ["item_id_1", "item_id_2"],
  "headless": true
}
```

## Technical Details

### CSFloat Scraper (`csfloat_scraper.py`)
- Uses Selenium WebDriver for web scraping
- Searches CSFloat market with item name
- Applies condition filters (FN, MW, FT, WW, BS)
- Extracts price from first search result

### API Endpoint (`/api/steam/update-prices`)
- Authenticates user requests
- Processes items in batches
- Updates database with new prices
- Returns detailed results

### Frontend Integration
- "Update Prices" button in Steam inventory
- Real-time progress indication
- Automatic local state updates
- Error handling and user feedback

## XPath Selectors Used

```
Search Input: //*[@id="mat-input-18"]
Condition Buttons:
- FN: .../div[3]/div[1]
- MW: .../div[3]/div[2] 
- FT: .../div[3]/div[3]
- WW: .../div[3]/div[4]
- BS: .../div[3]/div[5]
First Result: .../item-card[1]
```

## Response Format

```json
{
  "status": "success",
  "message": "Updated prices for 45 items and skipped 3 items",
  "updated_items": 45,
  "skipped_items": 3,
  "failed_items": 0,
  "details": {
    "updated": [
      {"name": "AK-47 | Redline", "price": 8.75}
    ],
    "skipped": [
      {"name": "Operation Badge", "reason": "No price found on CSFloat"}
    ],
    "failed": []
  }
}
```

## Error Handling

- **Rate Limiting**: Adds delays between requests
- **Missing Items**: Skips items not found on CSFloat
- **WebDriver Issues**: Fallback error messages
- **Database Errors**: Individual item failure tracking

## Future Enhancements

1. **Multiple Sources**: Add more pricing sources
2. **Price History**: Track price changes over time
3. **Alerts**: Notify on significant price changes
4. **Filters**: Update only specific rarities/conditions
5. **Scheduling**: Automatic daily price updates

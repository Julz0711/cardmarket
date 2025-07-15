#!/usr/bin/env python3

from database import steam_item_model

if steam_item_model:
    items = steam_item_model.get_items_by_user('default_user')
    print(f'Found {len(items)} Steam items for default_user')
    
    if items:
        print("\nFirst 5 items:")
        for item in items[:5]:
            print(f'- {item.get("name", "Unknown")} (ID: {item.get("_id", "Unknown")})')
    
    # Also check total items in the collection
    total_items = steam_item_model.collection.count_documents({})
    print(f'\nTotal Steam items in database: {total_items}')
else:
    print('Steam item model not available')

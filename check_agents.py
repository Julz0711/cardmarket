#!/usr/bin/env python3

import sys
sys.path.append('backend')

from database import MongoDB

def check_agent_rarities():
    mongo = MongoDB()
    db = mongo.db
    
    # Find agent items
    agent_items = list(db.steam_items.find(
        {'name': {'$regex': 'agent', '$options': 'i'}}, 
        {'name': 1, 'rarity': 1}
    ).limit(10))
    
    print("Current agent rarities in database:")
    for item in agent_items:
        print(f"  {item['name']} -> '{item['rarity']}'")
    
    print("\nAll unique rarities in database:")
    all_rarities = db.steam_items.distinct('rarity')
    for rarity in sorted(all_rarities):
        print(f"  '{rarity}'")

if __name__ == "__main__":
    check_agent_rarities()

"""
MongoDB Database Models and Operations for CardMarket App
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional
import logging
import os
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError
import requests

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = None
        self.db = None
        self.connected = False
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/cardmarket_local')
            database_name = os.getenv('DATABASE_NAME', 'cardmarket')
            
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # Reduced timeout for faster feedback
                connectTimeoutMS=5000,
                socketTimeoutMS=20000
            )
            self.db = self.client[database_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: {database_name}")
            self.connected = True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.warning("MongoDB not available. App will run but data won't persist.")
            self.connected = False
            self.client = None
            self.db = None
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

class CardModel:
    def __init__(self, db):
        """Initialize Card model with database reference"""
        if db is None:
            raise ValueError("Database connection required for CardModel")
        self.db = db
        self.collection = db.cards
        self.ensure_indexes()
    
    def ensure_indexes(self):
        """Create necessary indexes for better performance"""
        try:
            # Create compound index for efficient queries
            self.collection.create_index([
                ("user_id", 1),
                ("tcg", 1),
                ("expansion", 1),
                ("number", 1)
            ])
            
            # Index for search functionality
            self.collection.create_index([
                ("name", "text"),
                ("tcg", "text"),
                ("expansion", "text")
            ])
            
            logger.info("Card collection indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def create_card(self, card_data: Dict) -> str:
        """Create a new card and return its ID"""
        try:
            # Add metadata
            card_data.update({
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'price_history': [{
                    'price': card_data.get('current_price', 0),
                    'date': datetime.utcnow(),
                    'source': 'scraper'
                }]
            })
            
            result = self.collection.insert_one(card_data)
            logger.info(f"Created card: {card_data.get('name')} with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create card: {e}")
            raise
    
    def find_existing_card(self, user_id: str, tcg: str, expansion: str, number: int, card_language: str) -> Optional[Dict]:
        """Find an existing card by user_id, tcg, expansion, number, and card_language"""
        try:
            query = {
                'user_id': user_id,
                'tcg': tcg,
                'expansion': expansion,
                'number': number,
                'card_language': card_language
            }
            
            card = self.collection.find_one(query)
            if card:
                card['_id'] = str(card['_id'])
                card['id'] = card['_id']
                logger.info(f"Found existing card: {card.get('name')} (#{number}) from {tcg} - {expansion}")
            
            return card
            
        except Exception as e:
            logger.error(f"Failed to find existing card: {e}")
            return None
    
    def get_cards(self, user_id: str = None, limit: int = 1000) -> List[Dict]:
        """Get cards for a user (or all cards if no user_id)"""
        try:
            query = {}
            if user_id:
                query['user_id'] = user_id
            
            cards = list(self.collection.find(query).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for card in cards:
                card['_id'] = str(card['_id'])
                card['id'] = card['_id']  # Add id field for frontend compatibility
            
            logger.info(f"Retrieved {len(cards)} cards for user: {user_id or 'all'}")
            return cards
            
        except Exception as e:
            logger.error(f"Failed to get cards: {e}")
            raise
    
    def get_card_by_id(self, card_id: str) -> Optional[Dict]:
        """Get a specific card by ID"""
        try:
            card = self.collection.find_one({'_id': ObjectId(card_id)})
            if card:
                card['_id'] = str(card['_id'])
                card['id'] = card['_id']
            return card
            
        except Exception as e:
            logger.error(f"Failed to get card by ID {card_id}: {e}")
            return None
    
    def update_card(self, card_id: str, update_data: Dict) -> bool:
        """Update a card"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {'_id': ObjectId(card_id)},
                {'$set': update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated card: {card_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update card {card_id}: {e}")
            return False
    
    def update_card_price(self, card_id: str, new_price: float) -> bool:
        """Update card price and add to price history"""
        try:
            # Add new price to history
            price_entry = {
                'price': new_price,
                'date': datetime.utcnow(),
                'source': 'manual_update'
            }
            
            result = self.collection.update_one(
                {'_id': ObjectId(card_id)},
                {
                    '$set': {
                        'current_price': new_price,
                        'updated_at': datetime.utcnow()
                    },
                    '$push': {'price_history': price_entry}
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated price for card {card_id}: €{new_price}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update price for card {card_id}: {e}")
            return False
    
    def delete_card(self, card_id: str) -> bool:
        """Delete a card"""
        try:
            result = self.collection.delete_one({'_id': ObjectId(card_id)})
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted card: {card_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete card {card_id}: {e}")
            return False
    
    def delete_all_cards(self, user_id: str = None) -> int:
        """Delete all cards for a user (or all cards if no user_id)"""
        try:
            query = {}
            if user_id:
                query['user_id'] = user_id
            
            result = self.collection.delete_many(query)
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} cards for user: {user_id or 'all'}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete cards: {e}")
            return 0
    
    def get_portfolio_summary(self, user_id: str = None) -> Dict:
        """Calculate portfolio summary for a user including Steam inventory"""
        try:
            # Fetch EUR conversion rates
            conversion_rates = {"USD": 1.0} 
            try:
                response = requests.get(
                    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/eur.json"
                )
                if response.ok:
                    data = response.json()
                    conversion_rates.update(data.get("eur", {}))
            except Exception as e:
                logger.warning(f"Failed to fetch conversion rates: {e}")

            match_stage = {}
            if user_id:
                match_stage['user_id'] = user_id
            
            pipeline = [
                {'$match': match_stage},
                {
                    '$group': {
                        '_id': None,
                        'total_cards': {'$sum': '$quantity'},
                        'total_value': {
                            '$sum': {
                                '$multiply': [
                                    {
                                        '$cond': [
                                            {'$eq': ['$currency', 'EUR']},
                                            {'$multiply': ['$current_price', conversion_rates.get('$currency', 1.0)]},
                                            '$current_price'
                                        ]
                                    },
                                    '$quantity'
                                ]
                            }
                        },
                        'total_investment': {
                            '$sum': {
                                '$multiply': [
                                    {
                                        '$cond': [
                                            {'$eq': ['$currency', 'EUR']},
                                            {'$multiply': ['$price_bought', conversion_rates.get('$currency', 1.0)]},
                                            '$price_bought'
                                        ]
                                    },
                                    '$quantity'
                                ]
                            }
                        },
                        'cards': {'$push': '$$ROOT'}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            
            # Get Steam inventory stats and items if user_id is provided
            steam_stats = {'total_value': 0, 'total_bought': 0, 'total_items': 0}
            steam_items = []
            if user_id:
                try:
                    # Use global steam_item_model instance
                    global steam_item_model
                    if steam_item_model:
                        steam_stats = steam_item_model.get_user_stats(user_id)
                        steam_items = steam_item_model.get_user_items(user_id)
                except Exception as e:
                    logger.warning(f"Failed to get Steam stats: {e}")
            
            # Get financial assets stats and items if user_id is provided
            financial_stats = {'stocks': {'value': 0, 'investment': 0, 'count': 0, 'items': []},
                              'etfs': {'value': 0, 'investment': 0, 'count': 0, 'items': []},
                              'crypto': {'value': 0, 'investment': 0, 'count': 0, 'items': []}}
            
            if user_id:
                try:
                    # Use global financial_asset_model instance
                    global financial_asset_model
                    if financial_asset_model:
                        for asset_type in ['stocks', 'etfs', 'crypto']:
                            assets = financial_asset_model.get_assets_by_type(user_id, asset_type)
                            total_value = 0
                            total_investment = 0
                            for asset in assets:
                                if asset.get('currency') == 'USD':
                                    conversion_rate = conversion_rates.get('USD', 1.0)
                                else:
                                    conversion_rate = 1.0
                                current_value = asset.get('current_price', 0) * asset.get('quantity', 0) * conversion_rate
                                investment = asset.get('price_bought', 0) * asset.get('quantity', 0) * conversion_rate
                                total_value += current_value
                                total_investment += investment
                            
                            financial_stats[asset_type] = {
                                'value': total_value,
                                'investment': total_investment,
                                'count': len(assets),
                                'items': assets
                            }
                except Exception as e:
                    logger.warning(f"Failed to get financial assets stats: {e}")
            
            if not result:
                # Only Steam items and/or financial assets, no cards
                steam_value = steam_stats.get('total_value', 0)
                steam_investment = steam_stats.get('total_bought', 0)
                
                # Add financial assets
                stocks_value = financial_stats['stocks']['value']
                stocks_investment = financial_stats['stocks']['investment']
                etfs_value = financial_stats['etfs']['value'] 
                etfs_investment = financial_stats['etfs']['investment']
                crypto_value = financial_stats['crypto']['value']
                crypto_investment = financial_stats['crypto']['investment']
                
                total_value = steam_value + stocks_value + etfs_value + crypto_value
                total_investment = steam_investment + stocks_investment + etfs_investment + crypto_investment
                profit_loss = total_value - total_investment
                profit_loss_percentage = (profit_loss / total_investment * 100) if total_investment > 0 else 0
                
                # Calculate performers from all asset types
                all_performers = []
                
                # Steam performers
                steam_performers = self._calculate_performers(steam_items, 'steam')
                all_performers.extend(steam_performers['all'])
                
                # Financial asset performers
                for asset_type in ['stocks', 'etfs', 'crypto']:
                    financial_performers = self._calculate_performers(financial_stats[asset_type]['items'], asset_type)
                    all_performers.extend(financial_performers['all'])
                
                # Sort all performers
                all_performers.sort(key=lambda x: x['profit_loss_percentage'], reverse=True)
                top_performers = all_performers[:3]
                worst_performers = all_performers[-3:] if len(all_performers) >= 3 else []
                
                # Calculate percentages
                steam_percentage = (steam_value / total_value * 100) if total_value > 0 else 0
                stocks_percentage = (stocks_value / total_value * 100) if total_value > 0 else 0
                etfs_percentage = (etfs_value / total_value * 100) if total_value > 0 else 0
                crypto_percentage = (crypto_value / total_value * 100) if total_value > 0 else 0
                
                return {
                    'total_portfolio_value': total_value,
                    'total_investment': total_investment,
                    'total_profit_loss': profit_loss,
                    'total_profit_loss_percentage': profit_loss_percentage,
                    'asset_breakdown': {
                        'cards': {'value': 0, 'percentage': 0, 'count': 0},
                        'steam': {'value': steam_value, 'percentage': steam_percentage, 'count': steam_stats.get('total_items', 0)},
                        'stocks': {'value': stocks_value, 'percentage': stocks_percentage, 'count': financial_stats['stocks']['count']},
                        'etfs': {'value': etfs_value, 'percentage': etfs_percentage, 'count': financial_stats['etfs']['count']},
                        'crypto': {'value': crypto_value, 'percentage': crypto_percentage, 'count': financial_stats['crypto']['count']}
                    },
                    'top_performers': top_performers,
                    'worst_performers': worst_performers
                }
            
            data = result[0]
            cards_value = data['total_value']
            cards_investment = data['total_investment']
            steam_value = steam_stats.get('total_value', 0)
            steam_investment = steam_stats.get('total_bought', 0)
            
            # Add financial assets
            stocks_value = financial_stats['stocks']['value']
            stocks_investment = financial_stats['stocks']['investment']
            etfs_value = financial_stats['etfs']['value'] 
            etfs_investment = financial_stats['etfs']['investment']
            crypto_value = financial_stats['crypto']['value']
            crypto_investment = financial_stats['crypto']['investment']
            
            total_value = cards_value + steam_value + stocks_value + etfs_value + crypto_value
            total_investment = cards_investment + steam_investment + stocks_investment + etfs_investment + crypto_investment
            profit_loss = total_value - total_investment
            profit_loss_percentage = (profit_loss / total_investment * 100) if total_investment > 0 else 0
            
            # Calculate performers across all asset types
            all_performers = []
            
            # Add card performers
            card_performers = self._calculate_performers(data['cards'], 'card')
            all_performers.extend(card_performers['all'])
            logger.info(f"Card performers found: {len(card_performers['all'])}")
            
            # Add steam performers
            steam_performers = self._calculate_performers(steam_items, 'steam')
            all_performers.extend(steam_performers['all'])
            logger.info(f"Steam performers found: {len(steam_performers['all'])}")
            
            # Add financial asset performers
            for asset_type in ['stocks', 'etfs', 'crypto']:
                financial_performers = self._calculate_performers(financial_stats[asset_type]['items'], asset_type)
                all_performers.extend(financial_performers['all'])
                logger.info(f"{asset_type.capitalize()} performers found: {len(financial_performers['all'])}")
            
            logger.info(f"Total performers: {len(all_performers)}")
            
            # Sort all performers by profit/loss percentage
            all_performers.sort(key=lambda x: x['profit_loss_percentage'], reverse=True)
            
            # Get top 3 and worst 3
            top_performers = all_performers[:3]  # Best performers (highest %)
            worst_performers = all_performers[-3:] if len(all_performers) >= 3 else []  # Worst performers (lowest %)
            
            logger.info(f"Top 3 performers: {[p['name'] + ': ' + str(round(p['profit_loss_percentage'], 2)) + '%' for p in top_performers]}")
            logger.info(f"Worst 3 performers: {[p['name'] + ': ' + str(round(p['profit_loss_percentage'], 2)) + '%' for p in worst_performers]}")
            
            # Calculate asset breakdown percentages
            cards_percentage = (cards_value / total_value * 100) if total_value > 0 else 0
            steam_percentage = (steam_value / total_value * 100) if total_value > 0 else 0
            stocks_percentage = (stocks_value / total_value * 100) if total_value > 0 else 0
            etfs_percentage = (etfs_value / total_value * 100) if total_value > 0 else 0
            crypto_percentage = (crypto_value / total_value * 100) if total_value > 0 else 0
            
            return {
                'total_portfolio_value': total_value,
                'total_investment': total_investment,
                'total_profit_loss': profit_loss,
                'total_profit_loss_percentage': profit_loss_percentage,
                'total_cards': data['total_cards'],
                'asset_breakdown': {
                    'cards': {
                        'value': cards_value,
                        'percentage': cards_percentage,
                        'count': data['total_cards']
                    },
                    'stocks': {
                        'value': stocks_value,
                        'percentage': stocks_percentage,
                        'count': financial_stats['stocks']['count']
                    },
                    'etfs': {
                        'value': etfs_value,
                        'percentage': etfs_percentage,
                        'count': financial_stats['etfs']['count']
                    },
                    'crypto': {
                        'value': crypto_value,
                        'percentage': crypto_percentage,
                        'count': financial_stats['crypto']['count']
                    },
                    'steam': {
                        'value': steam_value,
                        'percentage': steam_percentage,
                        'count': steam_stats.get('total_items', 0)
                    }
                },
                'top_performers': top_performers,
                'worst_performers': worst_performers
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate portfolio summary: {e}")
            return {
                'total_portfolio_value': 0,
                'total_investment': 0,
                'total_profit_loss': 0,
                'total_profit_loss_percentage': 0,
                'asset_breakdown': {
                    'cards': {'value': 0, 'percentage': 100, 'count': 0}
                },
                'top_performers': [],
                'worst_performers': []
            }
    
    def _calculate_performers(self, items: List[Dict], asset_type: str) -> Dict:
        """Calculate top and worst performers for a list of items"""
        performers = []
        
        logger.info(f"Processing {len(items)} {asset_type} items for performance calculation")
        
        for item in items:
            price_bought = item.get('price_bought', 0)
            current_price = item.get('current_price', 0)
            name = item.get('name', 'Unknown')
            
            logger.debug(f"{asset_type} item '{name}': bought=${price_bought}, current=${current_price}")
            
            # Include items with purchase price OR Steam items with current value (treat as acquired for free)
            should_include = False
            if price_bought > 0:
                should_include = True
            elif asset_type == 'steam' and current_price > 0:
                # For Steam items without purchase price, treat as acquired for "free" (show current value as gain)
                should_include = True
                price_bought = 0.01  # Use tiny value to avoid division by zero
            
            if should_include:
                profit_loss_absolute = current_price - price_bought
                profit_loss_percentage = (profit_loss_absolute / price_bought) * 100
                
                performer = {
                    'id': str(item.get('_id', item.get('asset_id', 'unknown'))),
                    'name': name,
                    'current_price': current_price,
                    'price_bought': price_bought if price_bought > 0.01 else 0,  # Show 0 for "free" items
                    'profit_loss_absolute': profit_loss_absolute,
                    'profit_loss_percentage': profit_loss_percentage,
                    'asset_type': asset_type
                }
                
                performers.append(performer)
                logger.debug(f"Added performer: {name} ({asset_type}) - {profit_loss_percentage:.2f}%")
            else:
                logger.debug(f"Skipped {asset_type} item '{name}': no valid purchase price and no current value")
        
        # Sort by profit/loss percentage
        performers.sort(key=lambda x: x['profit_loss_percentage'], reverse=True)
        
        logger.info(f"{asset_type} performers summary: {len(performers)} valid items")
        if performers:
            logger.info(f"Best {asset_type} performer: {performers[0]['name']} ({performers[0]['profit_loss_percentage']:.2f}%)")
            logger.info(f"Worst {asset_type} performer: {performers[-1]['name']} ({performers[-1]['profit_loss_percentage']:.2f}%)")
        
        return {
            'all': performers,
            'top': performers[:3],
            'worst': performers[-3:] if len(performers) >= 3 else []
        }

class SteamItemModel:
    """Model for Steam inventory items"""
    
    def __init__(self, db):
        self.collection = db.steam_items
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary indexes"""
        try:
            # Index for user-specific queries
            self.collection.create_index([("user_id", 1)])
            
            # Compound index for duplicate detection
            self.collection.create_index([
                ("user_id", 1),
                ("asset_id", 1)
            ], unique=True)
            
            # Index for search and filtering
            self.collection.create_index([("name", "text")])
            
            logger.info("Steam item collection indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create steam item indexes: {e}")
    
    def create_item(self, item_data):
        """Create a new steam item"""
        try:
            item_data['created_at'] = datetime.utcnow()
            item_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.insert_one(item_data)
            
            # Return the created item with its ID
            created_item = self.collection.find_one({"_id": result.inserted_id})
            if created_item:
                created_item['_id'] = str(created_item['_id'])
            
            return created_item
            
        except DuplicateKeyError:
            raise ValueError("Steam item with this asset_id already exists for this user")
        except Exception as e:
            logger.error(f"Error creating steam item: {e}")
            raise
    
    def get_items_by_user(self, user_id, limit=None, skip=0):
        """Get all steam items for a user"""
        try:
            query = {"user_id": user_id}
            
            cursor = self.collection.find(query).sort("created_at", -1)
            
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            items = list(cursor)
            
            # Convert ObjectId to string
            for item in items:
                item['_id'] = str(item['_id'])
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting steam items for user {user_id}: {e}")
            raise
    
    def find_existing_item(self, user_id, asset_id):
        """Find an existing steam item by asset_id"""
        try:
            existing = self.collection.find_one({
                "user_id": user_id,
                "asset_id": asset_id
            })
            
            if existing:
                existing['_id'] = str(existing['_id'])
            
            return existing
            
        except Exception as e:
            logger.error(f"Error finding existing steam item: {e}")
            return None
    
    def get_user_items(self, user_id):
        """Get all steam items for a user"""
        try:
            items = list(self.collection.find({"user_id": user_id}))
            
            # Convert ObjectId to string
            for item in items:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting steam items for user {user_id}: {e}")
            return []
    
    def update_item(self, item_id, update_data):
        """Update a steam item"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            from bson import ObjectId
            result = self.collection.update_one(
                {"_id": ObjectId(item_id)},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise ValueError("Steam item not found")
            
            # Return updated item
            updated_item = self.collection.find_one({"_id": ObjectId(item_id)})
            if updated_item:
                updated_item['_id'] = str(updated_item['_id'])
            
            return updated_item
            
        except Exception as e:
            logger.error(f"Error updating steam item {item_id}: {e}")
            raise
    
    def delete_item(self, item_id, user_id):
        """Delete a steam item"""
        try:
            from bson import ObjectId
            result = self.collection.delete_one({
                "_id": ObjectId(item_id),
                "user_id": user_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting steam item {item_id}: {e}")
            raise
    
    def delete_all_items(self, user_id):
        """Delete all steam items for a user"""
        try:
            result = self.collection.delete_many({"user_id": user_id})
            logger.info(f"Deleted {result.deleted_count} steam items for user {user_id}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting all steam items for user {user_id}: {e}")
            raise
    
    # Removed update_item_price method - no pricing updates
    
    def get_user_stats(self, user_id):
        """Get statistics for user's steam inventory"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_items": {"$sum": 1},
                    "total_value": {"$sum": "$current_price"},
                    "total_bought": {"$sum": "$price_bought"},
                    "avg_value": {"$avg": "$current_price"},
                    "by_rarity": {
                        "$push": {
                            "rarity": "$rarity",
                            "value": "$current_price"
                        }
                    }
                }}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            if result:
                stats = result[0]
                
                # Calculate rarity distribution
                rarity_stats = {}
                for item in stats.get('by_rarity', []):
                    rarity = item.get('rarity', 'Unknown')
                    if rarity not in rarity_stats:
                        rarity_stats[rarity] = {'count': 0, 'value': 0}
                    rarity_stats[rarity]['count'] += 1
                    rarity_stats[rarity]['value'] += item.get('value', 0)
                
                return {
                    'total_items': stats.get('total_items', 0),
                    'total_value': round(stats.get('total_value', 0), 2),
                    'total_bought': round(stats.get('total_bought', 0), 2),
                    'avg_value': round(stats.get('avg_value', 0), 2),
                    'rarity_distribution': rarity_stats
                }
            
            return {
                'total_items': 0,
                'total_value': 0,
                'total_bought': 0,
                'avg_value': 0,
                'rarity_distribution': {}
            }
            
        except Exception as e:
            logger.error(f"Error getting steam stats for user {user_id}: {e}")
            raise

class FinancialAssetModel:
    """Model for managing financial assets (stocks, ETFs, crypto)"""
    
    def __init__(self, db):
        if db is None:
            raise ValueError("Database connection required for FinancialAssetModel")
        self.db = db
        self.collection = db.financial_assets
        self.ensure_indexes()
    
    def ensure_indexes(self):
        """Create necessary indexes for better performance"""
        try:
            # Create compound index for unique assets per user
            self.collection.create_index([
                ("user_id", 1),
                ("asset_type", 1),
                ("symbol", 1)
            ], unique=True)
            
            # Index for symbol searches
            self.collection.create_index([
                ("symbol", "text"),
                ("name", "text")
            ])
            
            logger.info("Financial assets collection indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create financial assets indexes: {e}")
    
    def create_asset(self, asset_data: Dict) -> str:
        """Create a new financial asset"""
        try:
            asset_data.update({
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'price_history': [{
                    'price': asset_data.get('current_price', 0),
                    'date': datetime.utcnow(),
                    'source': 'yfinance'
                }]
            })
            
            result = self.collection.insert_one(asset_data)
            logger.info(f"Created financial asset: {asset_data.get('symbol')} (ID: {result.inserted_id})")
            return str(result.inserted_id)
        except DuplicateKeyError:
            raise ValueError(f"Asset {asset_data.get('symbol')} already exists for this user")
        except Exception as e:
            logger.error(f"Error creating financial asset: {e}")
            raise
    
    def get_assets_by_type(self, user_id: str, asset_type: str) -> List[Dict]:
        """Get all assets of a specific type for a user"""
        try:
            assets = list(self.collection.find({
                'user_id': user_id,
                'asset_type': asset_type
            }).sort('symbol', 1))
            
            # Convert ObjectId to string
            for asset in assets:
                asset['id'] = str(asset['_id'])
                del asset['_id']
                asset['type'] = asset_type  # Ensure type field is set
                
            return assets
        except Exception as e:
            logger.error(f"Error getting {asset_type} for user {user_id}: {e}")
            raise
    
    def get_asset_by_id(self, user_id: str, asset_id: str) -> Optional[Dict]:
        """Get a specific asset by ID"""
        try:
            asset = self.collection.find_one({
                '_id': ObjectId(asset_id),
                'user_id': user_id
            })
            
            if asset:
                asset['id'] = str(asset['_id'])
                del asset['_id']
                
            return asset
        except Exception as e:
            logger.error(f"Error getting asset {asset_id}: {e}")
            return None
    
    def update_asset(self, user_id: str, asset_id: str, updates: Dict) -> bool:
        """Update an asset"""
        try:
            updates['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {'_id': ObjectId(asset_id), 'user_id': user_id},
                {'$set': updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated asset {asset_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating asset {asset_id}: {e}")
            raise
    
    def update_price(self, user_id: str, asset_id: str, new_price: float, source: str = 'yfinance') -> bool:
        """Update asset price and add to price history"""
        try:
            # Get current asset
            asset = self.get_asset_by_id(user_id, asset_id)
            if not asset:
                return False
            
            # Add to price history
            price_entry = {
                'price': new_price,
                'date': datetime.utcnow(),
                'source': source
            }
            
            result = self.collection.update_one(
                {'_id': ObjectId(asset_id), 'user_id': user_id},
                {
                    '$set': {
                        'current_price': new_price,
                        'updated_at': datetime.utcnow()
                    },
                    '$push': {
                        'price_history': {
                            '$each': [price_entry],
                            '$slice': -100  # Keep last 100 price updates
                        }
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating price for asset {asset_id}: {e}")
            raise
    
    def delete_asset(self, user_id: str, asset_id: str) -> bool:
        """Delete an asset"""
        try:
            result = self.collection.delete_one({
                '_id': ObjectId(asset_id),
                'user_id': user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"Deleted asset {asset_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting asset {asset_id}: {e}")
            raise
    
    def delete_all_assets(self, user_id: str, asset_type: str) -> int:
        """Delete all assets of a specific type for a user"""
        try:
            result = self.collection.delete_many({
                'user_id': user_id,
                'asset_type': asset_type
            })
            
            logger.info(f"Deleted {result.deleted_count} {asset_type} for user {user_id}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting all {asset_type} for user {user_id}: {e}")
            raise

# Global database instance
mongodb = MongoDB()
if mongodb.connected:
    # Initialize models
    card_model = CardModel(mongodb.db)
    steam_item_model = SteamItemModel(mongodb.db)
    financial_asset_model = FinancialAssetModel(mongodb.db)
else:
    card_model = None
    steam_item_model = None
    financial_asset_model = None
    logger.warning("Models not initialized - MongoDB not available")

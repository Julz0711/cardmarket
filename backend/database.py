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
    
    def find_existing_card(self, user_id: str, tcg: str, expansion: str, number: int) -> Optional[Dict]:
        """Find an existing card by user_id, tcg, expansion, and number"""
        try:
            query = {
                'user_id': user_id,
                'tcg': tcg,
                'expansion': expansion,
                'number': number
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
                            '$sum': {'$multiply': ['$current_price', '$quantity']}
                        },
                        'total_investment': {
                            '$sum': {'$multiply': ['$price_bought', '$quantity']}
                        },
                        'cards': {'$push': '$$ROOT'}
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            # Get Steam inventory stats if user_id is provided
            steam_stats = {'total_value': 0, 'total_bought': 0, 'total_items': 0}
            if user_id:
                try:
                    # Use global steam_item_model instance
                    global steam_item_model
                    if steam_item_model:
                        steam_stats = steam_item_model.get_user_stats(user_id)
                except Exception as e:
                    logger.warning(f"Failed to get Steam stats: {e}")
            
            if not result:
                return {
                    'total_portfolio_value': steam_stats.get('total_value', 0),
                    'total_investment': steam_stats.get('total_bought', 0),
                    'total_profit_loss': steam_stats.get('total_value', 0) - steam_stats.get('total_bought', 0),
                    'total_profit_loss_percentage': 0,
                    'asset_breakdown': {
                        'cards': {'value': 0, 'percentage': 0, 'count': 0},
                        'steam': {'value': steam_stats.get('total_value', 0), 'percentage': 100, 'count': steam_stats.get('total_items', 0)}
                    },
                    'top_performers': [],
                    'worst_performers': []
                }
            
            data = result[0]
            cards_value = data['total_value']
            cards_investment = data['total_investment']
            steam_value = steam_stats.get('total_value', 0)
            steam_investment = steam_stats.get('total_bought', 0)
            
            total_value = cards_value + steam_value
            total_investment = cards_investment + steam_investment
            profit_loss = total_value - total_investment
            profit_loss_percentage = (profit_loss / total_investment * 100) if total_investment > 0 else 0
            
            
            # Calculate top/worst performers
            cards = data['cards']
            performers = []
            for card in cards:
                if card['price_bought'] > 0:
                    card_profit_loss = (card['current_price'] - card['price_bought']) / card['price_bought'] * 100
                    performers.append({
                        'id': str(card['_id']),
                        'name': card['name'],
                        'current_price': card['current_price'],
                        'price_bought': card['price_bought'],
                        'profit_loss_percentage': card_profit_loss
                    })
            
            performers.sort(key=lambda x: x['profit_loss_percentage'], reverse=True)
            
            # Calculate asset breakdown percentages
            cards_percentage = (cards_value / total_value * 100) if total_value > 0 else 0
            steam_percentage = (steam_value / total_value * 100) if total_value > 0 else 0
            
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
                    'stocks': {'value': 0, 'percentage': 0, 'count': 0},
                    'etfs': {'value': 0, 'percentage': 0, 'count': 0},
                    'crypto': {'value': 0, 'percentage': 0, 'count': 0},
                    'steam': {
                        'value': steam_value,
                        'percentage': steam_percentage,
                        'count': steam_stats.get('total_items', 0)
                    }
                },
                'top_performers': performers[:5],
                'worst_performers': performers[-5:] if len(performers) > 5 else []
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

# Global database instance
mongodb = MongoDB()
if mongodb.connected:
    # Initialize models
    card_model = CardModel(mongodb.db)
    steam_item_model = SteamItemModel(mongodb.db)
else:
    card_model = None
    steam_item_model = None
    logger.warning("Models not initialized - MongoDB not available")

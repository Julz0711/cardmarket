"""
Authentication system for CardMarket app
Handles user registration, login, JWT tokens, and password hashing
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import logging
import os
from database import mongodb

logger = logging.getLogger(__name__)

class UserModel:
    def __init__(self, db):
        """Initialize User model with database reference"""
        if db is None:
            raise ValueError("Database connection required for UserModel")
        self.db = db
        self.collection = db.users
        self.ensure_indexes()
    
    def ensure_indexes(self):
        """Create necessary indexes for users"""
        try:
            # Unique index on email
            self.collection.create_index("email", unique=True)
            # Index on username for fast lookups
            self.collection.create_index("username")
            logger.info("User collection indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create user indexes: {e}")
    
    def create_user(self, user_data):
        """Create a new user"""
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(
                user_data['password'].encode('utf-8'), 
                bcrypt.gensalt()
            )
            
            user_doc = {
                'username': user_data['username'],
                'email': user_data['email'],
                'password_hash': password_hash,
                'created_at': datetime.now().isoformat(),
                'last_login': None,
                'is_active': True,
                'profile': {
                    'display_name': user_data.get('display_name', user_data['username']),
                    'bio': user_data.get('bio', ''),
                    'avatar_url': user_data.get('avatar_url', '')
                }
            }
            
            result = self.collection.insert_one(user_doc)
            user_doc['_id'] = result.inserted_id
            
            # Remove password hash from return value
            user_doc.pop('password_hash', None)
            
            logger.info(f"Created user: {user_data['username']}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def authenticate_user(self, email, password):
        """Authenticate user with email and password"""
        try:
            user = self.collection.find_one({'email': email})
            if not user:
                return None
            
            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                # Update last login
                self.collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {'last_login': datetime.now().isoformat()}}
                )
                
                # Remove password hash from return value
                user.pop('password_hash', None)
                user['user_id'] = str(user['_id'])
                
                logger.info(f"User authenticated: {email}")
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            from bson import ObjectId
            user = self.collection.find_one({'_id': ObjectId(user_id)})
            if user:
                user.pop('password_hash', None)
                user['user_id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            user = self.collection.find_one({'email': email})
            if user:
                user.pop('password_hash', None)
                user['user_id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def update_user(self, user_id, update_data):
        """Update user information"""
        try:
            from bson import ObjectId
            update_data['updated_at'] = datetime.now().isoformat()
            
            result = self.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

# JWT Token utilities
class JWTManager:
    @staticmethod
    def generate_token(user_id, username, email):
        """Generate JWT token for user"""
        try:
            payload = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'exp': datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
                'iat': datetime.utcnow()
            }
            
            secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            
            return token
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            return None
    
    @staticmethod
    def decode_token(token):
        """Decode and validate JWT token"""
        try:
            secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

# Authentication decorator
def auth_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid Authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token required'}), 401
        
        # Decode token
        payload = JWTManager.decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'email': payload['email']
        }
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication - provides default user if not authenticated"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
                payload = JWTManager.decode_token(token)
                if payload:
                    request.current_user = {
                        'user_id': payload['user_id'],
                        'username': payload['username'],
                        'email': payload['email']
                    }
                else:
                    # Invalid token, use default user
                    request.current_user = {
                        'user_id': 'default_user',
                        'username': 'Anonymous',
                        'email': 'anonymous@localhost'
                    }
            except:
                # No token or invalid format, use default user
                request.current_user = {
                    'user_id': 'default_user',
                    'username': 'Anonymous', 
                    'email': 'anonymous@localhost'
                }
        else:
            # No token provided, use default user
            request.current_user = {
                'user_id': 'default_user',
                'username': 'Anonymous',
                'email': 'anonymous@localhost'
            }
        
        return f(*args, **kwargs)
    
    return decorated_function

# Initialize user model
if mongodb.connected:
    user_model = UserModel(mongodb.db)
else:
    user_model = None
    logger.warning("UserModel not initialized - MongoDB not available")

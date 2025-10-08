import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from encryption import KeyEncryption
from config import FIREBASE_CREDENTIALS_PATH, FIREBASE_DATABASE_URL
import os

class FirebaseManager:
    def __init__(self):
        """Initialize Firebase connection"""
        self.db = None
        self.encryption = KeyEncryption()
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Try to load credentials from environment variable or file
                creds_loaded = False
                
                # Option 1: Try FIREBASE_CREDENTIALS from environment (base64 encoded JSON)
                firebase_creds_env = os.getenv('FIREBASE_CREDENTIALS')
                if firebase_creds_env:
                    try:
                        import base64
                        print("Loading Firebase credentials from FIREBASE_CREDENTIALS environment variable")
                        decoded_creds = base64.b64decode(firebase_creds_env).decode('utf-8')
                        firebase_creds = json.loads(decoded_creds)
                        
                        # Ensure private key has proper line breaks
                        if 'private_key' in firebase_creds and '\\n' in firebase_creds['private_key']:
                            firebase_creds['private_key'] = firebase_creds['private_key'].replace('\\n', '\n')
                        
                        cred = credentials.Certificate(firebase_creds)
                        firebase_admin.initialize_app(cred, {
                            'databaseURL': FIREBASE_DATABASE_URL
                        })
                        print("✅ Firebase initialized from environment variable successfully")
                        creds_loaded = True
                    except Exception as e:
                        print(f"Failed to load from FIREBASE_CREDENTIALS env var: {e}")
                
                # Option 2: Try firebase_credentials.json file
                if not creds_loaded and os.path.exists('firebase_credentials.json'):
                    try:
                        print("Loading Firebase credentials from firebase_credentials.json file")
                        cred = credentials.Certificate('firebase_credentials.json')
                        firebase_admin.initialize_app(cred, {
                            'databaseURL': FIREBASE_DATABASE_URL
                        })
                        print("✅ Firebase initialized from file successfully")
                        creds_loaded = True
                    except Exception as e:
                        print(f"Failed to load from firebase_credentials.json: {e}")
                
                # Option 3: Fallback to hardcoded credentials with proper key formatting
                if not creds_loaded:
                    # Hardcoded Firebase credentials with properly formatted private key
                    private_key_lines = [
                        "-----BEGIN PRIVATE KEY-----",
                        "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCILu4SHrTMSfpl",
                        "51K5EgHfWej5dyxW4YEwLReSiuEFtf/ibst/SMylzGMYCk21KLJELV3vDrsgQuou",
                        "3MYEuZI3IVzKHFlTYPnRDcoBPsFIJGsVEKjj9yKEQNTWRMHhhV4L2veqWIDiP89J",
                        "VT4FQAmxvA3NIlhzulZwmuUDZuA39cz08Nt3CR46pqIklC/jnA/155pgSHV2vFRr",
                        "w4QkP6lSng5nZMTPkBC+kEIUPRPERzbdv7ykmHd1lVEqPxLOBRc4fLqU8s4YCcDx",
                        "BamJflujEIEGGg91VnrGyx1hs13kLSzCAoZEIZAUxkrkBfvBJrqzitsTlgJ3gq/1",
                        "gHj5l0IpAgMBAAECggEAJKv+kAKUzS5er3JLZGrk9jBP/F2LIxo2n7KE1oFvdwo7",
                        "jc4oHm6MLVmMlbywkEgVOSa+VNGysk1Soqvw5vTR2uaxBfv8UeebXiBIdW1gvvyP",
                        "mWyTDlBOiy6qIckCLKitWqPsbYLHsiVcvHKn8OH9uk7ZqJPHHeLfxBLx+KiLWIYD",
                        "yo1GMp0ZIuUJqNawBsiiGfTfoKrKrwVh0NsdGVxJ2ovCAlvqVyd44Gfcrh4sBDHA",
                        "kpXy/NNllAkUeRyP5+ekDKJ8FyV3mxriuGlDt4R7/tVTnqf61vfx2TZPpdDrc7iZ",
                        "nmJ6hBmpEtdDa1b++RwrAulk3foJjUYOib1Nb00GwQKBgQC8fVCSWcAVJbIdub7j",
                        "PwxkS+as48byMjmKFt22qTXiH/D40+AGn7VN9t4hcJbnlvWM82uY9nbfIoMMc6Yu",
                        "UH8BA10HFMKtZxOh5mpiG0IQIrpxmccbDB7q0+mQg86hy7OVPwhuuhxI+n/kkrHA",
                        "IMyav9CT3o1iP6Vr4NkrwUEwBwKBgQC49aNKvZ1Y7CIOxrzNBxNfCQ+kh0NhAeYd",
                        "VLXJ7y5nAwPwARjd8Hdsjw3Y1dss1se7BwOFlW/GorL8gApBfs6PEQ3veTPb+6jd",
                        "iwNQPSUI15WeVd/uKOLzu4Y1bGQi2JcbPWe+UcsQJaSKBb9Plb8GqslAXpgu2aPE",
                        "bojLEH8QTwKBgQCf9Liref7H83V0RGz57EdX1hGsJqBuaLDrvvvoRzCy9OhKQYOc",
                        "G2yA/T8EocduQW2gb/KfnIjEU0VjC8G7DBS7h18q4zNSdGb0vdUJ7JfjmZUfUqDl",
                        "EyQppCxRt4ljRLrhrNw7GzVluS9Pii3OHgeES8N1uSfCeMCpC+dAeoAXgQKBgQCu",
                        "Q2llev9sD5cLGv45okgDC3N8jaDTHknkKrLYnoy2q6WjFDWMrgqm8qWWPe+x8G7g",
                        "bPxJeQGGQjanJjADg2k0bFoX3bcZtaNlkJs/l0x0Z0Jlmv1P05/5Ch6p6QTzu+Oq",
                        "25EKROAwx3aeQEn+vtTrgC/7gOSbh5z/7zDdOh6tiwKBgQCIEvsBTvcaxZhDZK9u",
                        "2aNg+RCjmcw+YUxU+EJFQTdDxxkN/hSWewt+w7S0DG+EMK/wiKfLs7kxVwEdbY8Q",
                        "ZUnjBOwlNroSKp+dPirn96ojjuCUHrrgE5P264KaqJyqFYJXPjHFIZuuca8QECsA",
                        "yENcecpTynONtPgb+nvmw9RGNQ==",
                        "-----END PRIVATE KEY-----"
                    ]
                    
                    firebase_creds = {
                        "type": "service_account",
                        "project_id": "parivar-50ef1",
                        "private_key_id": "8c5e9d4e0849876ea30846f3c35590c6b7780414",
                        "private_key": "\n".join(private_key_lines),
                        "client_email": "firebase-adminsdk-fbsvc@parivar-50ef1.iam.gserviceaccount.com",
                        "client_id": "117824911279718345875",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40parivar-50ef1.iam.gserviceaccount.com",
                        "universe_domain": "googleapis.com"
                    }
                    
                    try:
                        print("Using hardcoded Firebase credentials with properly formatted key")
                        cred = credentials.Certificate(firebase_creds)
                        firebase_admin.initialize_app(cred, {
                            'databaseURL': FIREBASE_DATABASE_URL
                        })
                        print("✅ Firebase initialized with hardcoded credentials successfully")
                        creds_loaded = True
                    except Exception as e:
                        print(f"❌ Error loading hardcoded Firebase credentials: {e}")
                        print("Warning: Using default Firebase app.")
                        firebase_admin.initialize_app()
            
            # Initialize Firestore
            self.db = firestore.client()
            print("Firebase initialized successfully")
            
            # Test the connection
            try:
                # Try to access a collection to test the connection
                test_collection = self.db.collection('test_connection')
                print("✅ Firebase connection test successful")
            except Exception as e:
                print(f"⚠️ Firebase connection test failed: {e}")
                print("This might indicate a credentials or permissions issue")
            
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            # Create a mock database for testing
            self.db = MockFirestore()
    
    def save_user_wallet(self, user_id: int, username: str, public_key: str, 
                        private_key: str, wallet_type: str) -> bool:
        """Save user wallet to Firebase"""
        try:
            if not self.db:
                return False
            
            # Encrypt private key before storing
            encrypted_private_key = self.encryption.encrypt_private_key(private_key)
            
            # Prepare wallet data
            wallet_data = {
                'user_id': user_id,
                'username': username,
                'public_key': public_key,
                'encrypted_private_key': encrypted_private_key,
                'type': wallet_type,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to Firestore
            doc_ref = self.db.collection('wallets').document(str(user_id))
            doc_ref.set(wallet_data)
            
            return True
            
        except Exception as e:
            print(f"Error saving wallet: {e}")
            return False
    
    def get_user_wallet(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user wallet from Firebase"""
        try:
            if not self.db:
                print(f"Firebase database not initialized for user {user_id}")
                return None
            
            print(f"Attempting to get wallet for user {user_id}")
            doc_ref = self.db.collection('wallets').document(str(user_id))
            doc = doc_ref.get()
            
            if doc.exists:
                wallet_data = doc.to_dict()
                print(f"Wallet found for user {user_id}: {wallet_data.get('public_key', 'No public key')[:20]}...")
                # Don't return encrypted private key in public wallet data
                return {
                    'user_id': wallet_data['user_id'],
                    'username': wallet_data['username'],
                    'public_key': wallet_data['public_key'],
                    'type': wallet_data['type'],
                    'created_at': wallet_data['created_at'],
                    'updated_at': wallet_data['updated_at']
                }
            else:
                print(f"No wallet found for user {user_id}")
            
            return None
            
        except Exception as e:
            print(f"Error getting wallet for user {user_id}: {e}")
            return None
    
    def get_private_key(self, user_id: int) -> Optional[str]:
        """Get decrypted private key for user"""
        try:
            if not self.db:
                return None
            
            doc_ref = self.db.collection('wallets').document(str(user_id))
            doc = doc_ref.get()
            
            if doc.exists:
                wallet_data = doc.to_dict()
                encrypted_private_key = wallet_data.get('encrypted_private_key')
                if encrypted_private_key:
                    return self.encryption.decrypt_private_key(encrypted_private_key)
            
            return None
            
        except Exception as e:
            print(f"Error getting private key: {e}")
            return None

    def check_twitter_auth(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Check if user has Twitter authentication"""
        try:
            if not self.db:
                return None
            
            doc_ref = self.db.collection('twitter_auth').document(str(user_id))
            doc = doc_ref.get()
            
            if doc.exists:
                auth_data = doc.to_dict()
                # Check if access token is still valid
                if auth_data.get('expiresAt') and auth_data.get('expiresAt') > datetime.now().timestamp() * 1000:
                    return auth_data
                else:
                    # Token expired, remove the document
                    doc_ref.delete()
                    return None
            
            return None
            
        except Exception as e:
            print(f"Error checking Twitter auth: {e}")
            return None

    def save_twitter_auth(self, user_id: int, auth_data: Dict[str, Any]) -> bool:
        """Save Twitter authentication data"""
        try:
            if not self.db:
                return False
            
            # Prepare auth data
            twitter_auth_data = {
                'userId': str(user_id),
                'accessToken': auth_data.get('accessToken'),
                'refreshToken': auth_data.get('refreshToken'),
                'twitterId': auth_data.get('twitterId'),
                'twitterUsername': auth_data.get('twitterUsername'),
                'createdAt': auth_data.get('createdAt'),
                'expiresAt': auth_data.get('expiresAt')
            }
            
            # Save to Firestore
            doc_ref = self.db.collection('twitter_auth').document(str(user_id))
            doc_ref.set(twitter_auth_data)
            
            return True
            
        except Exception as e:
            print(f"Error saving Twitter auth: {e}")
            return False

    def get_twitter_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get Twitter user information"""
        try:
            if not self.db:
                return None
            
            doc_ref = self.db.collection('twitter_auth').document(str(user_id))
            doc = doc_ref.get()
            
            if doc.exists:
                auth_data = doc.to_dict()
                # Check if access token is still valid
                if auth_data.get('expiresAt') and auth_data.get('expiresAt') > datetime.now().timestamp() * 1000:
                    return {
                        'twitterUsername': auth_data.get('twitterUsername'),
                        'twitterId': auth_data.get('twitterId'),
                        'isAuthenticated': True
                    }
            
            return {'isAuthenticated': False}
            
        except Exception as e:
            print(f"Error getting Twitter user info: {e}")
            return {'isAuthenticated': False}
    
    def remove_twitter_auth(self, user_id: int) -> bool:
        """Remove Twitter authentication data"""
        try:
            if not self.db:
                return False
            
            doc_ref = self.db.collection('twitter_auth').document(str(user_id))
            doc_ref.delete()
            
            return True
            
        except Exception as e:
            print(f"Error removing Twitter auth: {e}")
            return False
    
    def user_has_wallet(self, user_id: int) -> bool:
        """Check if user has a wallet"""
        try:
            if not self.db:
                print(f"Firebase database not initialized for user {user_id}")
                return False
            
            print(f"Checking if user {user_id} has a wallet")
            doc_ref = self.db.collection('wallets').document(str(user_id))
            doc = doc_ref.get()
            has_wallet = doc.exists
            print(f"User {user_id} has wallet: {has_wallet}")
            return has_wallet
            
        except Exception as e:
            print(f"Error checking wallet existence for user {user_id}: {e}")
            return False
    
    def delete_user_wallet(self, user_id: int) -> bool:
        """Delete user wallet from Firebase"""
        try:
            if not self.db:
                return False
            
            doc_ref = self.db.collection('wallets').document(str(user_id))
            doc_ref.delete()
            
            return True
            
        except Exception as e:
            print(f"Error deleting wallet: {e}")
            return False
    
    def update_wallet(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update wallet information"""
        try:
            if not self.db:
                return False
            
            # Add updated timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            doc_ref = self.db.collection('wallets').document(str(user_id))
            doc_ref.update(updates)
            
            return True
            
        except Exception as e:
            print(f"Error updating wallet: {e}")
            return False
    
    def get_all_wallets(self) -> List[Dict[str, Any]]:
        """Get all wallets (for admin purposes)"""
        try:
            if not self.db:
                return []
            
            wallets = []
            docs = self.db.collection('wallets').stream()
            
            for doc in docs:
                wallet_data = doc.to_dict()
                # Remove sensitive data
                wallet_data.pop('encrypted_private_key', None)
                wallets.append(wallet_data)
            
            return wallets
            
        except Exception as e:
            print(f"Error getting all wallets: {e}")
            return []
    
    def save_trade_history(self, user_id: int, trade_data: Dict[str, Any]) -> bool:
        """Save trade history"""
        try:
            if not self.db:
                return False
            
            # Add metadata
            trade_data['user_id'] = user_id
            trade_data['timestamp'] = datetime.now().isoformat()
            
            # Save to trades collection
            self.db.collection('trades').add(trade_data)
            
            return True
            
        except Exception as e:
            print(f"Error saving trade history: {e}")
            return False
    
    def get_user_trades(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's trade history"""
        try:
            if not self.db:
                return []
            
            trades = []
            docs = self.db.collection('trades').where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            for doc in docs:
                trades.append(doc.to_dict())
            
            return trades
            
        except Exception as e:
            print(f"Error getting user trades: {e}")
            return []


class MockFirestore:
    """Mock Firestore for testing when Firebase is not available"""
    
    def __init__(self):
        self.collections = {}
        print("Using mock Firestore for testing")
    
    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection()
        return self.collections[name]


class MockCollection:
    """Mock collection for testing"""
    
    def __init__(self):
        self.documents = {}
    
    def document(self, doc_id):
        if doc_id not in self.documents:
            self.documents[doc_id] = MockDocument()
        return self.documents[doc_id]
    
    def add(self, data):
        doc_id = str(len(self.documents) + 1)
        self.documents[doc_id] = MockDocument(data)
        return MockDocumentReference(doc_id, self)
    
    def where(self, field, op, value):
        return MockQuery(self.documents, field, op, value)
    
    def order_by(self, field, direction=None):
        return MockQuery(self.documents, field, '==', None, order_by=field, direction=direction)
    
    def limit(self, limit):
        return MockQuery(self.documents, None, None, None, limit=limit)
    
    def stream(self):
        return [MockDocumentSnapshot(doc_id, doc) for doc_id, doc in self.documents.items()]


class MockDocument:
    """Mock document for testing"""
    
    def __init__(self, data=None):
        self.data = data or {}
    
    def set(self, data):
        self.data.update(data)
    
    def get(self):
        return MockDocumentSnapshot(None, self)
    
    def update(self, updates):
        self.data.update(updates)
    
    def delete(self):
        pass


class MockDocumentSnapshot:
    """Mock document snapshot for testing"""
    
    def __init__(self, doc_id, doc):
        self.id = doc_id
        self.doc = doc
    
    def exists(self):
        return True
    
    def to_dict(self):
        return self.doc.data


class MockDocumentReference:
    """Mock document reference for testing"""
    
    def __init__(self, doc_id, collection):
        self.id = doc_id
        self.collection = collection


class MockQuery:
    """Mock query for testing"""
    
    def __init__(self, documents, field, op, value, order_by=None, direction=None, limit=None):
        self.documents = documents
        self.field = field
        self.op = op
        self.value = value
        self.order_by = order_by
        self.direction = direction
        self.limit = limit
    
    def stream(self):
        # Simple mock implementation
        docs = list(self.documents.values())
        if self.limit:
            docs = docs[:self.limit]
        return [MockDocumentSnapshot(None, doc) for doc in docs]



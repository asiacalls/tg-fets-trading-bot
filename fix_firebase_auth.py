#!/usr/bin/env python3
"""
Fix Firebase Authentication Issues
"""

import json
import base64
import os
from datetime import datetime

def generate_fresh_firebase_credentials():
    """Generate fresh Firebase credentials with proper formatting"""
    
    if not os.path.exists('firebase_credentials.json'):
        print("ERROR: firebase_credentials.json not found!")
        print("Please make sure you have the Firebase service account key file.")
        return None
    
    try:
        # Read the Firebase credentials file
        with open('firebase_credentials.json', 'r') as f:
            creds_data = json.load(f)
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email', 'client_id']
        for field in required_fields:
            if field not in creds_data:
                print(f"ERROR: Missing required field: {field}")
                return None
        
        # Ensure proper formatting
        if not creds_data['private_key'].startswith('-----BEGIN PRIVATE KEY-----'):
            print("ERROR: Invalid private key format")
            return None
        
        # Convert to JSON string with proper formatting
        creds_json = json.dumps(creds_data, separators=(',', ':'))
        
        # Encode to Base64
        creds_base64 = base64.b64encode(creds_json.encode('utf-8')).decode('utf-8')
        
        print("SUCCESS: Fresh Firebase credentials generated!")
        print("=" * 80)
        print("Copy this EXACT value to Render's FIREBASE_CREDENTIALS environment variable:")
        print("=" * 80)
        print(creds_base64)
        print("=" * 80)
        
        # Save to file
        with open('firebase_creds_fresh.txt', 'w') as f:
            f.write(creds_base64)
        
        print("Credentials saved to: firebase_creds_fresh.txt")
        print(f"Generated at: {datetime.now().isoformat()}")
        
        return creds_base64
        
    except Exception as e:
        print(f"ERROR: Failed to generate credentials: {e}")
        return None

def create_minimal_firebase_config():
    """Create a minimal Firebase configuration for testing"""
    
    # Read from existing credentials file to avoid hardcoding secrets
    if not os.path.exists('firebase_credentials.json'):
        print("ERROR: firebase_credentials.json not found!")
        return None
    
    try:
        with open('firebase_credentials.json', 'r') as f:
            creds_data = json.load(f)
        
        # Create minimal config with only essential fields
        minimal_config = {
            "type": creds_data.get("type", "service_account"),
            "project_id": creds_data.get("project_id"),
            "private_key_id": creds_data.get("private_key_id"),
            "private_key": creds_data.get("private_key"),
            "client_email": creds_data.get("client_email"),
            "client_id": creds_data.get("client_id"),
            "auth_uri": creds_data.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": creds_data.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": creds_data.get("client_x509_cert_url"),
            "universe_domain": creds_data.get("universe_domain", "googleapis.com")
        }
    except Exception as e:
        print(f"ERROR: Failed to read credentials: {e}")
        return None
    
    # Convert to JSON string
    creds_json = json.dumps(minimal_config, separators=(',', ':'))
    
    # Encode to Base64
    creds_base64 = base64.b64encode(creds_json.encode('utf-8')).decode('utf-8')
    
    print("SUCCESS: Minimal Firebase configuration generated!")
    print("=" * 80)
    print("Copy this EXACT value to Render's FIREBASE_CREDENTIALS environment variable:")
    print("=" * 80)
    print(creds_base64)
    print("=" * 80)
    
    # Save to file
    with open('firebase_creds_minimal.txt', 'w') as f:
        f.write(creds_base64)
    
    print("Credentials saved to: firebase_creds_minimal.txt")
    return creds_base64

if __name__ == "__main__":
    print("Firebase Authentication Fix Tool")
    print("=" * 40)
    
    # Try fresh credentials first
    fresh_creds = generate_fresh_firebase_credentials()
    
    if fresh_creds:
        print("\n" + "=" * 40)
        print("If the above doesn't work, try this minimal config:")
        print("=" * 40)
        minimal_creds = create_minimal_firebase_config()
    else:
        print("\nTrying minimal configuration...")
        minimal_creds = create_minimal_firebase_config()

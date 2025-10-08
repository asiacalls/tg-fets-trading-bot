#!/usr/bin/env python3
"""
Helper script to encode Firebase credentials for deployment
Run this to generate base64-encoded credentials for environment variables
"""

import json
import base64
import os

def encode_firebase_credentials():
    """Encode Firebase credentials to base64 for environment variables"""
    
    # Check if firebase_credentials.json exists
    if os.path.exists('firebase_credentials.json'):
        print("📁 Found firebase_credentials.json")
        with open('firebase_credentials.json', 'r') as f:
            creds = json.load(f)
    else:
        print("❌ firebase_credentials.json not found")
        print("Using default hardcoded credentials instead...")
        
        # Use the hardcoded credentials
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
        
        creds = {
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
    
    # Convert to JSON string
    creds_json = json.dumps(creds)
    
    # Encode to base64
    encoded = base64.b64encode(creds_json.encode('utf-8')).decode('utf-8')
    
    print("\n" + "="*60)
    print("✅ Firebase credentials encoded successfully!")
    print("="*60)
    print("\nAdd this to your deployment environment variables:")
    print("\n" + "-"*60)
    print(f"FIREBASE_CREDENTIALS={encoded}")
    print("-"*60)
    print("\nFor Oracle Cloud (.env file):")
    print(f"echo 'FIREBASE_CREDENTIALS={encoded}' >> oracle-deploy/env.production")
    print("\nFor other platforms:")
    print("Copy the FIREBASE_CREDENTIALS line above to your platform's environment variables")
    print("="*60)
    
    # Also save to a file for easy reference
    with open('firebase_creds_encoded.txt', 'w') as f:
        f.write(f"FIREBASE_CREDENTIALS={encoded}\n")
    
    print("\n📄 Also saved to: firebase_creds_encoded.txt")
    
    return encoded

if __name__ == "__main__":
    encode_firebase_credentials()


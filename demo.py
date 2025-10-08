#!/usr/bin/env python3
"""
Demo script for TG-Fets Trading Bot
This script demonstrates the core functionality without requiring Telegram or Firebase setup
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encryption import KeyEncryption
from blockchain_manager import BlockchainManager
from keyboard_manager import KeyboardManager

def demo_encryption():
    """Demonstrate encryption functionality"""
    print("🔐 Encryption Demo")
    print("-" * 30)
    
    encryption = KeyEncryption()
    
    # Test private key
    test_key = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    test_key_with_prefix = "0x" + test_key
    
    print(f"Original key: {test_key[:16]}...")
    print(f"Key with prefix: {test_key_with_prefix[:18]}...")
    
    # Encrypt
    encrypted = encryption.encrypt_private_key(test_key)
    print(f"Encrypted: {encrypted[:32]}...")
    
    # Decrypt
    decrypted = encryption.decrypt_private_key(encrypted)
    print(f"Decrypted: {decrypted[:16]}...")
    
    # Validation
    print(f"Valid key: {encryption.validate_private_key(test_key)}")
    print(f"Valid key with prefix: {encryption.validate_private_key(test_key_with_prefix)}")
    print(f"Invalid key: {encryption.validate_private_key('invalid')}")
    
    print()

def demo_blockchain():
    """Demonstrate blockchain functionality"""
    print("⛓️  Blockchain Demo")
    print("-" * 30)
    
    blockchain = BlockchainManager()
    
    # Create wallet
    print("Creating new wallet...")
    wallet = blockchain.create_wallet()
    print(f"Public key: {wallet['public_key']}")
    print(f"Private key: {wallet['private_key'][:16]}...")
    
    # Validate private key
    print("\nValidating private key...")
    public_from_private = blockchain.validate_private_key(wallet['private_key'])
    print(f"Derived public key: {public_from_private}")
    print(f"Match: {wallet['public_key'] == public_from_private}")
    
    # Chain support
    print("\nSupported chains:")
    for chain in ['ETH', 'BSC', 'BSC-TEST', 'UNKNOWN']:
        supported = blockchain.is_chain_supported(chain)
        print(f"  {chain}: {'✅' if supported else '❌'}")
    
    print()

def demo_keyboards():
    """Demonstrate keyboard layouts"""
    print("⌨️  Keyboard Layouts Demo")
    print("-" * 30)
    
    keyboard = KeyboardManager()
    
    # Main menu
    print("Main Menu:")
    main_menu = keyboard.get_main_menu()
    for row in main_menu.inline_keyboard:
        for button in row:
            print(f"  - {button.text} -> {button.callback_data}")
    
    print("\nBuy/Sell Menu:")
    buy_sell_menu = keyboard.get_buy_sell_menu()
    for row in buy_sell_menu.inline_keyboard:
        for button in row:
            print(f"  - {button.text} -> {button.callback_data}")
    
    print("\nChain Selection Menu:")
    chain_menu = keyboard.get_chain_selection_menu("balance")
    for row in chain_menu.inline_keyboard:
        for button in row:
            print(f"  - {button.text} -> {button.callback_data}")
    
    print()

def demo_wallet_flow():
    """Demonstrate wallet creation and validation flow"""
    print("💼 Wallet Flow Demo")
    print("-" * 30)
    
    blockchain = BlockchainManager()
    encryption = KeyEncryption()
    
    # Simulate user creating a wallet
    print("1. User clicks 'Create Wallet'")
    wallet = blockchain.create_wallet()
    print(f"   Generated wallet: {wallet['public_key'][:16]}...")
    
    # Simulate saving to database (encrypted)
    print("\n2. Encrypting private key for storage...")
    encrypted_key = encryption.encrypt_private_key(wallet['private_key'])
    print(f"   Encrypted key: {encrypted_key[:32]}...")
    
    # Simulate retrieving from database
    print("\n3. Retrieving private key from storage...")
    decrypted_key = encryption.decrypt_private_key(encrypted_key)
    print(f"   Decrypted key: {decrypted_key[:16]}...")
    
    # Validate the retrieved key
    print("\n4. Validating retrieved private key...")
    public_key = blockchain.validate_private_key(decrypted_key)
    print(f"   Derived public key: {public_key}")
    print(f"   Validation successful: {public_key == wallet['public_key']}")
    
    print()

def demo_trading_flow():
    """Demonstrate trading flow"""
    print("📈 Trading Flow Demo")
    print("-" * 30)
    
    blockchain = BlockchainManager()
    
    # Simulate user selecting buy/sell
    print("1. User selects 'Buy'")
    action = "buy"
    
    # Simulate chain selection
    print("2. User selects 'BSC'")
    chain = "BSC"
    
    # Simulate wallet check
    print("3. Checking if user has wallet...")
    # In real scenario, this would check Firebase
    has_wallet = True  # Simulated
    
    if has_wallet:
        print("   ✅ Wallet found")
        print("   Proceeding to trading interface...")
        print("   (Trading execution would happen here)")
    else:
        print("   ❌ No wallet found")
        print("   Redirecting to wallet creation/import...")
    
    print()

def main():
    """Main demo function"""
    print("🤖 TG-Fets Trading Bot - Demo Mode")
    print("=" * 50)
    print("This demo showcases the core functionality without requiring")
    print("Telegram Bot API or Firebase setup.")
    print()
    
    try:
        demo_encryption()
        demo_blockchain()
        demo_keyboards()
        demo_wallet_flow()
        demo_trading_flow()
        
        print("🎉 Demo completed successfully!")
        print("\n💡 To run the actual bot:")
        print("1. Set up your environment variables")
        print("2. Configure Firebase credentials")
        print("3. Run: python main.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main()

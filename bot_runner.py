#!/usr/bin/env python3
"""
TG-Fets Trading Bot Runner - Python 3.13 Compatible
A simplified version that demonstrates all bot functionality
"""

import sys
import os
import asyncio
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class BotSimulator:
    """Simulates the Telegram bot interface"""
    
    def __init__(self):
        self.firebase = None
        self.blockchain = None
        self.trading = None
        self.encryption = None
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize all bot components"""
        try:
            from firebase_manager import FirebaseManager
            from blockchain_manager import BlockchainManager
            from trading_manager import TradingManager
            from encryption import KeyEncryption
            
            self.firebase = FirebaseManager()
            self.blockchain = BlockchainManager()
            self.trading = TradingManager()
            self.encryption = KeyEncryption()
            
            print("✅ All components initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            sys.exit(1)
    
    def show_main_menu(self):
        """Show the main menu"""
        print("\n🤖 TG-Fets Trading Bot - Main Menu")
        print("=" * 40)
        print("1. 💰 Buy/Sell Tokens")
        print("2. 🔐 Wallet Management")
        print("3. 💳 Check Balance")
        print("4. 💸 Transfer Tokens")
        print("5. 🔍 Token Scanner")
        print("6. ⚙️ Settings")
        print("7. 🧪 Run Demo")
        print("8. ❌ Exit")
        print("=" * 40)
    
    def handle_wallet_management(self):
        """Handle wallet management"""
        print("\n🔐 Wallet Management")
        print("-" * 25)
        
        # Check if user has wallet
        user_id = 12345  # Demo user ID
        
        if self.firebase.user_has_wallet(user_id):
            print("✅ You have a wallet!")
            wallet = self.firebase.get_user_wallet(user_id)
            print(f"Address: {wallet['public_key']}")
            print(f"Created: {wallet['created_at'][:10]}")
            
            choice = input("\n1. Show Private Key\n2. Delete Wallet\n3. Back\nChoice: ")
            
            if choice == "1":
                private_key = self.firebase.get_private_key(user_id)
                if private_key:
                    print(f"\n🔑 Private Key: {private_key}")
                    print("⚠️  Keep this secure and never share it!")
                else:
                    print("❌ Could not retrieve private key")
            elif choice == "2":
                if self.firebase.delete_user_wallet(user_id):
                    print("✅ Wallet deleted successfully")
                else:
                    print("❌ Failed to delete wallet")
        else:
            print("❌ You don't have a wallet yet")
            choice = input("\n1. Create New Wallet\n2. Import Wallet\n3. Back\nChoice: ")
            
            if choice == "1":
                self.create_wallet(user_id)
            elif choice == "2":
                self.import_wallet(user_id)
    
    def create_wallet(self, user_id):
        """Create a new wallet"""
        print("\n🆕 Creating new wallet...")
        
        try:
            wallet_data = self.blockchain.create_wallet()
            username = "demo_user"
            
            success = self.firebase.save_user_wallet(
                user_id, username, wallet_data['public_key'], 
                wallet_data['private_key'], "created"
            )
            
            if success:
                print("✅ Wallet created successfully!")
                print(f"Public Key: {wallet_data['public_key']}")
                print("⚠️  Private key has been encrypted and stored securely")
            else:
                print("❌ Failed to create wallet")
                
        except Exception as e:
            print(f"❌ Error creating wallet: {e}")
    
    def import_wallet(self, user_id):
        """Import existing wallet"""
        print("\n📥 Importing wallet...")
        print("⚠️  Enter your private key (64 characters):")
        
        private_key = input("Private Key: ").strip()
        
        if len(private_key) != 64:
            print("❌ Invalid private key length")
            return
        
        # Validate private key
        public_key = self.blockchain.validate_private_key(private_key)
        
        if not public_key:
            print("❌ Invalid private key")
            return
        
        # Save to database
        username = "demo_user"
        success = self.firebase.save_user_wallet(
            user_id, username, public_key, private_key, "imported"
        )
        
        if success:
            print("✅ Wallet imported successfully!")
            print(f"Public Key: {public_key}")
        else:
            print("❌ Failed to import wallet")
    
    def handle_trading(self):
        """Handle trading operations"""
        print("\n💰 Trading Operations")
        print("-" * 25)
        
        user_id = 12345
        
        if not self.firebase.user_has_wallet(user_id):
            print("❌ You need a wallet first!")
            return
        
        print("1. 🟢 Buy Tokens")
        print("2. 🔴 Sell Tokens")
        print("3. Back")
        
        choice = input("Choice: ")
        
        if choice == "1":
            self.buy_tokens(user_id)
        elif choice == "2":
            self.sell_tokens(user_id)
    
    def buy_tokens(self, user_id):
        """Buy tokens"""
        print("\n🟢 Buying Tokens")
        print("-" * 20)
        
        try:
            amount = float(input("Enter BNB amount: "))
            token_address = input("Enter token address: ")
            
            if not token_address.startswith('0x') or len(token_address) != 42:
                print("❌ Invalid token address")
                return
            
            # Get wallet
            wallet = self.firebase.get_user_wallet(user_id)
            private_key = self.firebase.get_private_key(user_id)
            
            if not private_key:
                print("❌ Could not retrieve private key")
                return
            
            print(f"\n📋 Trade Summary:")
            print(f"Amount: {amount} BNB")
            print(f"Token: {token_address[:10]}...")
            print(f"Chain: BSC-TEST")
            
            confirm = input("\nConfirm trade? (y/n): ")
            if confirm.lower() == 'y':
                print("⏳ Executing trade...")
                # In real implementation, this would execute the trade
                print("✅ Trade executed successfully!")
                print("(This is a simulation - no actual trade was made)")
            else:
                print("❌ Trade cancelled")
                
        except ValueError:
            print("❌ Invalid amount")
    
    def sell_tokens(self, user_id):
        """Sell tokens"""
        print("\n🔴 Selling Tokens")
        print("-" * 20)
        
        try:
            amount = float(input("Enter token amount: "))
            token_address = input("Enter token address: ")
            
            if not token_address.startswith('0x') or len(token_address) != 42:
                print("❌ Invalid token address")
                return
            
            print(f"\n📋 Trade Summary:")
            print(f"Amount: {amount} tokens")
            print(f"Token: {token_address[:10]}...")
            print(f"Chain: BSC-TEST")
            
            confirm = input("\nConfirm trade? (y/n): ")
            if confirm.lower() == 'y':
                print("⏳ Executing trade...")
                # In real implementation, this would execute the trade
                print("✅ Trade executed successfully!")
                print("(This is a simulation - no actual trade was made)")
            else:
                print("❌ Trade cancelled")
                
        except ValueError:
            print("❌ Invalid amount")
    
    def check_balance(self):
        """Check wallet balance"""
        print("\n💳 Balance Check")
        print("-" * 20)
        
        user_id = 12345
        
        if not self.firebase.user_has_wallet(user_id):
            print("❌ You need a wallet first!")
            return
        
        wallet = self.firebase.get_user_wallet(user_id)
        print(f"Wallet: {wallet['public_key'][:20]}...")
        
        # Check balance on different chains
        chains = ['BSC-TEST', 'BSC', 'ETH']
        
        for chain in chains:
            balance = self.blockchain.get_balance(chain, wallet['public_key'])
            if balance is not None:
                symbol = 'BNB' if 'BSC' in chain else 'ETH'
                print(f"{chain}: {balance:.6f} {symbol}")
            else:
                print(f"{chain}: Connection failed")
    
    def token_scanner(self):
        """Token scanner functionality"""
        print("\n🔍 Token Scanner")
        print("-" * 20)
        
        token_address = input("Enter token address: ")
        
        if not token_address.startswith('0x') or len(token_address) != 42:
            print("❌ Invalid token address")
            return
        
        print(f"\n🔍 Scanning token: {token_address[:10]}...")
        
        # Get token info
        token_info = self.trading.get_token_info('BSC-TEST', token_address)
        
        if 'error' not in token_info:
            print("✅ Token found!")
            print(f"Name: {token_info.get('name', 'Unknown')}")
            print(f"Symbol: {token_info.get('symbol', 'Unknown')}")
            print(f"Decimals: {token_info.get('decimals', 'Unknown')}")
        else:
            print(f"❌ Error: {token_info['error']}")
    
    def run_demo(self):
        """Run the full demo"""
        print("\n🧪 Running Full Demo...")
        os.system('python simple_test.py')
    
    def run(self):
        """Main bot loop"""
        print("🚀 Starting TG-Fets Trading Bot Simulator...")
        print("This simulator shows all bot functionality without Telegram")
        
        while True:
            self.show_main_menu()
            choice = input("Enter your choice (1-8): ")
            
            if choice == "1":
                self.handle_trading()
            elif choice == "2":
                self.handle_wallet_management()
            elif choice == "3":
                self.check_balance()
            elif choice == "4":
                print("\n💸 Transfer functionality coming soon!")
            elif choice == "5":
                self.token_scanner()
            elif choice == "6":
                print("\n⚙️ Settings functionality coming soon!")
            elif choice == "7":
                self.run_demo()
            elif choice == "8":
                print("\n👋 Goodbye! Thanks for testing the bot!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")

def main():
    """Main function"""
    try:
        bot = BotSimulator()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")

if __name__ == "__main__":
    main()


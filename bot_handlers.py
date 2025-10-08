from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from typing import Dict, Any
import logging
from datetime import datetime

from keyboard_manager import KeyboardManager
from firebase_manager import FirebaseManager
from blockchain_manager import BlockchainManager
from trading_manager import TradingManager
from token_scanner import TokenScanner
from config import TRADING_STATES, TRADING_CONFIG

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PRIVATE_KEY = 1
WAITING_FOR_RECIPIENT = 2
WAITING_FOR_AMOUNT = 3
WAITING_FOR_TOKEN_ADDRESS = 4

class BotHandlers:
    def __init__(self):
        self.firebase = FirebaseManager()
        self.blockchain = BlockchainManager()
        self.trading = TradingManager()
        self.token_scanner = TokenScanner()
        self.keyboard = KeyboardManager()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await self.show_main_menu(update, context)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu"""
        user_id = update.effective_user.id
        
        # Check if user has Twitter authentication
        twitter_info = self.firebase.get_twitter_user_info(user_id)
        twitter_username = None
        if twitter_info and twitter_info.get('isAuthenticated'):
            twitter_username = twitter_info.get('twitterUsername')
        
        text = "🤖 Welcome to TG-Fets Trading Bot!\n\nSelect an option from the menu below:"
        keyboard = self.keyboard.get_main_menu(twitter_username)
        
        if update.callback_query:
            await self.safe_edit_message(
                update.callback_query,
                text=text, 
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(text=text, reply_markup=keyboard)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == "main_menu":
            await self.show_main_menu(update, context)
        elif callback_data == "buy_sell":
            await self.show_buy_sell_menu(update, context)
        elif callback_data in ["buy", "sell"]:
            await self.handle_buy_sell_selection(update, context)
        elif callback_data.startswith("trading_chain_"):
            await self.handle_trading_chain_selection(update, context)
        elif callback_data == "confirm_trade":
            await self.execute_trade(update, context)
        elif callback_data == "cancel_trade":
            await self.cancel_trade(update, context)
        elif callback_data == "wallet":
            await self.show_wallet_menu(update, context)
        elif callback_data == "create_wallet":
            await self.create_wallet(update, context)
        elif callback_data == "import_wallet":
            await self.request_private_key(update, context)
        elif callback_data == "balance":
            await self.show_balance_menu(update, context)
        elif callback_data.startswith("balance_"):
            await self.show_balance_for_chain(update, context)
        elif callback_data == "settings":
            await self.show_settings_menu(update, context)
        elif callback_data == "transfer":
            await self.show_transfer_menu(update, context)
        elif callback_data == "scan_token":
            await self.request_token_address(update, context)
        elif callback_data == "scanner_history":
            await self.show_scanner_history(update, context)
        elif callback_data == "twitter_auth":
            await self.show_twitter_placeholder(update, context)
        elif callback_data == "twitter_auth_complete":
            await self.handle_twitter_auth_complete(update, context)
        elif callback_data.startswith("save_twitter_auth_"):
            await self.save_twitter_auth_data(update, context)
        elif callback_data == "show_private_key":
            await self.show_private_key(update, context)
        elif callback_data == "confirm_show_private_key":
            await self.confirm_show_private_key(update, context)
        elif callback_data == "delete_wallet":
            await self.confirm_delete_wallet(update, context)
        elif callback_data == "confirm_delete_wallet":
            await self.delete_wallet(update, context)
        elif callback_data == "cancel":
            await self.show_main_menu(update, context)
        elif callback_data == "notif_prefs":
            await self.show_notification_preferences(update, context)
        elif callback_data == "toggle_sensitive":
            await self.toggle_sensitive_info(update, context)
        elif callback_data == "transfer_native":
            await self.show_transfer_native(update, context)
        elif callback_data == "transfer_token":
            await self.show_transfer_token(update, context)
        elif callback_data.startswith('quick_amount_'):
            amount = callback_data.replace('quick_amount_', '')
            await self.handle_quick_amount_selection(update, context, amount)
        elif callback_data == 'custom_amount':
            await self.handle_custom_amount_selection(update, context)
        elif callback_data.startswith('edit_slippage_'):
            action = callback_data.replace('edit_slippage_', '')
            await self.handle_edit_slippage(update, context, action)
        elif callback_data.startswith('set_slippage_'):
            slippage = callback_data.replace('set_slippage_', '')
            await self.handle_set_slippage(update, context, slippage)
        elif callback_data.startswith('copy_address_'):
            await self.handle_copy_address(update, context)
        elif callback_data.startswith('refresh_scan_'):
            await self.handle_refresh_scan(update, context)
        elif callback_data.startswith('scanner_chain_'):
            await self.handle_scanner_chain_selection(update, context)
        else:
            await query.edit_message_text("Unknown option selected.")
    
    async def show_buy_sell_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show buy/sell selection menu"""
        text = "Select an action:"
        keyboard = self.keyboard.get_buy_sell_menu()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def handle_buy_sell_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle buy/sell selection and show trading chain menu"""
        action = update.callback_query.data
        context.user_data['trade_action'] = action
        
        text = f"Select chain for {action.lower()} trading:"
        keyboard = self.keyboard.get_trading_chain_selection_menu()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    

    
    async def show_wallet_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show wallet menu based on user's wallet status"""
        user_id = update.effective_user.id
        
        if self.firebase.user_has_wallet(user_id):
            await self.show_wallet_details(update, context)
        else:
            text = "You don't have a wallet saved. Choose an option:"
            keyboard = self.keyboard.get_wallet_menu()
            await self.safe_edit_message(
                update.callback_query,
                text=text, 
                reply_markup=keyboard
            )
    
    async def show_wallet_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show wallet details for existing wallet"""
        user_id = update.effective_user.id
        wallet = self.firebase.get_user_wallet(user_id)
        
        text = f"🔐 Wallet Details\n\nPublic Key: `{wallet['public_key']}`\nType: {wallet['type']}\nCreated: {wallet['created_at'][:10]}"
        keyboard = self.keyboard.get_wallet_details_menu()
        
        await self.safe_edit_message(
            update.callback_query,
            text=text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def create_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a new wallet for the user"""
        try:
            user = update.effective_user
            user_id = user.id
            username = user.username or user.first_name
            
            # Generate new wallet
            wallet_data = self.blockchain.create_wallet()
            
            # Save to Firebase
            success = self.firebase.save_user_wallet(
                user_id, username, wallet_data['public_key'], 
                wallet_data['private_key'], "created"
            )
            
            if success:
                text = f"✅ Generated new wallet:\n\n"
                text += f"Address: {wallet_data['public_key']}\n"
                text += f"Private Key: {wallet_data['private_key']}\n\n"
                text += f"⚠️ Make sure to save this mnemonic phrase OR private key using pen and paper only. Do NOT copy-paste it anywhere. You could also import it to your Metamask/Trust Wallet. After you finish saving/importing the wallet credentials, delete this message. The bot will not display this information again."
                keyboard = self.keyboard.get_back_button("wallet")
                await update.callback_query.edit_message_text(
                    text=text, 
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                text = "❌ Failed to create wallet. Please try again."
                keyboard = self.keyboard.get_back_button("wallet")
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
                
        except Exception as e:
            logger.error(f"Error creating wallet: {e}")
            text = "❌ An error occurred while creating the wallet. Please try again."
            keyboard = self.keyboard.get_back_button("wallet")
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def request_private_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request private key from user for import"""
        text = "🔑 Please enter your private key:\n\n⚠️ WARNING: Never share your private key with anyone!\n\nEnter the private key :"
        keyboard = self.keyboard.get_cancel_button()
        
        await update.callback_query.edit_message_text(
            text=text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_PRIVATE_KEY
    
    async def handle_private_key_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle private key input and import wallet"""
        private_key = update.message.text.strip()
        user = update.effective_user
        user_id = user.id
        username = user.username or user.first_name
        
        # Debug logging
        logger.info(f"User {user_id} attempting to import wallet with private key: {private_key[:10]}...")
        
        # Validate private key and get public address
        public_key = self.blockchain.validate_private_key(private_key)
        
        if not public_key:
            logger.warning(f"Private key validation failed for user {user_id}")
            text = "❌ Invalid private key format. Please enter a valid 64-character hexadecimal private key."
            keyboard = self.keyboard.get_back_button("wallet")
            await update.message.reply_text(text=text, reply_markup=keyboard)
            return ConversationHandler.END
        
        logger.info(f"Private key validation successful for user {user_id}, public key: {public_key[:10]}...")
        
        # Save to Firebase
        success = self.firebase.save_user_wallet(
            user_id, username, public_key, private_key, "imported"
        )
        
        if success:
            text = f"✅ Wallet imported successfully:\n\n"
            text += f"Address: {public_key}\n"
            text += f"Private Key: {private_key}\n\n"
            text += f"⚠️ Make sure to save this mnemonic phrase OR private key using pen and paper only. Do NOT copy-paste it anywhere. You could also import it to your Metamask/Trust Wallet. After you finish saving/importing the wallet credentials, delete this message. "
            keyboard = self.keyboard.get_back_button("wallet")
            await update.message.reply_text(
                text=text, 
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Wallet imported successfully for user {user_id}")
        else:
            text = "❌ Failed to import wallet. Please try again."
            keyboard = self.keyboard.get_back_button("wallet")
            await update.message.reply_text(text=text, reply_markup=keyboard)
            logger.error(f"Failed to import wallet for user {user_id}")
        
        return ConversationHandler.END
    
    async def show_balance_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show balance menu with chain selection"""
        text = "Select chain to check balance:"
        keyboard = self.keyboard.get_chain_selection_menu("balance")
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def show_balance_for_chain(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show balance for selected chain"""
        query = update.callback_query
        chain = query.data.split('_', 1)[1]
        user_id = update.effective_user.id
        
        if not self.firebase.user_has_wallet(user_id):
            text = "You don't have a wallet saved. Please create or import a wallet first."
            keyboard = self.keyboard.get_wallet_menu()
            await query.edit_message_text(text=text, reply_markup=keyboard)
            return
        
        wallet = self.firebase.get_user_wallet(user_id)
        balance = self.blockchain.get_balance(chain, wallet['public_key'])
        
        if balance is not None:
            text = f"💰 Balance on {chain}\n\nAddress: `{wallet['public_key']}`\nBalance: {balance:.6f} {'ETH' if chain == 'ETH' else 'BNB'}"
        else:
            text = f"❌ Could not fetch balance for {chain}. Please check your connection and try again."
        
        keyboard = self.keyboard.get_back_button("balance")
        await query.edit_message_text(
            text=text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show settings menu"""
        text = "⚙️ Settings\n\nConfigure your bot preferences:"
        keyboard = self.keyboard.get_settings_menu()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def show_transfer_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show transfer menu"""
        text = "💸 Transfer\n\nSelect transfer type:"
        keyboard = self.keyboard.get_transfer_menu()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def request_token_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request token address for scanning"""
        text = "🔍 Token Scanner\n\nSelect chain and enter the token contract address to scan:"
        keyboard = self.keyboard.get_scanner_chain_selection_menu()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def handle_scanner_chain_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle scanner chain selection"""
        query = update.callback_query
        chain = query.data.replace('scanner_chain_', '')
        context.user_data['scanner_chain'] = chain
        
        text = f"🔍 Token Scanner - {chain}\n\nEnter the token contract address to scan:"
        keyboard = self.keyboard.get_cancel_button()
        await query.edit_message_text(text=text, reply_markup=keyboard)
        return WAITING_FOR_TOKEN_ADDRESS
    
    async def handle_token_address_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle token address input and perform token scan"""
        token_address = update.message.text.strip()
        chain = context.user_data.get('scanner_chain', 'BSC')
        
        # Basic validation (simple format check)
        if not token_address.startswith('0x') or len(token_address) != 42:
            text = "❌ Invalid token address format. Please enter a valid Ethereum/BSC address."
            keyboard = self.keyboard.get_back_button("scan_token")
            await update.message.reply_text(text=text, reply_markup=keyboard)
            return ConversationHandler.END
        
        # Show scanning message
        scanning_msg = await update.message.reply_text(
            "🔍 Scanning token...",
            reply_markup=self.keyboard.get_cancel_button()
        )
        
        try:
            # Perform token scan
            scan_result = await self.token_scanner.scan_token(token_address, chain)
            
            if scan_result and "error" not in scan_result:
                # Store scan result in context for refresh functionality
                context.user_data['last_scan_result'] = scan_result
                context.user_data['last_token_address'] = token_address
                context.user_data['last_scan_chain'] = chain
                
                # Format and display result
                formatted_result = self.token_scanner.format_scan_result(scan_result)
                keyboard = self.keyboard.get_scanner_result_menu(token_address)
                
                await scanning_msg.edit_text(
                    text=formatted_result,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Show error message
                error_msg = scan_result.get('error', 'Unknown error occurred') if scan_result else 'No data received'
                text = f"❌ Token Scan Failed\n\nError: {error_msg}\n\nPlease try again with a valid token address."
                keyboard = self.keyboard.get_scanner_result_menu(token_address)
                
                await scanning_msg.edit_text(
                    text=text,
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error scanning token: {e}")
            text = f"❌ Token Scan Error\n\nAn unexpected error occurred: {str(e)}\n\nPlease try again."
            keyboard = self.keyboard.get_scanner_result_menu(token_address)
            
            await scanning_msg.edit_text(
                text=text,
                reply_markup=keyboard
            )
        
        return ConversationHandler.END
    
    async def handle_copy_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle copy address button click"""
        query = update.callback_query
        await query.answer()
        
        # Extract token address from callback data
        callback_data = query.data
        token_address = callback_data.replace('copy_address_', '')
        
        if token_address:
            # Copy address to clipboard (in a real implementation, this would copy to system clipboard)
            # For Telegram, we'll just show the address in a message
            text = f"📋 Token Address\n\n`{token_address}`\n\n✅ Address copied to message above. You can copy it manually."
            keyboard = self.keyboard.get_back_button("scan_token")
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(
                "❌ No token address found to copy.",
                reply_markup=self.keyboard.get_back_button("scan_token")
            )
    
    async def handle_refresh_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle refresh scan button click"""
        query = update.callback_query
        await query.answer()
        
        # Get stored scan data from context
        token_address = context.user_data.get('last_token_address')
        chain = context.user_data.get('last_scan_chain', 'BSC')
        
        if not token_address:
            await query.edit_message_text(
                "❌ No previous scan found to refresh. Please scan a token first.",
                reply_markup=self.keyboard.get_back_button("scan_token")
            )
            return
        
        # Show refreshing message
        await query.edit_message_text(
            "🔄 Refreshing token data...",
            reply_markup=self.keyboard.get_cancel_button()
        )
        
        try:
            # Perform fresh token scan
            scan_result = await self.token_scanner.scan_token(token_address, chain)
            
            if scan_result and "error" not in scan_result:
                # Update stored scan result
                context.user_data['last_scan_result'] = scan_result
                
                # Format and display refreshed result
                formatted_result = self.token_scanner.format_scan_result(scan_result)
                keyboard = self.keyboard.get_scanner_result_menu(token_address)
                
                await query.edit_message_text(
                    text=formatted_result,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Show error message
                error_msg = scan_result.get('error', 'Unknown error occurred') if scan_result else 'No data received'
                text = f"❌ Refresh Failed\n\nError: {error_msg}\n\nPlease try again."
                keyboard = self.keyboard.get_scanner_result_menu(token_address)
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error refreshing token scan: {e}")
            text = f"❌ Refresh Error\n\nAn unexpected error occurred: {str(e)}\n\nPlease try again."
            keyboard = self.keyboard.get_scanner_result_menu(token_address)
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard
            )
    
    async def show_scanner_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show scanner history (placeholder)"""
        text = "📋 Scanner History\n\nNo scan history available yet.\n\nThis feature will be implemented in future updates."
        keyboard = self.keyboard.get_back_button()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    

    
    async def confirm_show_private_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show private key after confirmation"""
        user_id = update.effective_user.id
        wallet = self.firebase.get_user_wallet(user_id)
        
        if wallet:
            private_key = self.firebase.get_private_key(user_id)
            if private_key:
                text = f"🔑 PRIVATE KEY\n\n⚠️ SECURITY WARNING: This is extremely sensitive information!\n\nPrivate Key: `{private_key}`\n\n💡 Tip: Copy this key and delete this message immediately. Never share it with anyone!"
                keyboard = self.keyboard.get_back_button("wallet")
                await update.callback_query.edit_message_text(
                    text=text, 
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                text = "❌ Could not retrieve private key. Please try again."
                keyboard = self.keyboard.get_back_button("wallet")
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        else:
            text = "❌ No wallet found."
            keyboard = self.keyboard.get_back_button("wallet")
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def show_notification_preferences(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show notification preferences"""
        text = "🔔 Notification Preferences\n\nConfigure how you want to receive notifications:"
        keyboard = self.keyboard.get_back_button("settings")
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def toggle_sensitive_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle sensitive information display"""
        text = "👁️ Show/Hide Sensitive Info\n\nThis feature will be implemented in future updates."
        keyboard = self.keyboard.get_back_button("settings")
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def show_transfer_native(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show native token transfer interface"""
        text = "💸 Native Token Transfer\n\nThis feature will be implemented in future updates."
        keyboard = self.keyboard.get_back_button("transfer")
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def show_transfer_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show token transfer interface"""
        text = "🪙 Token Transfer\n\nThis feature will be implemented in future updates."
        keyboard = self.keyboard.get_back_button("transfer")
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def show_twitter_placeholder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Twitter authentication flow"""
        user_id = update.effective_user.id
        
        # Check if user is already authenticated
        twitter_info = self.firebase.get_twitter_user_info(user_id)
        
        if twitter_info and twitter_info.get('isAuthenticated'):
            # User is already authenticated
            username = twitter_info.get('twitterUsername', 'Unknown')
            text = f"🐦 Twitter Connected Successfully!\n\n"
            text += f"✅ Username: @{username}\n"
            text += f"🔗 Status: Authenticated\n"
            
            keyboard = self.keyboard.get_back_button()
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        else:
            # Show authentication flow
            auth_url = f"https://twitter-auth-frontend.vercel.app/?user={user_id}"
            
            text = "🐦 Twitter Authentication\n\n"
        
            text += "📱 Authentication Process:\n"
            text += "1. Click the link below to authenticate\n"
            text += "2. Complete Twitter OAuth process\n"
            text += "3. Return here and click 'Complete'\n\n"
            text += f"🔗 Authentication Link:\n`{auth_url}`\n\n"
            text += "After completing authentication on Twitter, click the Complete button below."
            
            keyboard = self.keyboard.get_twitter_auth_keyboard()
            await update.callback_query.edit_message_text(
                text=text, 
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_twitter_auth_complete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Twitter authentication completion"""
        user_id = update.effective_user.id
        
        # Check if user has Twitter authentication data
        twitter_auth = self.firebase.check_twitter_auth(user_id)
        
        if twitter_auth:
            # User is authenticated
            username = twitter_auth.get('twitterUsername', 'Unknown')
            text = f"✅ Twitter Authentication Successful!\n\n"
            text += f"🐦 Username: @{username}\n"
            text += f"🔗 Status: Connected\n"
            
            keyboard = self.keyboard.get_back_button()
            await update.callback_query.edit_message_text(
                text=text, 
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # No authentication data found
            text = "❌ Twitter Authentication Not Found\n\n"
            text += "It seems like you haven't completed the Twitter authentication process yet.\n\n"
            text += "Please:\n"
            text += "1. Click the authentication link\n"
            text += "2. Complete the Twitter OAuth process\n"
            text += "3. Return here and click 'Complete' again\n\n"
            text += "If you're having issues, please try the authentication process again."
            
            keyboard = self.keyboard.get_back_button("twitter_auth")
            await update.callback_query.edit_message_text(
                text=text, 
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def save_twitter_auth_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save Twitter authentication data from frontend"""
        user_id = update.effective_user.id
        callback_data = update.callback_query.data
        
        # Extract auth data from callback data
        # Format: save_twitter_auth_accessToken_refreshToken_twitterId_twitterUsername_createdAt_expiresAt
        try:
            parts = callback_data.split('_')[2:]  # Remove 'save_twitter_auth' prefix
            
            if len(parts) >= 6:
                access_token = parts[0]
                refresh_token = parts[1]
                twitter_id = parts[2]
                twitter_username = parts[3]
                created_at = int(parts[4])
                expires_at = int(parts[5])
                
                # Prepare auth data
                auth_data = {
                    'accessToken': access_token,
                    'refreshToken': refresh_token,
                    'twitterId': twitter_id,
                    'twitterUsername': twitter_username,
                    'createdAt': created_at,
                    'expiresAt': expires_at
                }
                
                # Save to Firebase
                success = self.firebase.save_twitter_auth(user_id, auth_data)
                
                if success:
                    text = f"✅ Twitter Authentication Successfully!\n\n"
                    text += f"🐦 Username: @{twitter_username}\n"
                    text += f"🔗 Status: Connected\n\n"
                    text += f"Your Twitter account is now connected to the bot!"
                    
                    keyboard = self.keyboard.get_back_button()
                    await update.callback_query.edit_message_text(
                        text=text, 
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    text = "❌ Failed to Save Twitter Authentication\n\n"
                    text += "There was an error saving your Twitter authentication data.\n\n"
                    text += "Please try again or contact support if the issue persists."
                    
                    keyboard = self.keyboard.get_back_button("twitter_auth")
                    await update.callback_query.edit_message_text(
                        text=text, 
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                text = "❌ Invalid Authentication Data\n\n"
                text += "The authentication data received is incomplete.\n\n"
                text += "Please try the authentication process again."
                
                keyboard = self.keyboard.get_back_button("twitter_auth")
                await update.callback_query.edit_message_text(
                    text=text, 
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error saving Twitter auth data: {e}")
            text = "❌ Error Saving Authentication\n\n"
            text += "There was an error processing your Twitter authentication.\n\n"
            text += "Please try again or contact support if the issue persists."
            
            keyboard = self.keyboard.get_back_button("twitter_auth")
            await update.callback_query.edit_message_text(
                text=text, 
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def show_private_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show private key with confirmation"""
        text = "⚠️ SECURITY WARNING\n\nAre you sure you want to view your private key?\n\nThis is extremely sensitive information that gives full access to your wallet!"
        keyboard = self.keyboard.get_confirm_menu("show_private_key")
        await update.callback_query.edit_message_text(
            text=text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def confirm_delete_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm wallet deletion"""
        text = "🗑️ DANGER ZONE\n\nAre you sure you want to delete your wallet?\n\n⚠️ This action cannot be undone and you will lose access to your funds if you don't have a backup!"
        keyboard = self.keyboard.get_confirm_menu("delete_wallet")
        await update.callback_query.edit_message_text(
            text=text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def delete_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete user's wallet"""
        user_id = update.effective_user.id
        
        if self.firebase.delete_user_wallet(user_id):
            text = "✅ Wallet deleted successfully.\n\nYou can create a new wallet or import an existing one from the Wallet menu."
            keyboard = self.keyboard.get_back_button()
        else:
            text = "❌ Failed to delete wallet. Please try again."
            keyboard = self.keyboard.get_back_button()
        
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current conversation"""
        await self.show_main_menu(update, context)
        return ConversationHandler.END
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors gracefully"""
        try:
            if update and update.callback_query:
                # For callback queries, just answer them to remove the loading state
                await update.callback_query.answer()
            logger.error(f"Exception while handling an update: {context.error}")
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    async def safe_edit_message(self, callback_query, text: str, reply_markup=None, parse_mode=None):
        """Safely edit message with error handling"""
        try:
            await callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            if "Message is not modified" in str(e):
                # Message is already the same, just answer the callback
                await callback_query.answer()
            else:
                # Other error, log it and answer callback
                logger.warning(f"Message edit failed: {e}")
                await callback_query.answer()

    # Trading Methods
    async def handle_trading_chain_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle trading chain selection and check wallet"""
        query = update.callback_query
        chain = query.data.replace('trading_chain_', '')
        
        user_id = update.effective_user.id
        
        if not self.firebase.user_has_wallet(user_id):
            text = "❌ You don't have a wallet saved. Please create or import a wallet first."
            keyboard = self.keyboard.get_wallet_menu()
            await query.edit_message_text(text=text, reply_markup=keyboard)
            return
        
        if not self.trading.validate_trading_chain(chain):
            text = f"❌ Trading is not enabled for {chain}."
            keyboard = self.keyboard.get_back_button("buy_sell")
            await query.edit_message_text(text=text, reply_markup=keyboard)
            return
        
        # Store chain in context
        context.user_data['trade_chain'] = chain
        
        # Get wallet balance
        wallet = self.firebase.get_user_wallet(user_id)
        balance = self.blockchain.get_balance(chain, wallet['public_key'])
        
        if balance is None:
            balance = 0.0
        
        # Store wallet info in context
        context.user_data['wallet_address'] = wallet['public_key']
        context.user_data['wallet_balance'] = balance
        
        action = context.user_data.get('trade_action', 'trade')
        
        if action == 'buy':
            text = f"💰 Buy Tokens with BNB\n\nChain: {chain}\nWallet: `{wallet['public_key'][:10]}...`\nBNB Balance: {balance:.6f} BNB\n\nEnter the amount of BNB you want to spend:"
        else:  # sell
            text = f"💰 Sell Tokens for BNB\n\nChain: {chain}\nWallet: `{wallet['public_key'][:10]}...`\n\nEnter the token amount you want to sell:"
        
        keyboard = self.keyboard.get_cancel_button()
        await query.edit_message_text(
            text=text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Set conversation state
        context.user_data['waiting_for'] = 'amount'
        return TRADING_STATES['WAITING_FOR_AMOUNT']
    
    async def request_trade_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request trade amount from user"""
        try:
            amount_text = update.message.text.strip()
            amount = float(amount_text)
            
            if amount <= 0:
                await update.message.reply_text(
                    "❌ Amount must be greater than 0. Please try again:",
                    reply_markup=self.keyboard.get_cancel_button()
                )
                return TRADING_STATES['WAITING_FOR_AMOUNT']
            
            chain = context.user_data.get('trade_chain')
            action = context.user_data.get('trade_action')
            balance = context.user_data.get('wallet_balance', 0)
            
            # Validate amount
            limits = self.trading.get_trading_limits(chain)
            if action == 'buy' and amount > balance:
                await update.message.reply_text(
                    f"❌ Insufficient BNB balance. You have {balance:.6f} BNB, but trying to spend {amount:.6f} BNB.",
                    reply_markup=self.keyboard.get_cancel_button()
                )
                return TRADING_STATES['WAITING_FOR_AMOUNT']
            
            if amount < limits.get('min_amount', 0.001):
                await update.message.reply_text(
                    f"❌ Amount too small. Minimum amount is {limits.get('min_amount', 0.001)} BNB.",
                    reply_markup=self.keyboard.get_cancel_button()
                )
                return TRADING_STATES['WAITING_FOR_AMOUNT']
            
            if amount > limits.get('max_amount', 10.0):
                await update.message.reply_text(
                    f"❌ Amount too large. Maximum amount is {limits.get('max_amount', 10.0)} BNB.",
                    reply_markup=self.keyboard.get_cancel_button()
                )
                return TRADING_STATES['WAITING_FOR_AMOUNT']
            
            # Store amount in context
            context.user_data['trade_amount'] = amount
            
            # Request token address
            if action == 'buy':
                text = f"🔍 Enter Token Address\n\nAmount: {amount:.6f} BNB\n\nEnter the token contract address you want to buy:"
            else:  # sell
                text = f"🔍 Enter Token Address\n\nAmount: {amount:.6f} tokens\n\nEnter the token contract address you want to sell:"
            
            keyboard = self.keyboard.get_cancel_button()
            await update.message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            context.user_data['waiting_for'] = 'token_address'
            return TRADING_STATES['WAITING_FOR_TOKEN_ADDRESS']
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a valid number:",
                reply_markup=self.keyboard.get_cancel_button()
            )
            return TRADING_STATES['WAITING_FOR_AMOUNT']
    
    async def request_token_address_for_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request token address and show trade summary"""
        try:
            token_address = update.message.text.strip()
            
            # Validate token address format
            if not token_address.startswith('0x') or len(token_address) != 42:
                await update.message.reply_text(
                    "❌ Invalid token address format. Please enter a valid Ethereum address:",
                    reply_markup=self.keyboard.get_cancel_button()
                )
                return TRADING_STATES['WAITING_FOR_TOKEN_ADDRESS']
            
            chain = context.user_data.get('trade_chain')
            action = context.user_data.get('trade_action')
            
            # Store token address in context
            context.user_data['token_address'] = token_address
            
            # Get detailed token information using scanner
            try:
                scan_result = await self.token_scanner.scan_token(token_address, chain)
                
                if scan_result and "error" not in scan_result:
                    # Format token information similar to the example you provided
                    token_name = scan_result.get('token_name', 'Unknown')
                    token_symbol = scan_result.get('token_symbol', 'Unknown')
                    price_usd = scan_result.get('price_usd', 0) or 0
                    price_change_24h = scan_result.get('price_change_24h', 0) or 0
                    liquidity_usd = scan_result.get('liquidity_usd', 0) or 0
                    volume_24h = scan_result.get('volume_24h', 0) or 0
                    fdv = scan_result.get('fdv', 0) or 0
                    transactions_24h = scan_result.get('transactions_24h', {'buys': 0, 'sells': 0})
                    
                    # Format price change - handle both percentage and decimal formats
                    if price_change_24h is not None:
                        # Check if the value is already a percentage (e.g., 5.5 for 5.5%)
                        # or a decimal (e.g., 0.055 for 5.5%)
                        if abs(price_change_24h) > 1:
                            # Already a percentage, format directly
                            if price_change_24h > 0:
                                price_change_str = f"📈 +{price_change_24h:.2f}%"
                            else:
                                price_change_str = f"📉 {price_change_24h:.2f}%"
                        else:
                            # It's a decimal, convert to percentage
                            if price_change_24h > 0:
                                price_change_str = f"📈 +{price_change_24h:.2%}"
                            else:
                                price_change_str = f"📉 {price_change_24h:.2%}"
                    else:
                        price_change_str = "➡️ 0.00%"
                    
                    # Format prices
                    if price_usd and price_usd < 0.000001:
                        price_usd_str = f"${price_usd:.12f}"
                    elif price_usd and price_usd < 0.01:
                        price_usd_str = f"${price_usd:.8f}"
                    elif price_usd and price_usd < 1:
                        price_usd_str = f"${price_usd:.6f}"
                    elif price_usd:
                        price_usd_str = f"${price_usd:.4f}"
                    else:
                        price_usd_str = "$0.0000"
                    
                    # Get actual wallet balance
                    user_id = update.effective_user.id
                    wallet_balance = 0
                    native_balance = 0
                    
                    try:
                        # Get wallet address
                        wallet_data = self.firebase.get_user_wallet(user_id)
                        if wallet_data:
                            wallet_address = wallet_data['public_key']
                            
                            # Get token balance
                            token_balance_data = self.trading.get_token_balance(chain, wallet_address, token_address)
                            if token_balance_data and 'error' not in token_balance_data:
                                wallet_balance = token_balance_data.get('balance', 0)
                            
                            # Get native balance (BNB/ETH)
                            native_balance_data = self.blockchain.get_balance(chain, wallet_address)
                            if native_balance_data is not None:
                                native_balance = native_balance_data
                    except Exception as e:
                        logger.error(f"Error getting wallet balance: {e}")
                    
                    # Build detailed token information
                    text = f"🪙 {token_name} (${token_symbol})\n"
                    text += f"{token_address}\n"
                    text += f"V2 Pool 🔗 {chain}\n\n"
                    
                    text += f"⛽ {chain} | 0.1 GWEI  Ξ $0.0₆1\n\n"
                    
                    text += f"🧢 MC ${fdv:,.0f} | 💵 Price {price_usd_str}\n"
                    text += f"⚖️ Taxes | 🅑 0.0% 🅢 0.0% 🅣 0.0%\n"
                    liquidity_percentage = (liquidity_usd/fdv*100) if fdv and fdv > 0 else 0
                    text += f"💧 Liquidity | ${liquidity_usd:,.0f} ({liquidity_percentage:.2f}%)\n"
                    text += f"🕓 Refresh | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    
                    text += f"💰 Balance\n"
                    text += f" {token_symbol}   | {chain}\n"
                    text += f" {wallet_balance:.6f} | {native_balance:.6f}\n\n"
                    
                    if fdv and fdv > 0 and liquidity_usd/fdv < 0.01:
                        text += f"🚨 Liquidity / Total Supply < 1%\n\n"
                    
                    if action == 'buy':
                        text += f"Enter Amount ({chain}):"
                        
                        # Create quick amount buttons for buy action
                        keyboard = self._create_amount_selection_keyboard(chain, action, user_id)
                    else:  # sell
                        text += f"Enter Amount ({token_symbol}):"
                        keyboard = self._create_amount_selection_keyboard(chain, action, user_id)
                        
                    await update.message.reply_text(
                        text=text,
                        reply_markup=keyboard
                    )
                    return TRADING_STATES['WAITING_FOR_AMOUNT']
                    
                else:
                    # Fallback to simple format if scanning fails
                    text = f"✅ Token Address Valid!\n\n"
                    text += f"🔑 Token: `{token_address[:20]}...`\n"
                    text += f"🌐 Network: {chain}\n\n"
                    
                    if action == 'buy':
                        text += f"💰 Enter the amount of {chain} to spend\n\n"
                        text += f"💡 Example: 0.1, 0.5, 1.0\n\n"
                        text += f"🔧 Just type the amount below:"
                        
                        # Create quick amount buttons for buy action (fallback)
                        keyboard = self._create_amount_selection_keyboard(chain, action, user_id)
                    else:  # sell
                        text += f"💰 Enter the amount of tokens to sell\n\n"
                        text += f"💡 Example: 100, 1000, 5000\n\n"
                        text += f"🔧 Just type the amount below:"
                        keyboard = self._create_amount_selection_keyboard(chain, action, user_id)
                        
                    await update.message.reply_text(
                        text=text,
                        reply_markup=keyboard
                    )
                    return TRADING_STATES['WAITING_FOR_AMOUNT']
                    
            except Exception as e:
                logger.error(f"Error scanning token: {e}")
                # Fallback to simple format
                text = f"✅ Token Address Valid!\n\n"
                text += f"🔑 Token: `{token_address[:20]}...`\n"
                text += f"🌐 Network: {chain}\n\n"
                
                if action == 'buy':
                    text += f"💰 Enter the amount of {chain} to spend\n\n"
                    text += f"💡 Example: 0.1, 0.5, 1.0\n\n"
                    text += f"🔧 Just type the amount below:"
                    
                    # Create quick amount buttons for buy action (exception fallback)
                    keyboard = self._create_amount_selection_keyboard(chain, action, user_id)
                else:  # sell
                    text += f"💰 Enter the amount of tokens to sell\n\n"
                    text += f"💡 Example: 100, 1000, 5000\n\n"
                    text += f"🔧 Just type the amount below:"
                    keyboard = self._create_amount_selection_keyboard(chain, action, user_id)
                    
                await update.message.reply_text(
                    text=text,
                    reply_markup=keyboard
                )
                return TRADING_STATES['WAITING_FOR_AMOUNT']
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error processing token address: {str(e)}",
                reply_markup=self.keyboard.get_cancel_button()
            )
            return TRADING_STATES['WAITING_FOR_TOKEN_ADDRESS']
    
    async def show_trade_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trade summary and ask for confirmation"""
        action = context.user_data.get('trade_action')
        chain = context.user_data.get('trade_chain')
        amount = context.user_data.get('trade_amount')
        token_info = context.user_data.get('token_info', {})
        swap_info = context.user_data.get('swap_info', {})
        
        if action == 'buy':
            text = f"📋 Trade Summary - BUY\n\n"
            text += f"🔗 Chain: {chain}\n"
            text += f"💰 Amount: {amount:.6f} BNB\n"
            text += f"🪙 Token: {token_info.get('name', 'Unknown')} ({token_info.get('symbol', 'Unknown')})\n"
            text += f"📍 Token Address: `{token_info.get('address', '')[:10]}...`\n"
            text += f"💸 Fee: {swap_info.get('fee_bnb', 0):.6f} BNB\n"
            text += f"📊 Estimated Output: {swap_info.get('estimated_output', 0):.6f} tokens\n"
            text += f"⚡ Slippage: {swap_info.get('slippage', 0.5)}%\n\n"
            text += f"⚠️ Please review the details above carefully before confirming."
        else:  # sell
            text = f"📋 Trade Summary - SELL\n\n"
            text += f"🔗 Chain: {chain}\n"
            text += f"🪙 Amount: {amount:.6f} {token_info.get('symbol', 'tokens')}\n"
            text += f"🪙 Token: {token_info.get('name', 'Unknown')} ({token_info.get('symbol', 'Unknown')})\n"
            text += f"📍 Token Address: `{token_info.get('address', '')[:10]}...`\n"
            text += f"💸 Fee: {swap_info.get('fee_bnb', 0):.6f} BNB\n"
            text += f"💰 Estimated Output: {swap_info.get('estimated_output', 0):.6f} BNB\n"
            text += f"⚡ Slippage: {swap_info.get('slippage', 0.5)}%\n\n"
            text += f"⚠️ Please review the details above carefully before confirming."
        
        keyboard = self.keyboard.get_trade_confirmation_menu()
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def execute_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute the confirmed trade"""
        query = update.callback_query
        await query.answer()
        
        try:
            action = context.user_data.get('trade_action')
            chain = context.user_data.get('trade_chain')
            amount = context.user_data.get('trade_amount')
            token_address = context.user_data.get('token_address')
            wallet_address = context.user_data.get('wallet_address')
            
            # Get private key
            user_id = update.effective_user.id
            private_key = self.firebase.get_private_key(user_id)
            
            if not private_key:
                text = "❌ Could not retrieve private key. Please try again."
                keyboard = self.keyboard.get_back_button("main_menu")
                await query.edit_message_text(text=text, reply_markup=keyboard)
                return
            
            # Add 0x prefix if not present
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            # Show processing message
            await query.edit_message_text(
                "⏳ Processing your trade...\n\nThis may take a few moments.",
                reply_markup=None
            )
            
            # Execute trade
            if action == 'buy':
                result = self.trading.execute_buy_trade(
                    chain, wallet_address, private_key, amount, token_address
                )
            else:  # sell
                result = self.trading.execute_sell_trade(
                    chain, wallet_address, private_key, token_address, amount
                )
            
            if 'error' in result:
                text = f"❌ Trade Failed\n\nError: {result['error']}\n\nPlease try again or contact support."
                keyboard = self.keyboard.get_back_button("main_menu")
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Show success message
            if action == 'buy':
                text = f"✅ Trade Executed Successfully!\n\n"
                text += f"🔗 Chain: {chain}\n"
                text += f"💰 Amount Spent: {amount:.6f} BNB\n"
                text += f"🪙 Tokens Received: {result.get('estimated_output', 0):.6f}\n"
                text += f"💸 Fee: {result.get('fee', 0):.6f} BNB\n"
                text += f"📊 Transaction Hash: `{result.get('tx_hash', '')}`\n\n"
                text += f"🎉 Your trade has been completed!"
            else:  # sell
                text = f"✅ Trade Executed Successfully!\n\n"
                text += f"🔗 Chain: {chain}\n"
                text += f"🪙 Tokens Sold: {amount:.6f}\n"
                # text += f"💰 BNB Received: {result.get('estimated_output', 0):.6f} BNB\n"
                text += f"💸 Fee: {result.get('fee', 0):.6f} BNB\n"
                text += f"📊 Transaction Hash: `{result.get('tx_hash', '')}`\n\n"
                text += f"🎉 Your trade has been completed!"
            
            keyboard = self.keyboard.get_back_button("main_menu")
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Clear context
            context.user_data.clear()
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            text = f"❌ Trade Failed\n\nAn unexpected error occurred: {str(e)}\n\nPlease try again or contact support."
            keyboard = self.keyboard.get_back_button("main_menu")
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def cancel_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the current trade"""
        query = update.callback_query
        await query.answer()
        
        # Clear context
        context.user_data.clear()
        
        text = "❌ Trade cancelled. Returning to main menu."
        keyboard = self.keyboard.get_main_menu()
        await query.edit_message_text(text=text, reply_markup=keyboard)

    def _create_amount_selection_keyboard(self, native_symbol, action, user_id):
        """Create keyboard with quick amount buttons for buy actions"""
        # Use slippage from settings, with user preference as fallback
        current_slippage = TRADING_CONFIG.get('BSC', {}).get('slippage', 0.5)
        if hasattr(self, 'get_user_slippage') and user_id:
            current_slippage = self.get_user_slippage(user_id)
        
        keyboard = [
            [
                InlineKeyboardButton(f"0.01 {native_symbol}", callback_data="quick_amount_0.01"),
                InlineKeyboardButton(f"0.05 {native_symbol}", callback_data="quick_amount_0.05"),
                InlineKeyboardButton(f"0.1 {native_symbol}", callback_data="quick_amount_0.1")
            ],
            [
                InlineKeyboardButton(f"0.5 {native_symbol}", callback_data="quick_amount_0.5"),
                InlineKeyboardButton(f"1 {native_symbol}", callback_data="quick_amount_1"),
                InlineKeyboardButton(f"Buy X {native_symbol}", callback_data="custom_amount")
            ],
            [
                InlineKeyboardButton(f"Slippage | {current_slippage}%", callback_data=f"edit_slippage_{action}")
            ],
            [
                InlineKeyboardButton('🔙 Back to Trading', callback_data='buy_sell')
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _create_back_button_keyboard(self):
        """Create simple keyboard with back button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton('🔙 Back to Trading', callback_data='buy_sell')]
        ])

    async def handle_quick_amount_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount: str):
        """Handle quick amount button selection"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Store the selected amount in user data
            context.user_data['trade_amount'] = amount
            
            # Get current trading state
            action = context.user_data.get('trade_action', 'buy')
            token_address = context.user_data.get('token_address')
            chain = context.user_data.get('selected_chain', 'BSC')
            
            if not token_address:
                await query.edit_message_text("❌ No token address found. Please start over.")
                return
            
            # Show confirmation with amount
            text = f"✅ Amount Selected: {amount} {chain}\n\n"
            text += f"🔑 Token: `{token_address[:20]}...`\n"
            text += f"🌐 Network: {chain}\n"
            text += f"💰 Amount: {amount} {chain}\n\n"
            
            if action == 'buy':
                text += f"🔄 Ready to buy tokens with {amount} {chain}"
            else:
                text += f"🔄 Ready to sell {amount} tokens"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('✅ Confirm Trade', callback_data='confirm_trade'),
                    InlineKeyboardButton('❌ Cancel', callback_data='cancel_trade')
                ]
            ])
            
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error handling quick amount selection: {e}")
            await query.edit_message_text(f"❌ Error processing amount: {str(e)}")

    async def handle_custom_amount_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom amount button selection"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Get current trading state
            action = context.user_data.get('trade_action', 'buy')
            chain = context.user_data.get('selected_chain', 'BSC')
            
            text = f"💰 Enter Custom Amount\n\n"
            text += f"🌐 Network: {chain}\n"
            text += f"💡 Example: 0.1, 0.5, 1.0, 2.5\n\n"
            text += f"🔧 Type the amount of {chain} you want to spend:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('🔙 Back to Amount Selection', callback_data='buy_sell')
                ]
            ])
            
            await query.edit_message_text(text=text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error handling custom amount selection: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def handle_edit_slippage(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        """Handle slippage editing"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Get current slippage from settings
            chain = context.user_data.get('trade_chain', 'BSC')
            current_slippage = TRADING_CONFIG.get(chain, {}).get('slippage', 0.5)
            if hasattr(self, 'get_user_slippage'):
                current_slippage = self.get_user_slippage(update.effective_user.id)
            
            text = f"⚙️ Slippage Settings\n\n"
            text += f"Current Slippage: {current_slippage}%\n\n"
            text += f"💡 Slippage tolerance allows for price movement during trade execution.\n"
            text += f"Higher slippage = faster execution but potentially worse price.\n\n"
            text += f"🔧 Enter new slippage percentage (0.1 - 50):"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('0.5%', callback_data='set_slippage_0.5'),
                    InlineKeyboardButton('1%', callback_data='set_slippage_1'),
                    InlineKeyboardButton('2%', callback_data='set_slippage_2')
                ],
                [
                    InlineKeyboardButton('5%', callback_data='set_slippage_5'),
                    InlineKeyboardButton('10%', callback_data='set_slippage_10'),
                    InlineKeyboardButton('Custom', callback_data='set_slippage_custom')
                ],
                [
                    InlineKeyboardButton('🔙 Back to Trading', callback_data='buy_sell')
                ]
            ])
            
            await query.edit_message_text(text=text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error handling slippage edit: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def handle_set_slippage(self, update: Update, context: ContextTypes.DEFAULT_TYPE, slippage: str):
        """Handle slippage setting"""
        query = update.callback_query
        await query.answer()
        
        try:
            if slippage == 'custom':
                text = f"🔧 Enter Custom Slippage\n\n"
                text += f"💡 Enter slippage percentage (0.1 - 50):"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton('🔙 Back to Slippage Settings', callback_data='edit_slippage_buy')]
                ])
                
                await query.edit_message_text(text=text, reply_markup=keyboard)
                return
            
            # Parse and validate slippage
            try:
                slippage_value = float(slippage)
                if slippage_value < 0.1 or slippage_value > 50:
                    await query.edit_message_text("❌ Slippage must be between 0.1% and 50%")
                    return
            except ValueError:
                await query.edit_message_text("❌ Invalid slippage value")
                return
            
            # Save slippage setting (if method exists)
            if hasattr(self, 'set_user_slippage'):
                self.set_user_slippage(update.effective_user.id, slippage_value)
            
            text = f"✅ Slippage Updated!\n\n"
            text += f"New Slippage: {slippage_value}%\n\n"
            text += f"🔄 Returning to trading..."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton('🔙 Back to Trading', callback_data='buy_sell')]
            ])
            
            await query.edit_message_text(text=text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error setting slippage: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")

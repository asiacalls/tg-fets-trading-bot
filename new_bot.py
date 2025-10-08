#!/usr/bin/env python3
"""
New TG-Fets Trading Bot - Clean & Simple Approach
"""

import os
import logging
import asyncio
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from aiohttp import web
from config import TRADING_CONFIG

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset = 0
        self.running = False
        self.user_cache = {}  # Cache to store user names
        
        # X Bot credentials
        self.x_bearer_token = os.getenv('X_BEARER_TOKEN')
        self.x_api_key = os.getenv('X_API_KEY')
        self.x_api_secret = os.getenv('X_API_SECRET')
        self.x_access_token = os.getenv('X_ACCESS_TOKEN')
        self.x_access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        
        # Initialize components
        self.initialize_components()
        
        # Simple trading state
        self.trading_state = {}  # chat_id -> {action: 'buy'|'sell', token: 'address', amount: 'value'}
        
        # Scanner state for refresh functionality
        self.last_scan_results = {}  # chat_id -> {result: scan_result, token_address: address, chain: chain}
        
        # X Bot state
        self.x_bot_running = False
        self.last_processed_tweet_id = None
    
    def initialize_components(self):
        try:
            from firebase_manager import FirebaseManager
            from blockchain_manager import BlockchainManager
            from trading_manager import TradingManager
            from encryption import KeyEncryption
            from token_scanner import TokenScanner
            from positions_manager import PositionsManager
            from transfer_manager import TransferManager
            
            self.firebase = FirebaseManager()
            self.blockchain = BlockchainManager()
            self.trading = TradingManager()
            self.encryption = KeyEncryption()
            self.token_scanner = TokenScanner()
            self.positions_manager = PositionsManager()
            self.transfer_manager = TransferManager()
        
            # Initialize user settings
            self.user_slippage = {}  # Store user slippage preferences
            
            logger.info("✅ All components initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            raise
    
    async def send_message(self, chat_id, text, reply_markup=None):
        import aiohttp
        
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return await response.json()
    
    def create_inline_keyboard(self, buttons):
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                keyboard_row.append({
                    'text': button['text'],
                    'callback_data': button['callback_data']
                })
            keyboard.append(keyboard_row)
        
        return {'inline_keyboard': keyboard}
    
    def get_main_menu(self, twitter_username=None):
        buttons = [
            [
                {'text': f'🐦 @{twitter_username}' if twitter_username else '🐦 Twitter Auth', 'callback_data': 'twitter_auth'}
            ],
            [
                {'text': '🔗 Chains', 'callback_data': 'buy_sell'}
            ],
            [
                {'text': '🔐 Wallet', 'callback_data': 'wallet'}
            ],
            [
                {'text': '💳 Balance', 'callback_data': 'balance'},
                {'text': '🔍 Scanner', 'callback_data': 'scanner'}
            ],
            [
                {'text': '📊 Positions', 'callback_data': 'positions'},
                                {'text': '💸 Transfer', 'callback_data': 'transfer'}

            ],
          
            [
                {'text': '❓ Help', 'callback_data': 'help'},
                {'text': '⚙️ Settings', 'callback_data': 'settings'}
            ]
        ]
        return self.create_inline_keyboard(buttons)
    
    # ==================== UTILITY METHODS ====================
    
    def get_user_slippage(self, user_id):
        """Get user slippage preference with default fallback"""
        return self.user_slippage.get(user_id, TRADING_CONFIG.get('BSC', {}).get('slippage', 0.5))
    
    def set_user_slippage(self, user_id, slippage):
        """Set user slippage preference"""
        self.user_slippage[user_id] = slippage
    
    def get_chain_data(self, chain):
        """Get chain configuration data"""
        chain_configs = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'dex': 'Uniswap v3',
                'rpc': 'https://mainnet.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'dex': 'PancakeSwap v2',
                'rpc': 'https://bsc-dataseed.binance.org'
            }
        }
        return chain_configs.get(chain, chain_configs['BSC'])
    
    # ==================== KEYBOARD HELPER METHODS ====================
    
    def _create_amount_selection_keyboard(self, native_symbol, action, user_id):
        """Create keyboard with quick amount buttons for buy/sell actions"""
        current_slippage = self.get_user_slippage(user_id) if user_id else TRADING_CONFIG.get('BSC', {}).get('slippage', 0.5)
        
        if action == 'buy':
            # Buy buttons - fixed amounts
            keyboard = [
                [
                    {'text': f"0.01 {native_symbol}", 'callback_data': "quick_amount_0.01"},
                    {'text': f"0.05 {native_symbol}", 'callback_data': "quick_amount_0.05"},
                    {'text': f"0.1 {native_symbol}", 'callback_data': "quick_amount_0.1"}
                ],
                [
                    {'text': f"0.5 {native_symbol}", 'callback_data': "quick_amount_0.5"},
                    {'text': f"1 {native_symbol}", 'callback_data': "quick_amount_1"},
                    {'text': f"Buy X {native_symbol}", 'callback_data': "custom_amount"}
                ],
                [
                    {'text': f"Slippage | {current_slippage}%", 'callback_data': "settings_slippage"}
                ],
                [
                    {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
                ]
            ]
        else:
            # Sell buttons - percentage of token balance
            keyboard = [
                [
                    {'text': "10%", 'callback_data': "sell_percentage_10"},
                    {'text': "25%", 'callback_data': "sell_percentage_25"},
                    {'text': "50%", 'callback_data': "sell_percentage_50"}
                ],
                [
                    {'text': "75%", 'callback_data': "sell_percentage_75"},
                    {'text': "100%", 'callback_data': "sell_percentage_100"},
                    {'text': f"Sell X", 'callback_data': "custom_amount"}
                ],
                [
                    {'text': f"Slippage | {current_slippage}%", 'callback_data': f"edit_slippage_{action}"}
                ],
                [
                    {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
                ]
            ]
        
        return self.create_inline_keyboard(keyboard)
    
    def _create_back_button_keyboard(self):
        """Create simple keyboard with back button"""
        return self.create_inline_keyboard([
            [{'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}]
        ])
    
    def get_buy_sell_menu(self):
        buttons = [
            [
                {'text': '🟢 Buy Tokens', 'callback_data': 'buy'},
                {'text': '🔴 Sell Tokens', 'callback_data': 'sell'}
            ],
            [
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]
        ]
        return self.create_inline_keyboard(buttons)
    
    def get_chain_selection_menu(self):
        """Get chain selection menu"""
        buttons = [
            [
                {'text': '🔵 Ethereum', 'callback_data': 'select_chain_eth'},
                {'text': '🟡 BSC', 'callback_data': 'select_chain_bsc'}
            ],
        
            [
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]
        ]
        return self.create_inline_keyboard(buttons)
    
    async def handle_start_command(self, chat_id, user_id, username):
        # Check if user has Twitter authentication
        twitter_info = self.firebase.get_twitter_user_info(user_id)
        twitter_username = None
        if twitter_info and twitter_info.get('isAuthenticated'):
            twitter_username = twitter_info.get('twitterUsername')
        
        text = f"Welcome, {username}!\nStep into the future with Future Edge Tech 🚀\n\nAuthenticate your X account to unlock seamless direct trades and scan any BSC or ETH tokens — all within the X platform."
        await self.send_message(chat_id, text, self.get_main_menu(twitter_username))
    
    async def handle_callback_query(self, chat_id, user_id, callback_data):
        if callback_data == 'main_menu':
            # Get username from cache or use default
            username = self.user_cache.get(user_id, 'User')
            
            # If username is still 'User' and not in cache, try to get it from Telegram API
            if username == 'User':
                try:
                    import aiohttp
                    url = f"{self.base_url}/getChat"
                    data = {'chat_id': user_id}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=data) as response:
                            result = await response.json()
                            if result.get('ok'):
                                user_info = result.get('result', {})
                                username = user_info.get('first_name', 'User')
                                # Cache it for future use
                                self.user_cache[user_id] = username
                except Exception as e:
                    logger.error(f"Error getting user info for {user_id}: {e}")
                    username = 'User'
            
            await self.handle_start_command(chat_id, user_id, username)
        elif callback_data == 'twitter_auth':
            await self.handle_twitter_auth(chat_id, user_id)
        elif callback_data == 'remove_twitter_auth':
            await self.handle_remove_twitter_auth(chat_id, user_id)
        elif callback_data == 'twitter_auth_complete':
            await self.handle_twitter_auth_complete(chat_id, user_id)
        elif callback_data.startswith('save_twitter_auth_'):
            await self.save_twitter_auth_data(chat_id, user_id, callback_data)
        elif callback_data == 'x_bot_status':
            await self.show_x_bot_status(chat_id)
        elif callback_data == 'reset_tweet_id':
            await self.reset_tweet_id_command(chat_id)
        elif callback_data == 'buy_sell':
            await self.handle_buy_sell_menu(chat_id)
        elif callback_data == 'buy':
            await self.handle_buy_tokens(chat_id, user_id)
        elif callback_data == 'sell':
            await self.handle_sell_tokens(chat_id, user_id)
        elif callback_data == 'select_chain_eth':
            await self.handle_chain_selection(chat_id, user_id, 'ETH')
        elif callback_data == 'select_chain_bsc':
            await self.handle_chain_selection(chat_id, user_id, 'BSC')
        elif callback_data == 'select_chain_sepolia':
            await self.handle_chain_selection(chat_id, user_id, 'SEPOLIA')
        elif callback_data == 'buy_eth':
            await self.handle_buy_tokens_with_chain(chat_id, user_id, 'ETH')
        elif callback_data == 'buy_bsc':
            await self.handle_buy_tokens_with_chain(chat_id, user_id, 'BSC')
        elif callback_data == 'buy_sepolia':
            await self.handle_buy_tokens_with_chain(chat_id, user_id, 'SEPOLIA')
        elif callback_data == 'sell_eth':
            await self.handle_sell_tokens_with_chain(chat_id, user_id, 'ETH')
        elif callback_data == 'sell_bsc':
            await self.handle_sell_tokens_with_chain(chat_id, user_id, 'BSC')
        elif callback_data == 'sell_sepolia':
            await self.handle_sell_tokens_with_chain(chat_id, user_id, 'SEPOLIA')
        elif callback_data.startswith('quick_buy_'):
            chain = callback_data.replace('quick_buy_', '').upper()
            await self.handle_quick_buy_from_success(chat_id, user_id, chain)
        elif callback_data.startswith('quick_sell_'):
            chain = callback_data.replace('quick_sell_', '').upper()
            await self.handle_quick_sell_from_success(chat_id, user_id, chain)
        elif callback_data == 'wallet':
            await self.handle_wallet_menu(chat_id, user_id)
        elif callback_data == 'balance':
            await self.handle_check_balance(chat_id, user_id)
        elif callback_data == 'scanner':
            await self.handle_token_scanner(chat_id)
        elif callback_data == 'positions':
            await self.handle_positions(chat_id)
        elif callback_data == 'transfer':
            await self.handle_transfer(chat_id)
        elif callback_data == 'token_scanner_menu':
            await self.handle_token_scanner(chat_id)
        elif callback_data == 'scan_bsc':
            await self.handle_scan_chain(chat_id, 'BSC')
        elif callback_data == 'scan_eth':
            await self.handle_scan_chain(chat_id, 'ETH')
        elif callback_data.startswith('copy_address_'):
            await self.handle_copy_address(chat_id, callback_data)
        elif callback_data.startswith('refresh_scan_'):
            await self.handle_refresh_scan(chat_id, callback_data)
        elif callback_data.startswith('positions_chain_'):
            chain = callback_data.replace('positions_chain_', '').upper()
            await self.handle_positions_chain_selection(chat_id, user_id, chain)
        elif callback_data.startswith('transfer_chain_'):
            chain = callback_data.replace('transfer_chain_', '').upper()
            # Map chain names to expected format
            chain_mapping = {
                'ETH': 'ETH',
                'BSC': 'BSC',
                'SEPOLIA': 'SEPOLIA'
            }
            chain = chain_mapping.get(chain, chain)
            await self.handle_transfer_chain_selection(chat_id, user_id, chain)
        elif callback_data == 'positions_check_contract':
            await self.handle_positions_check_contract(chat_id, user_id)
        elif callback_data.startswith('check_contract_'):
            chain = callback_data.replace('check_contract_', '').upper()
            await self.handle_contract_balance_check(chat_id, user_id, self.trading_state.get(chat_id, {}).get('contract_address'), chain)
        elif callback_data.startswith('transfer_native_'):
            chain = callback_data.replace('transfer_native_', '').upper()
            # Map chain names to expected format
            chain_mapping = {
                'ETH': 'ETH',
                'BSC': 'BSC',
                'SEPOLIA': 'SEPOLIA'
            }
            chain = chain_mapping.get(chain, chain)
            await self.handle_transfer_native(chat_id, user_id, chain)
        elif callback_data.startswith('transfer_token_'):
            chain = callback_data.replace('transfer_token_', '').upper()
            # Map chain names to expected format
            chain_mapping = {
                'ETH': 'ETH',
                'BSC': 'BSC',
                'SEPOLIA': 'SEPOLIA'
            }
            chain = chain_mapping.get(chain, chain)
            await self.handle_transfer_token(chat_id, user_id, chain)
        elif callback_data == 'confirm_transfer_native':
            await self.execute_transfer(chat_id, user_id, 'native')
        elif callback_data == 'confirm_transfer_token':
            await self.execute_transfer(chat_id, user_id, 'token')
        elif callback_data == 'settings':
            await self.handle_settings(chat_id)
        elif callback_data == 'settings_slippage':
            await self.handle_slippage_settings(chat_id)
        elif callback_data == 'help':
            await self.handle_help(chat_id)
        elif callback_data == 'create_wallet':
            await self.handle_create_wallet(chat_id, user_id)
        elif callback_data == 'import_wallet':
            await self.handle_import_wallet(chat_id, user_id)
        elif callback_data == 'show_private_key':
            await self.handle_show_private_key(chat_id, user_id)
        elif callback_data == 'delete_wallet':
            await self.handle_delete_wallet(chat_id, user_id)
        elif callback_data == 'confirm_buy':
            await self.handle_confirm_buy(chat_id, user_id)
        elif callback_data == 'confirm_sell':
            await self.handle_confirm_sell(chat_id, user_id)
        elif callback_data.startswith('quick_amount_'):
            amount = callback_data.replace('quick_amount_', '')
            await self.handle_quick_amount_selection(chat_id, user_id, amount)
        elif callback_data == 'custom_amount':
            await self.handle_custom_amount_selection(chat_id, user_id)
        elif callback_data.startswith('edit_slippage_'):
            action = callback_data.replace('edit_slippage_', '')
            await self.handle_edit_slippage(chat_id, user_id, action)
        elif callback_data.startswith('set_slippage_'):
            slippage = callback_data.replace('set_slippage_', '')
            await self.handle_set_slippage(chat_id, user_id, slippage)
        elif callback_data.startswith('sell_percentage_'):
            percentage = callback_data.replace('sell_percentage_', '')
            await self.handle_sell_percentage_selection(chat_id, user_id, percentage)
        else:
            await self.send_message(chat_id, "❌ Unknown option selected.")
    
    async def handle_buy_sell_menu(self, chat_id):
        text = "💰 Trading Operations\n\n"
        text += f"📋 Step 1: Select the blockchain network\n\n"
      
        text += f"Choose your preferred network:"
        await self.send_message(chat_id, text, self.get_chain_selection_menu())
    
    async def handle_buy_tokens(self, chat_id, user_id):
        
        if not self.firebase.user_has_wallet(user_id):
            text = "❌ You need a wallet first! Please create one."
            keyboard = self.create_inline_keyboard([[
                {'text': '🔐 Create Wallet', 'callback_data': 'wallet'},
             
            ],[{'text': '📥 Import wallet', 'callback_data': 'import_wallet'}],[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)
            return
        
        text = f"🟢 Buy Tokens\n\n"
        text += f"📋 Step 1: Select the blockchain network\n\n"
        text += f"🔗 Available Networks:\n"
        text += f"• 🔵 **ETH Mainnet** - Ethereum main network\n"
        text += f"• 🟡 **BSC Mainnet** - Binance Smart Chain main network\n"
        text += f"• 🟣 **Sepolia Testnet** - Ethereum test network\n\n"
        text += f"Choose your preferred network:"
        
        keyboard = self.get_chain_selection_menu('buy')
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_sell_tokens(self, chat_id, user_id):
        
        if not self.firebase.user_has_wallet(user_id):
            text = "❌ You need a wallet first! Please create one."
            keyboard = self.create_inline_keyboard([[
                {'text': '🔐 Create Wallet', 'callback_data': 'wallet'}
                    
            ],[{'text': '📥 Import wallet', 'callback_data': 'import_wallet'}],[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)
            return
        
        text = f"🔴 Sell Tokens\n\n"
        text += f"📋 Step 1: Select the blockchain network\n\n"
        text += f"🔗 Available Networks:\n"
        text += f"• 🔵 **ETH Mainnet** - Ethereum main network\n"
        text += f"• 🟡 **BSC Mainnet** - Binance Smart Chain main network\n"
        text += f"• 🟣 **Sepolia Testnet** - Ethereum test network\n\n"
        text += f"Choose your preferred network:"
        
        keyboard = self.get_chain_selection_menu('sell')
        await self.send_message(chat_id, text, keyboard)
    
    def get_buy_sell_for_chain_menu(self, chain):
        """Get buy/sell menu for a specific chain"""
        chain_info = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'icon': '🔵'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'icon': '🟡'
            },
            'SEPOLIA': {
                'name': 'Sepolia Testnet',
                'symbol': 'ETH',
                'icon': '🟣'
            }
        }
        
        chain_data = chain_info[chain]
        
        buttons = [
            [
                {'text': '🟢 Buy Tokens', 'callback_data': f'buy_{chain.lower().replace("-", "_")}'},
                {'text': '🔴 Sell Tokens', 'callback_data': f'sell_{chain.lower().replace("-", "_")}'}
            ],
            [
                {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
            ]
        ]
        return self.create_inline_keyboard(buttons)
    
    async def handle_chain_selection(self, chat_id, user_id, chain):
        """Handle chain selection and show buy/sell options"""
        # Store the selected chain in trading state
        self.trading_state[chat_id] = {'chain': chain}
        
        # Check if there's a scanned token available for this chain
        if chat_id in self.last_scan_results:
            scan_data = self.last_scan_results[chat_id]
            if scan_data['chain'] == chain:
                # Store the scanned token information in trading state
                self.trading_state[chat_id]['token_address'] = scan_data['token_address']
                self.trading_state[chat_id]['from_scanner'] = True
                logger.info(f"Scanner token stored for chat {chat_id}: {scan_data['token_address']}")
        
        logger.info(f"Chain selected for chat {chat_id}: {chain}, trading state: {self.trading_state[chat_id]}")
        
        chain_info = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'icon': '🔵',
                'rpc': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'icon': '🟡',
                'rpc': 'https://bsc-dataseed.binance.org/'
            },
            'SEPOLIA': {
                'name': 'Sepolia Testnet',
                'symbol': 'ETH',
                'icon': '🟣',
                'rpc': 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY'
            }
        }
        
        chain_data = chain_info[chain]
        
        text = f"{chain_data['icon']} Selected Network: {chain_data['name']}\n\n"
        text += f"📋 Step 2: Select your trading action\n\n"
        text += f"🌐 Network: {chain_data['name']}\n"
        text += f"💰 Native Token: {chain_data['symbol']}\n"
        text += f"Choose what you want to do:"
        
        keyboard = self.get_buy_sell_for_chain_menu(chain)
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_buy_tokens_with_chain(self, chat_id, user_id, chain):
        """Handle buy tokens with a pre-selected chain"""
        if not self.firebase.user_has_wallet(user_id):
            text = "❌ You need a wallet first! Please create one."
            keyboard = self.create_inline_keyboard([[
                {'text': '🔐 Create Wallet', 'callback_data': 'wallet'}
                        
            ],[{'text': '📥 Import wallet', 'callback_data': 'import_wallet'}],[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)
            return
        
        # Set trading state with action and chain
        self.trading_state[chat_id] = {'action': 'buy', 'chain': chain}
        
        # Check if coming from scanner with pre-selected token
        if chat_id in self.trading_state and self.trading_state[chat_id].get('from_scanner'):
            token_address = self.trading_state[chat_id].get('token_address')
            if token_address:
                # Pre-fill the token address and go to amount input
                self.trading_state[chat_id]['token_address'] = token_address
                await self.handle_token_address_input_from_scanner(chat_id, user_id, token_address, chain, 'buy')
                return
        
        logger.info(f"Buy action set for chat {chat_id}: action=buy, chain={chain}, trading state: {self.trading_state[chat_id]}")
        
        chain_info = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'icon': '🔵'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'icon': '🟡'
            },
            'SEPOLIA': {
                'name': 'Sepolia Testnet',
                'symbol': 'ETH',
                'icon': '🟣'
            }
        }
        
        chain_data = chain_info[chain]
        
        text = f"{chain_data['icon']} Buy Tokens on {chain_data['name']}\n\n"
        text += f"📋 Step 3: Enter the token contract address\n\n"
        text += f"💡 Format: 0x followed by 40 characters\n"
        text += f"Example: 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5\n\n"
        text += f"🌐 Network: {chain_data['name']}\n"
        text += f"💰 **Native Token:** {chain_data['symbol']}\n\n"
        text += f"🔧 Just type the address below:"
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_sell_tokens_with_chain(self, chat_id, user_id, chain):
        """Handle sell tokens with a pre-selected chain"""
        if not self.firebase.user_has_wallet(user_id):
            text = "❌ You need a wallet first! Please create one."
            keyboard = self.create_inline_keyboard([[
                {'text': '🔐 Create Wallet', 'callback_data': 'wallet'}
                        
            ],[{'text': '📥 Import wallet', 'callback_data': 'import_wallet'}],[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)
            return
        
        # Set trading state with action and chain
        self.trading_state[chat_id] = {'action': 'sell', 'chain': chain}
        
        # Check if coming from scanner with pre-selected token
        if chat_id in self.trading_state and self.trading_state[chat_id].get('from_scanner'):
            token_address = self.trading_state[chat_id].get('token_address')
            if token_address:
                # Pre-fill the token address and go to amount input
                self.trading_state[chat_id]['token_address'] = token_address
                await self.handle_token_address_input_from_scanner(chat_id, user_id, token_address, chain, 'sell')
                return
        
        logger.info(f"Sell action set for chat {chat_id}: action=sell, chain={chain}, trading state: {self.trading_state[chat_id]}")
        
        chain_info = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'icon': '🔵'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'icon': '🟡'
            },
            'SEPOLIA': {
                'name': 'Sepolia Testnet',
                'symbol': 'ETH',
                'icon': '🟣'
            }
        }
        
        chain_data = chain_info[chain]
        
        text = f"{chain_data['icon']} Sell Tokens on {chain_data['name']}\n\n"
        text += f"📋 Step 3: Enter the token contract address\n\n"
        text += f"💡 Format: 0x followed by 40 characters\n"
        text += f"Example: 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5\n\n"
        text += f"🌐 Network: {chain_data['name']}\n"
        text += f"💰 **Native Token:** {chain_data['symbol']}\n\n"
        text += f"🔧 Just type the address below:"
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_token_address_input_from_scanner(self, chat_id, user_id, token_address, chain, action):
        """Handle token address input when coming from scanner (pre-filled)"""
        try:
            # Update trading state
            self.trading_state[chat_id]['token_address'] = token_address
            
            # Get detailed token information using scanner
            scan_result = await self.token_scanner.scan_token(token_address, chain)
            
            if scan_result and "error" not in scan_result:
                # Format token information
                token_name = scan_result.get('token_name', 'Unknown')
                token_symbol = scan_result.get('token_symbol', 'Unknown')
                price_usd = scan_result.get('price_usd', 0) or 0
                price_change_24h = scan_result.get('price_change_24h', 0) or 0
                liquidity_usd = scan_result.get('liquidity_usd', 0) or 0
                volume_24h = scan_result.get('volume_24h', 0) or 0
                fdv = scan_result.get('fdv', 0) or 0
                transactions_24h = scan_result.get('transactions_24h', {'buys': 0, 'sells': 0})
                
                # Get tax information
                buy_tax = scan_result.get('buy_tax', 0)
                sell_tax = scan_result.get('sell_tax', 0)
                transfer_tax = scan_result.get('transfer_tax', 0)
                
                # Format price change
                if price_change_24h is not None:
                    if abs(price_change_24h) > 1:
                        if price_change_24h > 0:
                            price_change_str = f"📈 +{price_change_24h:.2f}%"
                        else:
                            price_change_str = f"📉 {price_change_24h:.2f}%"
                    else:
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
                
                # Get wallet balance
                wallet = self.firebase.get_user_wallet(user_id)
                wallet_balance = 0
                native_balance = 0
                
                try:
                    wallet_address = wallet['public_key']
                    
                    # Get token balance
                    wallet_balance = self.trading._get_token_balance(chain, token_address, wallet_address)
                    
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
                text += f"⚖️ Taxes | 🅑 {buy_tax:.1f}% 🅢 {sell_tax:.1f}% 🅣 {transfer_tax:.1f}%\n"
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
                    keyboard = self.get_amount_selection_keyboard(chain, action, user_id)
                else:  # sell
                    text += f"Enter Amount ({token_symbol}):"
                    keyboard = self.get_amount_selection_keyboard(chain, action, user_id)
                    
                await self.send_message(chat_id, text, keyboard)
                
            else:
                # Fallback to simple format if scanning fails
                text = f"✅ Token Address Valid!\n\n"
                text += f"🔑 Token: `{token_address[:20]}...`\n"
                text += f"🌐 Network: {chain}\n\n"
                
                if action == 'buy':
                    text += f"💰 Enter the amount of {chain} to spend\n\n"
                    text += f"💡 Example: 0.1, 0.5, 1.0\n\n"
                    text += f"🔧 Just type the amount below:"
                    keyboard = self.get_amount_selection_keyboard(chain, action, user_id)
                else:  # sell
                    text += f"💰 Enter the amount of tokens to sell\n\n"
                    text += f"💡 Example: 100, 1000, 5000\n\n"
                    text += f"🔧 Just type the amount below:"
                    keyboard = self.get_amount_selection_keyboard(chain, action, user_id)
                    
                await self.send_message(chat_id, text, keyboard)
                
        except Exception as e:
            logger.error(f"Error handling token address from scanner: {e}")
            await self.send_message(chat_id, f"❌ Error processing token: {str(e)}")
    
    async def handle_wallet_menu(self, chat_id, user_id):
        
        if self.firebase.user_has_wallet(user_id):
            wallet = self.firebase.get_user_wallet(user_id)
            
            # Add null check for wallet
            if wallet is None:
                text = "❌ Error retrieving wallet information. Please try again or contact support."
                keyboard = self.create_inline_keyboard([[
                    {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                ]])
                await self.send_message(chat_id, text, keyboard)
                return
            
            text = f"🔐 Wallet Management\n\n"
            text += f"✅ You have a wallet!\n\n"
            text += f"🔑 Public Address: `{wallet['public_key']}`\n"
            text += f"📅 Created: {wallet['created_at'][:10]}\n\n"
            text += f"Choose an option:"
            
            buttons = [
                [
                    {'text': '🔑 Show Private Key', 'callback_data': 'show_private_key'},
                    {'text': '🗑️ Delete Wallet', 'callback_data': 'delete_wallet'}
                ],
                [
                    {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                ]
            ]
            keyboard = self.create_inline_keyboard(buttons)
            
        else:   
            text = "🔐 Wallet Management\n\n❌ You don't have a wallet yet.\n\nChoose an option:"
            buttons = [
                [
                    {'text': '🆕 Create Wallet', 'callback_data': 'create_wallet'},
                    {'text': '📥 Import Wallet', 'callback_data': 'import_wallet'}
                ],
                [
                    {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                ]
            ]
            keyboard = self.create_inline_keyboard(buttons)
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_check_balance(self, chat_id, user_id):
        
        if not self.firebase.user_has_wallet(user_id):
            text = "❌ You don't have a wallet yet. Please create one first!"
            keyboard = self.create_inline_keyboard([[
                {'text': '🔐 Create Wallet', 'callback_data': 'create_wallet'}
            ],[{'text': '📥 Import wallet', 'callback_data': 'import_wallet'}],[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)
            return
        
        wallet = self.firebase.get_user_wallet(user_id)
        
        # Add null check for wallet
        if wallet is None:
            text = "❌ Error retrieving wallet information. Please try again or contact support."
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)
            return
        
        text = f"💳 Wallet Balance\n\n"
        text += f"🔑 Address: `{wallet['public_key'][:20]}...`\n\n"
        
        # Check balances on different chains
        chains = ['BSC', 'ETH']
        for chain in chains:
            try:
                balance = self.blockchain.get_balance(chain, wallet['public_key'])
                if balance is not None:
                    symbol = 'BNB' if chain == 'BSC' else 'ETH'
                    text += f"{chain}: {balance:.6f} {symbol}\n"
                else:
                    text += f"{chain}: Connection failed\n"
            except Exception as e:
                text += f"{chain}: Error checking balance\n"
        
        keyboard = self.create_inline_keyboard([[
            {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
        ]])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_token_scanner(self, chat_id):
        text = "🔍 Token Scanner\n\n"
        text += "Scan tokens on BSC or ETH chains for real-time data.\n\n"
        text += "📋 How to use:\n"
        text += "• Select your preferred chain\n"
        text += "• Enter the token contract address\n"
        text += "• Get detailed token information\n\n"
        text += "🔗 Supported Chains: BSC, ETH, SEPOLIA\n"
        text += "💡 Tip: Use this to research tokens before trading!"
        
        keyboard = self.create_inline_keyboard([
            [
                
                {'text': '🔵 ETH', 'callback_data': 'scan_eth'},
                {'text': '🟡 BSC', 'callback_data': 'scan_bsc'}
            ],
            [
            {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_positions(self, chat_id):
        """Handle positions menu"""
        text = "📊 Positions & Balances\n\n"
        text += "Select a blockchain network to check your token balances:\n\n"
        text += "💡 What you can do:\n"
        text += "• Check native token balance (ETH/BNB)\n"
        text += "• View all token positions on a chain\n"
        text += "• Check specific token contract balances\n\n"
        text += "Choose your network:"
        
        keyboard = self.create_inline_keyboard(self.positions_manager.get_positions_menu())
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_positions_chain_selection(self, chat_id, user_id, chain):
        """Handle chain selection for positions"""
        try:
            # Check if user has a wallet
            if not self.firebase.user_has_wallet(user_id):
                await self.send_message(chat_id, "❌ You don't have a wallet. Please create one first.")
                return
            
            wallet = self.firebase.get_user_wallet(user_id)
            if not wallet:
                await self.send_message(chat_id, "❌ Could not retrieve wallet information.")
                return
            
            # Show loading message
          
            
            # Get balances
            balance_data = await self.positions_manager.get_all_token_balances(
                wallet['public_key'], 
                chain
            )
            
            # Format and display results
            formatted_message = self.positions_manager.format_balance_message(balance_data)
            
            # Create menu with options
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔍 Check Contract', 'callback_data': 'positions_check_contract'},
                    {'text': '🔄 Refresh', 'callback_data': f'positions_chain_{chain.lower()}'}
                ],
                [
                    {'text': '🔙 Back to Positions', 'callback_data': 'positions'},
                    {'text': '🏠 Main Menu', 'callback_data': 'main_menu'}
                ],
                [
                    {'text': '💰 Buy/Sell', 'callback_data': f'select_chain_{chain.lower()}'}
                ]
            ])
            
            await self.send_message(chat_id, formatted_message, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling positions chain selection: {e}")
            await self.send_message(chat_id, f"❌ Error checking balances: {str(e)}")
    
    async def handle_positions_check_contract(self, chat_id, user_id):
        """Handle check contract balance request"""
        text = "🔍 Check Contract Balance\n\n"
        text += "Enter the token contract address you want to check:\n\n"
        text += "💡 Format: 0x followed by 40 characters\n"
        text += "**Example:** 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5\n\n"
        text += "🔧 Just type the contract address below:"
        
        # Store state for contract checking
        if chat_id not in self.trading_state:
            self.trading_state[chat_id] = {}
        self.trading_state[chat_id]['action'] = 'check_contract'
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '🔙 Back to Positions', 'callback_data': 'positions'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_contract_balance_check(self, chat_id, user_id, contract_address, chain):
        """Handle checking balance of a specific contract"""
        try:
            # Check if user has a wallet
            if not self.firebase.user_has_wallet(user_id):
                await self.send_message(chat_id, "❌ You don't have a wallet. Please create one first.")
                return
            
            wallet = self.firebase.get_user_wallet(user_id)
            if not wallet:
                await self.send_message(chat_id, "❌ Could not retrieve wallet information.")
                return
            
            if not contract_address:
                await self.send_message(chat_id, "❌ No contract address found. Please try again.")
                return
            
            # Show loading message
           
            
            
            # Check contract balance
            balance_data = await self.positions_manager.check_specific_contract_balance(
                wallet['public_key'],
                contract_address,
                chain
            )
            
            # Format and display results
            formatted_message = self.positions_manager.format_contract_balance_message(balance_data)
            
            # Create menu with options
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔄 Check Another', 'callback_data': 'positions_check_contract'},
                    {'text': '🔙 Back to Positions', 'callback_data': 'positions'}
                ],
                [
                    {'text': '🏠 Main Menu', 'callback_data': 'main_menu'}
                ],
                [
                    {'text': '💰 Buy/Sell', 'callback_data': f'select_chain_{chain.lower()}'}
                ]
            ])
            
            await self.send_message(chat_id, formatted_message, keyboard)
            
            # Clear the trading state
            if chat_id in self.trading_state:
                del self.trading_state[chat_id]
            
        except Exception as e:
            logger.error(f"Error checking contract balance: {e}")
            await self.send_message(chat_id, f"❌ Error checking contract balance: {str(e)}")
    
    async def handle_transfer(self, chat_id):
        """Handle transfer menu"""
        text = "💸 Transfer Tokens\n\n"
        text += "Select a blockchain network to transfer tokens:\n\n"
        text += "💡 What you can transfer:\n"
        text += "• Native tokens (ETH/BNB/tBNB)\n"
        text += "• ERC-20 tokens on any supported chain\n\n"
        text += "Choose your network:"
        
        keyboard = self.create_inline_keyboard(self.transfer_manager.get_transfer_menu())
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_transfer_chain_selection(self, chat_id, user_id, chain):
        """Handle chain selection for transfer"""
        try:
            # Check if user has a wallet
            if not self.firebase.user_has_wallet(user_id):
                await self.send_message(chat_id, "❌ You don't have a wallet. Please create one first.")
                return
            
            wallet = self.firebase.get_user_wallet(user_id)
            if not wallet:
                await self.send_message(chat_id, "❌ Could not retrieve wallet information.")
                return
            
            # Show transfer type selection
            text = f"💸 Transfer on {self.transfer_manager.get_chain_display_name(chain)}\n\n"
            text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
            text += f"💰 Native Token: {self.transfer_manager.get_native_symbol(chain)}\n\n"
            text += "Select transfer type:"
            
            keyboard = self.create_inline_keyboard(self.transfer_manager.get_transfer_type_menu(chain))
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling transfer chain selection: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")
    
    async def handle_transfer_native(self, chat_id, user_id, chain):
        """Handle native token transfer"""
        try:
            # Check if user has a wallet
            if not self.firebase.user_has_wallet(user_id):
                await self.send_message(chat_id, "❌ You don't have a wallet. Please create one first.")
                return
            
            wallet = self.firebase.get_user_wallet(user_id)
            if not wallet:
                await self.send_message(chat_id, "❌ Could not retrieve wallet information.")
                return
            
            # Store transfer state
            if chat_id not in self.trading_state:
                self.trading_state[chat_id] = {}
            
            self.trading_state[chat_id].update({
                'action': 'transfer_native',
                'chain': chain,
                'transfer_type': 'native'
            })
            
            # Ask for recipient address
            native_symbol = self.transfer_manager.get_native_symbol(chain)
            text = f"💸 Transfer {native_symbol}\n\n"
            text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
            text += f"💰 Token: {native_symbol}\n\n"
            text += "📝 Enter the recipient address:\n\n"
            text += "💡 Format: 0x followed by 40 characters\n"
            text += "**Example:** 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5\n\n"
            text += "🔧 **Just type the address below:**"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling transfer native: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")
    
    async def handle_transfer_token(self, chat_id, user_id, chain):
        """Handle ERC-20 token transfer"""
        try:
            # Check if user has a wallet
            if not self.firebase.user_has_wallet(user_id):
                await self.send_message(chat_id, "❌ You don't have a wallet. Please create one first.")
                return
            
            wallet = self.firebase.get_user_wallet(user_id)
            if not wallet:
                await self.send_message(chat_id, "❌ Could not retrieve wallet information.")
                return
            
            # Store transfer state
            if chat_id not in self.trading_state:
                self.trading_state[chat_id] = {}
            
            self.trading_state[chat_id].update({
                'action': 'transfer_token',
                'chain': chain,
                'transfer_type': 'token'
            })
            
            # Ask for token contract address
            text = f"🪙 Transfer Token\n\n"
            text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
            text += f"💰 Native Token: {self.transfer_manager.get_native_symbol(chain)}\n\n"
            text += "📝 Enter the token contract address:\n\n"
            text += "💡 Format: 0x followed by 40 characters\n"
            text += "**Example:** 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5\n\n"
            text += "🔧 Just type the contract address below:"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            return
            
            # Ask for token contract address
            text = f"🪙 Transfer Token\n\n"
            text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
            text += f"💰 Native Token: {self.transfer_manager.get_native_symbol(chain)}\n\n"
            text += "📝 Enter the token contract address:\n\n"
            text += "💡 Format: 0x followed by 40 characters\n"
            text += "**Example:** 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5\n\n"
            text += "🔧 Just type the contract address below:"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling transfer token: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")
    
    async def handle_scan_chain(self, chat_id, chain):
        """Handle chain selection for token scanning"""
        text = f"🔍 Token Scanner - {chain}\n\n"
        text += f"📝 Enter the token contract address you want to scan:\n\n"
        text += "💡 Example: `0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5`"
        
        # Store the selected chain for this chat
        self.trading_state[chat_id] = {'action': 'scan_token', 'chain': chain}
        
        keyboard = self.create_inline_keyboard([[
            {'text': '🔙 Back to Scanner', 'callback_data': 'scanner'}
        ]])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_settings(self, chat_id):
        text = "⚙️ Bot Settings\n\n"
       
        text += f"📊 Slippage: {self.get_user_slippage(chat_id)}%"
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '📊 Slippage', 'callback_data': 'settings_slippage'}
            ],
            [
            {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_slippage_settings(self, chat_id):
        """Handle slippage settings"""
        text = "📊 Slippage Settings\n\n"
       
        text += f"📈 Current Slippage: {self.get_user_slippage(chat_id)}%\n\n"
  

        text += "⚠️ Important:\n"
        text += "• Enter only the number (e.g., 0.5, not 0.5%)\n"
        text += "• Values between 0.1 and 50.0 are accepted\n"
        text += "• Higher values = higher success rate but worse prices\n\n"
        text += "🔧 Just type the number below:"
        
        # Store state for slippage input
        if chat_id not in self.trading_state:
            self.trading_state[chat_id] = {}
        self.trading_state[chat_id]['action'] = 'set_slippage'
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '🔙 Back to Settings', 'callback_data': 'settings'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    
    async def handle_help(self, chat_id):
        text = "❓ **Help & Support**\n\n"
        text += "🤖 **Available Commands:**\n"
        text += "• /start - Start the bot in Tg\n"
        text += "• /help - Show this help message\n\n"
        text += "🚀 **Quick Trading Commands:**\n"
        text += "• /buybsc - Quick buy on BSC\n"
        text += "• /buyeth - Quick buy on Ethereum\n"
        text += "• /sellbsc - Quick sell on BSC\n"
        text += "• /selleth - Quick sell on Ethereum\n\n"
        text += "💼 **Wallet Setup:**\n"
        text += "• Go to Wallet & Generate/import wallet\n\n"
        text += "**Authenticate X Account:**\n\n"
        text += "**Commands on X (e.g):**\n"
        text += "• Buy 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 0.01 ETH\n"
        text += "• Sell 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 1000 BSC\n\n"
        text += "🔍 **Token Scanner:**\n"
        text += "• SCAN 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 BSC\n\n"
        text += "💰 **Features:**\n"
        text += "• Create and manage wallets\n"
        text += "• Buy/sell tokens on Tg + X (Twitter)\n"
        text += "• Check balances\n"
        text += "• Token scanning on Tg + X (Twitter)\n\n"
        text += "🆘 **Need Help?**\n"
        text += "Contact support @fetsxbotsupport for any assistance."
        
        keyboard = self.create_inline_keyboard([[
            {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
        ]])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_twitter_auth(self, chat_id, user_id):
        """Handle Twitter authentication"""
        # Check if user is already authenticated
        twitter_info = self.firebase.get_twitter_user_info(user_id)
        
        if twitter_info and twitter_info.get('isAuthenticated'):
            # User is already authenticated
            username = twitter_info.get('twitterUsername', 'Unknown')
            text = f"🐦 **Twitter Connected Successfully!**\n\n"
            text += f"✅ **Username:** @{username}\n"
            text += f"🔗 **Status:** Connected\n"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🗑️ Remove Twitter Auth', 'callback_data': 'remove_twitter_auth'}
                ],
                [
                    {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                ],
                
            ])
            
            await self.send_message(chat_id, text, keyboard)
        else:
            # Show authentication flow
            auth_url = f"https://twitter-auth-frontend.vercel.app/?user={user_id}"
            
        text = "🐦 **Twitter Authentication**\n\n"
      
        text += "📱 **Authentication Process:**\n"
        text += "1. Click the link below to authenticate\n"
        text += "2. Complete Twitter OAuth process\n"
        text += "3. Return here and click 'Complete'\n"
        text += f"🔗 **Authentication Link:**\n[Click here to authenticate]({auth_url})\n\n"
        text += "After completing authentication on Twitter, click the \"Complete\" button below."
            
        keyboard = self.create_inline_keyboard([
            [
                    {'text': '✅ Complete', 'callback_data': 'twitter_auth_complete'}
            ],
            [
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_remove_twitter_auth(self, chat_id, user_id):
        """Handle removing Twitter authentication"""
        try:
            # Remove Twitter auth data from Firebase
            success = self.firebase.remove_twitter_auth(user_id)
            
            if success:
                text = "🗑️ **Twitter Authentication Removed**\n\n"
                text += "✅ Your Twitter account has been disconnected.\n"
                text += "🔒 All Twitter-related data has been cleared.\n\n"
                text += "💡 You can re-authenticate anytime from the main menu."
            else:
                text = "❌ **Error Removing Twitter Auth**\n\n"
                text += "Failed to remove Twitter authentication.\n"
                text += "Please try again or contact support."
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error removing Twitter auth: {e}")
            text = "❌ An error occurred while removing Twitter authentication."
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)

    
    async def handle_twitter_auth_complete(self, chat_id, user_id):
        """Handle Twitter authentication completion"""
        # Check if user has Twitter authentication data
        twitter_auth = self.firebase.check_twitter_auth(user_id)
        
        if twitter_auth:
            # User is authenticated
            username = twitter_auth.get('twitterUsername', 'Unknown')
            text = f"✅ **Twitter Authentication Successful!**\n\n"
            text += f"🐦 **Username:** @{username}\n"
            text += f"🔗 **Status:** Connected\n"
            text += f"📱 **Features:** Trading alerts, market updates, and more!\n\n"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            await self.send_message(chat_id, text, keyboard)
        else:
            # No authentication data found
            text = "❌ **Twitter Authentication Not Found**\n\n"
            text += "It seems like you haven't completed the Twitter authentication process yet.\n\n"
            text += "Please:\n"
            text += "1. Click the authentication link\n"
            text += "2. Complete the Twitter OAuth process\n"
            text += "3. Return here and click 'Complete' again\n\n"
            text += "If you're having issues, please try the authentication process again."
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Twitter Auth', 'callback_data': 'twitter_auth'}
            ]])
            await self.send_message(chat_id, text, keyboard)
    
    async def save_twitter_auth_data(self, chat_id, user_id, callback_data):
        """Save Twitter authentication data from frontend"""
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
                    text = f"✅ **Twitter Authentication Successfully!**\n\n"
                    text += f"🐦 **Username:** @{twitter_username}\n"
                    text += f"🔗 **Status:** Connected\n\n"
                    text += f"Your Twitter account is now connected to the bot!"
                    
                    keyboard = self.create_inline_keyboard([[
                        {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                    ]])
                    await self.send_message(chat_id, text, keyboard)
                else:
                    text = "❌ **Failed to Save Twitter Authentication**\n\n"
                    text += "There was an error saving your Twitter authentication data.\n\n"
                    text += "Please try again or contact support if the issue persists."
                    
                    keyboard = self.create_inline_keyboard([[
                        {'text': '🔙 Back to Twitter Auth', 'callback_data': 'twitter_auth'}
                    ]])
                    await self.send_message(chat_id, text, keyboard)
            else:
                text = "❌ **Invalid Authentication Data**\n\n"
                text += "The authentication data received is incomplete.\n\n"
                text += "Please try the authentication process again."
                
                keyboard = self.create_inline_keyboard([[
                    {'text': '🔙 Back to Twitter Auth', 'callback_data': 'twitter_auth'}
                ]])
                await self.send_message(chat_id, text, keyboard)
                
        except Exception as e:
            logger.error(f"Error saving Twitter auth data: {e}")
            text = "❌ **Error Saving Authentication**\n\n"
            text += "There was an error processing your Twitter authentication.\n\n"
            text += "Please try again or contact support if the issue persists."
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Twitter Auth', 'callback_data': 'twitter_auth'}
            ]])
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_create_wallet(self, chat_id, user_id):
        """Handle wallet creation"""
        try:
            # Create new wallet
            wallet_data = self.blockchain.create_wallet()
            logger.info(f"Wallet created: {wallet_data['public_key'][:20]}...")
            
            # Save to database
            username = "demo_user"
            
            success = self.firebase.save_user_wallet(
                user_id, username, wallet_data['public_key'], 
                wallet_data['private_key'], "created"
            )
            
            if success:
                text = f"✅ Generated new wallet:\n\n"
                text += f"Address: {wallet_data['public_key']}\n"
                text += f"Private Key: {wallet_data['private_key']}\n\n"
                text += f"⚠️ Make sure to save this mnemonic phrase OR private key using pen and paper only. Do NOT copy-paste it anywhere. You could also import it to your Metamask/Trust Wallet. After you finish saving/importing the wallet credentials, delete this message. "
                
                keyboard = self.create_inline_keyboard([[
                    {'text': '🔙 Back to Wallet', 'callback_data': 'wallet'}
                ]])
                
                await self.send_message(chat_id, text, keyboard)
            else:
                await self.send_message(chat_id, "❌ Failed to create wallet. Please try again.")
                
        except Exception as e:
            logger.error(f"Error creating wallet: {e}")
            await self.send_message(chat_id, f"❌ An error occurred: {str(e)}")
    
    async def handle_import_wallet(self, chat_id, user_id):
        """Handle wallet import"""
        text = "📥 **Import Existing Wallet**\n\n"
        text += "⚠️ **SECURITY WARNING:**\n"
        text += "• Never share your private key with anyone\n"
        text += "• This bot encrypts your key before storage\n"
        text += "• Only you can access your funds\n\n"
        text += "📝 **To import your wallet:**\n"
        text += "1. Get your private key from your wallet\n"
        text += "2. Send it as a message (64 characters)\n"
        text += "3. The bot will encrypt and store it securely\n\n"
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '🔙 Back to Wallet', 'callback_data': 'wallet'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_private_key_input(self, chat_id, user_id, private_key):
        """Handle private key input for wallet import"""
        try:
            username = "demo_user"
            
            # Validate private key
            if not self.encryption.validate_private_key(private_key):
                await self.send_message(chat_id, "❌ Invalid private key format. Please enter a valid 64-character hexadecimal key.")
                return
            
            # Get public address from private key
            public_key = self.blockchain.validate_private_key(private_key)
            if not public_key:
                await self.send_message(chat_id, "❌ Invalid private key. Could not derive public address.")
                return
            
            # Save to database
            success = self.firebase.save_user_wallet(
                user_id, username, public_key, private_key, "imported"
            )
            
            if success:
                text = f"✅ Wallet imported successfully:\n\n"
                text += f"Address: {public_key}\n"
                text += f"Private Key: {private_key}\n\n"
                text += f"⚠️ Make sure to save this mnemonic phrase OR private key using pen and paper only. Do NOT copy-paste it anywhere. You could also import it to your Metamask/Trust Wallet. After you finish saving/importing the wallet credentials, delete this message. "
                
                keyboard = self.create_inline_keyboard([[
                    {'text': '🔙 Back to Wallet', 'callback_data': 'wallet'}
                ]])
                
                await self.send_message(chat_id, text, keyboard)
            else:
                await self.send_message(chat_id, "❌ Failed to import wallet. Please try again.")
                
        except Exception as e:
            logger.error(f"Error importing wallet: {e}")
            await self.send_message(chat_id, f"❌ An error occurred: {str(e)}")
    
    async def handle_show_private_key(self, chat_id, user_id):
        """Handle showing private key"""
        
        if not self.firebase.user_has_wallet(user_id):
            await self.send_message(chat_id, "❌ You don't have a wallet.")
            return
        
        # Get private key
        private_key = self.firebase.get_private_key(user_id)
        if private_key:
            text = f"🔑 **PRIVATE KEY**\n\n"
            text += f"⚠️ **SECURITY WARNING:**\n"
            text += f"• This is extremely sensitive information!\n"
            text += f"• Copy it and delete this message immediately\n"
            text += f"• Never share it with anyone!\n\n"
            text += f"**Private Key:** `{private_key}`\n\n"
            text += f"💡 **Tip:** Store this securely offline!"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Wallet', 'callback_data': 'wallet'}
            ]])
            
            await self.send_message(chat_id, text, keyboard)
        else:
            await self.send_message(chat_id, "❌ Could not retrieve private key.")
    
    async def handle_delete_wallet(self, chat_id, user_id):
        """Handle wallet deletion"""
        
        if not self.firebase.user_has_wallet(user_id):
            await self.send_message(chat_id, "❌ You don't have a wallet.")
            return
        
        # Delete wallet
        success = self.firebase.delete_user_wallet(user_id)
        if success:
            text = "✅ **Wallet Deleted Successfully!**\n\n"
            text += f"🗑️ Your wallet has been removed from the database.\n\n"
            text += f"⚠️ **Important:**\n"
            text += f"• Your funds are still on the blockchain\n"
            text += f"• You can re-import with your private key\n"
            text += f"• Make sure you have a backup of your private key!"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔐 Create New Wallet', 'callback_data': 'create_wallet'}
            ],[{'text': '📥 Import wallet', 'callback_data': 'import_wallet'}],[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            
            await self.send_message(chat_id, text, keyboard)
        else:
            await self.send_message(chat_id, "❌ Failed to delete wallet. Please try again.")
    
    async def process_token_address(self, chat_id, token_address, user_id):
        """Process token address input"""

        # Check if this is for token scanning
        if chat_id in self.trading_state and self.trading_state[chat_id].get('action') == 'scan_token':
            await self.scan_token_address(chat_id, token_address)
            return
        
        # Check if this is for contract balance checking
        if chat_id in self.trading_state and self.trading_state[chat_id].get('action') == 'check_contract':
            # For contract checking, we need to know which chain to use
            # We'll ask the user to select a chain first
            text = "🔍 Check Contract Balance\n\n"
            text += f"📍 **Contract:** `{token_address[:10]}...`\n\n"
            text += "🌐 **Select the blockchain network:**\n\n"
            text += "Choose the network where this token contract exists:"
            
            # Store the contract address for later use
            self.trading_state[chat_id]['contract_address'] = token_address
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔵 ETH', 'callback_data': 'check_contract_eth'},
                    {'text': '🟡 BSC', 'callback_data': 'check_contract_bsc'}
                ],
                [
                    {'text': '🔙 Back to Positions', 'callback_data': 'positions'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            return
        
        # Check if this is for transfer native (recipient address)
        if chat_id in self.trading_state and self.trading_state[chat_id].get('action') == 'transfer_native':
            # Validate recipient address
            if not self.transfer_manager.validate_address(token_address):
                await self.send_message(chat_id, "❌ Invalid recipient address. Please check the format.")
                return
            
            # Store recipient address
            self.trading_state[chat_id]['recipient_address'] = token_address
            
            # Ask for amount
            chain = self.trading_state[chat_id]['chain']
            native_symbol = self.transfer_manager.get_native_symbol(chain)
            
            text = f"💸 Transfer {native_symbol}\n\n"
            text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
            text += f"💰 **Token:** {native_symbol}\n"
            text += f"📍 **To:** `{token_address[:10]}...{token_address[-10:]}`\n\n"
            text += f"💸 **Enter the amount to transfer:**\n\n"
            text += f"💡 **Example:** 0.1, 0.5, 1.0\n\n"
            text += f"🔧 **Just type the amount below:**"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            return
        
        # Check if this is for transfer token (token contract address)
        if chat_id in self.trading_state and self.trading_state[chat_id].get('action') == 'transfer_token':
            # Check if we already have a token contract address
            if 'token_contract' not in self.trading_state[chat_id]:
                # This is the first step - asking for token contract address
                # Validate token contract address
                if not self.transfer_manager.validate_address(token_address):
                    await self.send_message(chat_id, "❌ Invalid token contract address. Please check the format.")
                    return
                
                # Store token contract address
                self.trading_state[chat_id]['token_contract'] = token_address
                
                # Ask for recipient address
                chain = self.trading_state[chat_id]['chain']
                
                text = f"🪙 Transfer Token\n\n"
                text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                text += f"🪙 **Contract:** `{token_address[:10]}...{token_address[-10:]}`\n\n"
                text += f"📝 **Enter the recipient address:**\n\n"
                text += f"💡 Format: 0x followed by 40 characters\n"
                text += f"Example: 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5\n\n"
                text += f"🔧 **Just type the recipient address below:**"
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                    ]
                ])
                
                await self.send_message(chat_id, text, keyboard)
                return
            else:
                # This is the second step - asking for recipient address
                # Validate recipient address
                if not self.transfer_manager.validate_address(token_address):
                    await self.send_message(chat_id, "❌ Invalid recipient address. Please check the format.")
                    return
                
                # Store recipient address
                self.trading_state[chat_id]['recipient_address'] = token_address
                
                # Change action to amount input
                self.trading_state[chat_id]['action'] = 'transfer_token_amount'
                
                # Ask for amount
                chain = self.trading_state[chat_id]['chain']
                token_contract = self.trading_state[chat_id]['token_contract']
                
                text = f"🪙 Transfer Token\n\n"
                text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                text += f"🪙 **Contract:** `{token_contract[:10]}...{token_contract[-10:]}`\n"
                text += f"📍 **To:** `{token_address[:10]}...{token_address[-10:]}`\n\n"
                text += f"💸 **Enter the amount to transfer:**\n\n"
                text += f"💡 **Example:** 100, 1000, 5000\n\n"
                text += f"🔧 **Just type the amount below:**"
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                    ]
                ])
                
                await self.send_message(chat_id, text, keyboard)
                return
        
        # Handle trading flow
        if chat_id not in self.trading_state:
            await self.send_message(chat_id, "❌ Please select Buy or Sell first.")
            return
        
        # Check if trading state has required fields
        if 'action' not in self.trading_state[chat_id] or 'chain' not in self.trading_state[chat_id]:
            logger.error(f"Trading state incomplete for chat {chat_id}: {self.trading_state[chat_id]}")
            await self.send_message(chat_id, "❌ Trading state incomplete. Please restart the trading process.")
            # Clear the incomplete state
            del self.trading_state[chat_id]
            return
        
        # Validate token address
        chain = self.trading_state[chat_id]['chain']
        if not self.trading.validate_token_address(chain, token_address):
            await self.send_message(chat_id, "❌ Invalid token address. Please check the format.")
            return
        
        # Store token address and user_id
        self.trading_state[chat_id]['token'] = token_address
        self.trading_state[chat_id]['user_id'] = user_id
        
        action = self.trading_state[chat_id]['action']
        
        # Get chain info
        chain_info = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'dex': 'Uniswap V2'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'dex': 'PancakeSwap v2'
            },
            'SEPOLIA': {
                'name': 'Sepolia Testnet',
                'symbol': 'ETH',
                'dex': 'Uniswap V2'
            }
        }
        
        chain_data = chain_info.get(chain, chain_info['BSC'])
        
        # Get detailed token information using scanner
        try:
            # Scan the token to get detailed information
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
                
                # Get tax information
                buy_tax = scan_result.get('buy_tax', 0)
                sell_tax = scan_result.get('sell_tax', 0)
                transfer_tax = scan_result.get('transfer_tax', 0)
                
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
                user_id = self.trading_state[chat_id].get('user_id')
                wallet_balance = 0
                native_balance = 0
                
                if user_id:
                    try:
                        # Get wallet address
                        wallet_data = self.firebase.get_user_wallet(user_id)
                        logger.info(f"Wallet data for user {user_id}: {wallet_data}")
                        
                        if wallet_data:
                            wallet_address = wallet_data['public_key']
                            logger.info(f"Getting balance for wallet: {wallet_address}")
                            
                            # Get token balance using direct contract call
                            wallet_balance = await self._get_token_balance_contract_call(chain, wallet_address, token_address)
                            logger.info(f"Token balance (contract call): {wallet_balance}")
                            
                            # Get native balance using direct Web3 call
                            native_balance = await self._get_native_balance_contract_call(chain, wallet_address)
                            logger.info(f"Native balance (contract call): {native_balance}")
                        else:
                            logger.warning(f"No wallet data found for user {user_id}")
                            # Try to get balance using blockchain manager as fallback
                            try:
                                wallet_balance = 0
                                native_balance = 0
                                logger.info("Attempting fallback balance retrieval...")
                            except Exception as fallback_error:
                                logger.error(f"Fallback balance retrieval failed: {fallback_error}")
                    except Exception as e:
                        logger.error(f"Error getting wallet balance: {e}")
                        wallet_balance = 0
                        native_balance = 0
                else:
                    logger.warning(f"No user_id found in trading state for chat {chat_id}")
                    wallet_balance = 0
                    native_balance = 0
                
                # Build detailed token information
                text = f"🪙 {token_name} (${token_symbol})\n"
                text += f"{token_address}\n"
                text += f"V2 Pool 🔗 {chain}\n\n"
                
                text += f"⛽ {chain} | 0.1 GWEI  Ξ $0.0₆1\n\n"
                
                text += f"🧢 MC ${fdv:,.0f} | 💵 Price {price_usd_str}\n"
                text += f"⚖️ Taxes | 🅑 {buy_tax:.1f}% 🅢 {sell_tax:.1f}% 🅣 {transfer_tax:.1f}%\n"
                liquidity_percentage = (liquidity_usd/fdv*100) if fdv and fdv > 0 else 0
                text += f"💧 Liquidity | ${liquidity_usd:,.0f} ({liquidity_percentage:.2f}%)\n"
                text += f"🕓 Refresh | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                text += f"💰 Balance\n"
                text += f" {token_symbol}   | {chain_data['symbol']}\n"
                text += f" {wallet_balance:.6f} | {native_balance:.6f}\n\n"
                
                if fdv and fdv > 0 and liquidity_usd/fdv < 0.01:
                    text += f"🚨 Liquidity / Total Supply < 1%\n\n"
                
                if action == 'buy':
                    text += f"Enter Amount ({chain_data['symbol']}):"
                    
                    # Create quick amount buttons for buy action
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                else:  # sell
                    text += f"Enter Amount ({token_symbol}):"
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                    
            else:
                # Fallback to simple format if scanning fails
                text = f"✅ Token Address Valid!\n\n"
                text += f"🔑 Token: `{token_address[:20]}...`\n"
                text += f"🌐 Network: {chain_data['name']}\n"
                text += f"🔄 DEX: {chain_data['dex']}\n\n"
                
                if action == 'buy':
                    text += f"💰 Step 2: Enter the amount of {chain_data['symbol']} to spend\n\n"
                    text += f"💡 Example: 0.1, 0.5, 1.0\n\n"
                    text += f"🔧 Just type the amount below:"
                    
                    # Create quick amount buttons for buy action (fallback)
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                else:  # sell
                    text += f"💰 Step 2: Enter the amount of tokens to sell\n\n"
                    text += f"💡 Example: 100, 1000, 5000\n\n"
                    text += f"🔧 Just type the amount below:"
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                    
        except Exception as e:
            logger.error(f"Error scanning token: {e}")
            # Fallback to simple format
            text = f"✅ Token Address Valid!\n\n"
            text += f"🔑 Token: `{token_address[:20]}...`\n"
            text += f"🌐 Network: {chain_data['name']}\n"
            text += f"🔄 DEX: {chain_data['dex']}\n\n"
            
            if action == 'buy':
                text += f"💰 Step 2: Enter the amount of {chain_data['symbol']} to spend\n\n"
                text += f"💡 Example: 0.1, 0.5, 1.0\n\n"
                text += f"🔧 Just type the amount below:"
                
                # Create quick amount buttons for buy action (exception fallback)
                keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
            else:  # sell
                text += f"💰 Step 2: Enter the amount of tokens to sell\n\n"
                text += f"💡 Example: 100, 1000, 5000\n\n"
                text += f"🔧 Just type the amount below:"
                keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
        
        # Use the keyboard created above, or fallback to back button
        if 'keyboard' not in locals():
            keyboard = self._create_back_button_keyboard()
        
        await self.send_message(chat_id, text, keyboard)
    
    async def scan_token_address(self, chat_id, token_address):
        """Scan a token address using DexView API"""
        try:
            # Get the selected chain from trading state
            chain = self.trading_state[chat_id].get('chain', 'BSC')
            
            # Show scanning message
            scanning_text = f"🔍 **Scanning Token...**\n\n"
            scanning_text += f"📍 **Address:** `{token_address}`\n"
            scanning_text += f"🌐 **Chain:** {chain}\n"
            scanning_text += f"⏳ **Status:** Fetching token data..."
            
            await self.send_message(chat_id, scanning_text)
            
            # Scan the token
            result = await self.token_scanner.scan_token(token_address, chain)
            
            if result and "error" not in result:
                # Format and display the result
                formatted_result = self.token_scanner.format_scan_result(result)
                
                # Store scan result for refresh functionality
                self.last_scan_results[chat_id] = {
                    'result': result,
                    'token_address': token_address,
                    'chain': chain
                }
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '💰 Buy/Sell', 'callback_data': f'select_chain_{chain.lower()}'}
                    ],
                   
                    [
                        {'text': '📋 Copy Address', 'callback_data': f'copy_address_{token_address}'},
                        {'text': '🔄 Refresh', 'callback_data': f'refresh_scan_{token_address}'}
                    ],
                    [
                        {'text': '🔍 Scan Another', 'callback_data': 'scanner'},
                        {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                    ]
                ])
                
                await self.send_message(chat_id, formatted_result, keyboard)
                
                # Clear the trading state for this chat
                if chat_id in self.trading_state:
                    del self.trading_state[chat_id]
                    
            else:
                error_text = f"❌ **Token Scan Failed**\n\n"
                if result and "error" in result:
                    error_text += f"**Error:** {result['error']}\n\n"
                else:
                    error_text += f"**Error:** Failed to scan token\n\n"
                error_text += f"💡 **Possible reasons:**\n"
                error_text += f"• Token doesn't exist on {chain} chain\n"
                error_text += f"• Invalid contract address\n"
                error_text += f"• API temporarily unavailable\n\n"
                error_text += f"🔍 **Try again with a different address or chain**"
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '🔄 Try Again', 'callback_data': 'scanner'},
                        {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                    ]
                ])
                
                await self.send_message(chat_id, error_text, keyboard)
                
                # Clear the trading state for this chat
                if chat_id in self.trading_state:
                    del self.trading_state[chat_id]
                    
        except Exception as e:
            error_text = f"❌ **Token Scan Error**\n\n"
            error_text += f"**Error:** {str(e)}\n\n"
            error_text += f"🔧 **Technical Issue:** Please try again later"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            
            await self.send_message(chat_id, error_text, keyboard)
            
            # Clear the trading state for this chat
            if chat_id in self.trading_state:
                del self.trading_state[chat_id]
    
    async def handle_copy_address(self, chat_id, callback_data):
        """Handle copy address button click"""
        try:
            # Extract token address from callback data
            token_address = callback_data.replace('copy_address_', '')
            
            if token_address:
                # Show the address in a message for easy copying
                text = f"📋 **Token Address**\n\n"
                text += f"```\n{token_address}\n```\n\n"
                text += f"✅ **Address copied to message above. You can copy it manually.**"
                
                keyboard = self.create_inline_keyboard([[
                    {'text': '🔙 Back to Scanner', 'callback_data': 'scanner'}
                ]])
                
                await self.send_message(chat_id, text, keyboard)
            else:
                await self.send_message(chat_id, "❌ No token address found to copy.")
                
        except Exception as e:
            await self.send_message(chat_id, f"❌ Error copying address: {str(e)}")
    
    async def handle_refresh_scan(self, chat_id, callback_data):
        """Handle refresh scan button click"""
        try:
            # Extract token address from callback data
            token_address = callback_data.replace('refresh_scan_', '')
            
            # Get stored scan data
            if chat_id not in self.last_scan_results:
                await self.send_message(chat_id, "❌ No previous scan found to refresh. Please scan a token first.")
                return
            
            scan_data = self.last_scan_results[chat_id]
            chain = scan_data['chain']
            
            # Show refreshing message
            refreshing_text = f"🔄 **Refreshing Token Data...**\n\n"
            refreshing_text += f"📍 **Address:** `{token_address}`\n"
            refreshing_text += f"🌐 **Chain:** {chain}\n"
            refreshing_text += f"⏳ **Status:** Fetching updated data..."
            
            await self.send_message(chat_id, refreshing_text)
            
            # Perform fresh token scan
            result = await self.token_scanner.scan_token(token_address, chain)
            
            if result and "error" not in result:
                # Update stored scan result
                self.last_scan_results[chat_id] = {
                    'result': result,
                    'token_address': token_address,
                    'chain': chain
                }
                
                # Format and display refreshed result
                formatted_result = self.token_scanner.format_scan_result(result)
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '💰 Buy/Sell', 'callback_data': f'select_chain_{chain.lower()}'}
                    ],
                    [
                        {'text': '📋 Copy Address', 'callback_data': f'copy_address_{token_address}'},
                        {'text': '🔄 Refresh', 'callback_data': f'refresh_scan_{token_address}'}
                    ],
                    [
                        {'text': '🔍 Scan Another', 'callback_data': 'scanner'},
                        {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                    ]
                    
                ])
                
                await self.send_message(chat_id, formatted_result, keyboard)
                
            else:
                error_text = f"❌ **Refresh Failed**\n\n"
                if result and "error" in result:
                    error_text += f"**Error:** {result['error']}\n\n"
                else:
                    error_text += f"**Error:** Failed to refresh token data\n\n"
                error_text += f"💡 **Possible reasons:**\n"
                error_text += f"• Token data temporarily unavailable\n"
                error_text += f"• API temporarily unavailable\n\n"
                error_text += f"🔍 **Try again later**"
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '🔄 Try Again', 'callback_data': f'refresh_scan_{token_address}'},
                        {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                    ]
                ])
                
                await self.send_message(chat_id, error_text, keyboard)
                
        except Exception as e:
            error_text = f"❌ **Refresh Error**\n\n"
            error_text += f"**Error:** {str(e)}\n\n"
            error_text += f"🔧 **Technical Issue:** Please try again later"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            
            await self.send_message(chat_id, error_text, keyboard)
    
    async def process_amount(self, chat_id, user_id, amount_text):
        """Process amount input"""
        if chat_id not in self.trading_state:
            await self.send_message(chat_id, "❌ Please select Buy or Sell first.")
            return
        
        # Check if this is for transfer
        if chat_id in self.trading_state and self.trading_state[chat_id].get('action') == 'transfer_native':
            # Handle native token transfer amount
            try:
                amount = float(amount_text)
                if amount <= 0:
                    await self.send_message(chat_id, "❌ Amount must be greater than 0.")
                    return
            except ValueError:
                await self.send_message(chat_id, "❌ Invalid amount. Please enter a number.")
                return
            
            # Store amount
            self.trading_state[chat_id]['amount'] = amount
            
            # Show transfer confirmation
            await self.show_transfer_confirmation(chat_id, user_id, 'native', amount)
            return
        
        # Check if this is for token transfer (amount input)
        if chat_id in self.trading_state and self.trading_state[chat_id].get('action') == 'transfer_token_amount':
            # Handle token transfer amount
            try:
                amount = float(amount_text)
                if amount <= 0:
                    await self.send_message(chat_id, "❌ Amount must be greater than 0.")
                    return
            except ValueError:
                await self.send_message(chat_id, "❌ Invalid amount. Please enter a number.")
                return
            
            # Store amount
            self.trading_state[chat_id]['amount'] = amount
            
            # Show transfer confirmation
            await self.show_transfer_confirmation(chat_id, user_id, 'token', amount)
            return
        
        # Check if this is for setting slippage
        if chat_id in self.trading_state and self.trading_state[chat_id].get('action') == 'set_slippage':
            # Handle slippage input
            try:
                slippage_value = float(amount_text)
                if slippage_value < 0.1 or slippage_value > 50.0:
                    await self.send_message(chat_id, "❌ Slippage must be between 0.1% and 50.0%. Please enter a valid value.")
                    return
            except ValueError:
                await self.send_message(chat_id, "❌ Invalid slippage value. Please enter a number (e.g., 0.5, 1.0, 2.0).")
                return
            
            # Store slippage setting for this user
            self.set_user_slippage(chat_id, slippage_value)
            
            # Store slippage setting (you can extend this to save to database)
            # For now, we'll just show confirmation
            
            text = f"✅ **Custom Slippage Set Successfully!**\n\n"
            text += f"📊 **New Setting:** {slippage_value}%\n\n"
            
            if slippage_value <= 0.5:
                text += "💡 **Low Slippage:**\n"
                text += "• Excellent price protection\n"
                text += "• May fail on volatile tokens\n"
                text += "• Best for stable tokens and small trades"
            elif slippage_value <= 1.0:
                text += "💡 **Medium Slippage:**\n"
                text += "• Good price protection\n"
                text += "• Balanced success rate\n"
                text += "• Recommended for most trades"
            elif slippage_value <= 2.0:
                text += "💡 **High Slippage:**\n"
                text += "• Higher success rate\n"
                text += "• Moderate price protection\n"
                text += "• Good for volatile tokens"
            else:
                text += "💡 **Very High Slippage:**\n"
                text += "• Maximum success rate\n"
                text += "• Lower price protection\n"
                text += "• Use for very volatile tokens or urgent trades"
            
            text += f"\n💾 **Note:** This setting will be used for all future trades."
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔙 Back to Slippage', 'callback_data': 'settings_slippage'},
                    {'text': '⚙️ Settings', 'callback_data': 'settings'}
                ]
            ])
            
            # Clear the trading state
            if chat_id in self.trading_state:
                del self.trading_state[chat_id]
            
            await self.send_message(chat_id, text, keyboard)
            return
        
        if 'token' not in self.trading_state[chat_id] and 'token_address' not in self.trading_state[chat_id]:
            await self.send_message(chat_id, "❌ Please enter token address first.")
            return
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                await self.send_message(chat_id, "❌ Amount must be greater than 0.")
                return
        except ValueError:
            await self.send_message(chat_id, "❌ Invalid amount. Please enter a number.")
            return
        
        # Store amount
        self.trading_state[chat_id]['amount'] = amount
        
        # Show transaction overview instead of immediately executing
        action = self.trading_state[chat_id]['action']
        token_address = self.trading_state[chat_id].get('token') or self.trading_state[chat_id].get('token_address')
        
        if action == 'buy':
            await self.show_buy_overview(chat_id, user_id, token_address, amount)
        else:  # sell
            await self.show_sell_overview(chat_id, user_id, token_address, amount)
    
    async def show_buy_overview(self, chat_id, user_id, token_address, bnb_amount):
        """Show buy transaction overview with calculations"""
        
        if not self.firebase.user_has_wallet(user_id):
            await self.send_message(chat_id, "❌ You don't have a wallet.")
            return
        
        wallet = self.firebase.get_user_wallet(user_id)
        
        # Get price estimate and security info
        chain = self.trading_state[chat_id].get('chain', 'BSC')
        price_estimate = self.trading.get_token_price_estimate(
            chain, 
            token_address, 
            bnb_amount
        )
        
        if not price_estimate:
            await self.send_message(chat_id, "❌ Could not get price estimate.")
            return
        
        # Get tax information from token scanner
        security_info = await self.token_scanner.get_token_security_info(token_address, chain)
        buy_tax = security_info.get('buy_tax', 0) if security_info and 'error' not in security_info else 0
        sell_tax = security_info.get('sell_tax', 0) if security_info and 'error' not in security_info else 0
        transfer_tax = security_info.get('transfer_tax', 0) if security_info and 'error' not in security_info else 0
        
        # Calculate fees and totals
        gas_estimate = 0.005  # Estimated gas in BNB
        total_bnb = bnb_amount + gas_estimate
        token_amount = price_estimate['token_amount']
        
        # Calculate price per token
        price_per_token = bnb_amount / token_amount if token_amount > 0 else 0
        
        # Get chain info for display
        chain_info = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'dex': 'Uniswap V2'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'dex': 'PancakeSwap v2'
            },
            'SEPOLIA': {
                'name': 'Sepolia Testnet',
                'symbol': 'ETH',
                'dex': 'Uniswap V2'
            }
        }
        chain_data = chain_info.get(chain, chain_info['BSC'])
        
        text = f"🟢 **BUY TRANSACTION OVERVIEW**\n\n"
        text += f"🔑 **Token:** `{token_address[:20]}...`\n"
        text += f"🌐 Network: {chain_data['name']}\n"
        text += f"🔄 **DEX:** {chain_data['dex']}\n\n"
        text += f"💰 **Transaction Details:**\n"
        native_symbol = 'ETH' if chain == 'ETH' else 'BNB'

        text += f"• **{native_symbol} Amount:** {bnb_amount:.6f} {native_symbol}\n"
        text += f"• **Estimated Gas:** {gas_estimate:.6f} {native_symbol}\n"
        text += f"• **Total Cost:** {total_bnb:.6f} {native_symbol}\n\n"
        text += f"🪙 **Token Details:**\n"
        text += f"• **Tokens to Receive:** {token_amount:.6f}\n"
        text += f"• **Price per Token:** {price_per_token:.8f} {native_symbol}\n"
        text += f"• **Slippage:** {self.get_user_slippage(chat_id)}%\n\n"
        text += f"📊 **Price Impact:** Low\n"
        text += f"⏱️ **Estimated Time:** 30-60 seconds\n\n"
        text += f"⚠️ **Please review the details above.**\n"
        text += f"Click 'Confirm Buy' to proceed with the transaction."
        
        # Store transaction data for confirmation
        self.trading_state[chat_id]['price_estimate'] = price_estimate
        self.trading_state[chat_id]['gas_estimate'] = gas_estimate
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '✅ Confirm Buy', 'callback_data': 'confirm_buy'},
                {'text': '❌ Cancel', 'callback_data': 'buy_sell'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def show_sell_overview(self, chat_id, user_id, token_address, token_amount):
        """Show sell transaction overview with calculations"""
        
        if not self.firebase.user_has_wallet(user_id):
            await self.send_message(chat_id, "❌ You don't have a wallet.")
            return
        
        wallet = self.firebase.get_user_wallet(user_id)
        
        # Determine native symbol and get price estimate for selling via router
        chain = self.trading_state[chat_id].get('chain', 'BSC')
        native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
        sell_estimate = self.trading.get_token_sell_estimate(chain, token_address, token_amount)
        estimated_bnb = sell_estimate['native_out'] if sell_estimate else 0.0
        
        # Get tax information from token scanner
        security_info = await self.token_scanner.get_token_security_info(token_address, chain)
        buy_tax = security_info.get('buy_tax', 0) if security_info and 'error' not in security_info else 0
        sell_tax = security_info.get('sell_tax', 0) if security_info and 'error' not in security_info else 0
        transfer_tax = security_info.get('transfer_tax', 0) if security_info and 'error' not in security_info else 0
        
        # Calculate fees and totals (keep simple estimate for display)
        gas_estimate = 0.005
        net_bnb = max(estimated_bnb - gas_estimate, 0)
        
        # Calculate price per token
        price_per_token = (estimated_bnb / token_amount) if token_amount > 0 else 0
        
        # Get chain info for display
        chain_info = {
            'ETH': {
                'name': 'Ethereum Mainnet',
                'symbol': 'ETH',
                'dex': 'Uniswap V2'
            },
            'BSC': {
                'name': 'BSC Mainnet',
                'symbol': 'BNB',
                'dex': 'PancakeSwap v2'
            },
            'SEPOLIA': {
                'name': 'Sepolia Testnet',
                'symbol': 'ETH',
                'dex': 'Uniswap V2'
            }
        }
        chain_data = chain_info.get(chain, chain_info['BSC'])
        
        text = f"🔴 **SELL TRANSACTION OVERVIEW**\n\n"
        text += f"🔑 **Token:** `{token_address[:20]}...`\n"
        text += f"🌐 Network: {chain_data['name']}\n"
        text += f"🔄 **DEX:** {chain_data['dex']}\n\n"
        text += f"🪙 **Transaction Details:**\n"
        text += f"• **Token Amount:** {token_amount:.2f}\n"
        native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
        text += f"• **Estimated {native_symbol}:** {estimated_bnb:.6f} {native_symbol}\n"
        text += f"• **Gas Fee:** {gas_estimate:.6f} {native_symbol}\n"
        text += f"• **Net {native_symbol}:** {net_bnb:.6f} {native_symbol}\n\n"
        text += f"💰 **Price Details:**\n"
        text += f"• **Price per Token:** {price_per_token:.8f} {native_symbol}\n"
        text += f"• **Slippage:** {self.get_user_slippage(chat_id)}%\n\n"
        text += f"📊 **Price Impact:** Low\n"
        text += f"⏱️ **Estimated Time:** 30-60 seconds\n\n"
        text += f"⚠️ **Please review the details above.**\n"
        text += f"Click 'Confirm Sell' to proceed with the transaction."
        
        # Store transaction data for confirmation
        self.trading_state[chat_id]['estimated_bnb'] = estimated_bnb
        self.trading_state[chat_id]['gas_estimate'] = gas_estimate
        
        keyboard = self.create_inline_keyboard([
            [
                {'text': '✅ Confirm Sell', 'callback_data': 'confirm_sell'},
                {'text': '❌ Cancel', 'callback_data': 'buy_sell'}
            ]
        ])
        
        await self.send_message(chat_id, text, keyboard)
    
    async def handle_confirm_buy(self, chat_id, user_id):
        """Handle buy confirmation"""
        if chat_id not in self.trading_state:
            await self.send_message(chat_id, "❌ No pending transaction found.")
            return
        
        tx_data = self.trading_state[chat_id]
        token_address = tx_data.get('token') or tx_data.get('token_address')
        if 'amount' not in tx_data or not token_address:
            await self.send_message(chat_id, "❌ Incomplete transaction data.")
            return
        
        # Execute the buy transaction
        await self.execute_buy(chat_id, user_id, token_address, tx_data['amount'])
    
    async def handle_confirm_sell(self, chat_id, user_id):
        """Handle sell confirmation"""
        if chat_id not in self.trading_state:
            await self.send_message(chat_id, "❌ No pending transaction found.")
            return
        
        tx_data = self.trading_state[chat_id]
        token_address = tx_data.get('token') or tx_data.get('token_address')
        if 'amount' not in tx_data or not token_address:
            await self.send_message(chat_id, "❌ Incomplete transaction data.")
            return
        
        # Execute the sell transaction
        await self.execute_sell(chat_id, user_id, token_address, tx_data['amount'])
    
    async def show_transfer_confirmation(self, chat_id, user_id, transfer_type, amount):
        """Show transfer confirmation"""
        try:
            if not self.firebase.user_has_wallet(user_id):
                await self.send_message(chat_id, "❌ You don't have a wallet.")
                return
            
            wallet = self.firebase.get_user_wallet(user_id)
            chain = self.trading_state[chat_id]['chain']
            
            if transfer_type == 'native':
                # Native token transfer confirmation
                native_symbol = self.transfer_manager.get_native_symbol(chain)
                recipient_address = self.trading_state[chat_id]['recipient_address']
                
                text = f"💰 **Native {native_symbol} Transfer Confirmation**\n\n"
                text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                text += f"💸 **Amount:** {amount} {native_symbol}\n"
                text += f"📍 **To:** `{recipient_address[:10]}...{recipient_address[-10:]}`\n"
                text += f"🔑 **From:** `{wallet['public_key'][:10]}...{wallet['public_key'][-10:]}`\n\n"
                text += f"⚠️ **Please confirm the transfer details above.**\n"
                text += f"Click 'Confirm Transfer' to proceed."
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '✅ Confirm Transfer', 'callback_data': 'confirm_transfer_native'},
                        {'text': '❌ Cancel', 'callback_data': 'transfer'}
                    ]
                ])
                
            else:
                # Token transfer confirmation
                token_contract = self.trading_state[chat_id]['token_contract']
                recipient_address = self.trading_state[chat_id]['recipient_address']
                
                # Get token info
                token_info = await self.transfer_manager._get_token_info(
                    self.transfer_manager.web3_instances[chain], 
                    token_contract
                )
                
                if not token_info:
                    await self.send_message(chat_id, "❌ Could not get token information.")
                    return
                
                # Format token display - handle incomplete token info
                token_display = token_info['symbol']
                if token_info['name'] and token_info['name'] != "Unknown Token":
                    token_display += f" ({token_info['name']})"
                
                text = f"🪙 **Token Transfer Confirmation**\n\n"
                text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                text += f"🪙 **Token:** {token_display}\n"
                text += f"💸 **Amount:** {amount} {token_info['symbol']}\n"
                text += f"📍 **To:** `{recipient_address[:10]}...{recipient_address[-10:]}`\n"
                text += f"🔑 **From:** `{wallet['public_key'][:10]}...{wallet['public_key'][-10:]}`\n\n"
                text += f"⚠️ **Please confirm the transfer details above.**\n"
                text += f"Click 'Confirm Transfer' to proceed."
                
                keyboard = self.create_inline_keyboard([
                    [
                        {'text': '✅ Confirm Transfer', 'callback_data': 'confirm_transfer_token'},
                        {'text': '❌ Cancel', 'callback_data': 'transfer'}
                    ]
                ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error showing transfer confirmation: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")
    
    async def execute_transfer(self, chat_id, user_id, transfer_type):
        """Execute the transfer transaction"""
        try:
            if not self.firebase.user_has_wallet(user_id):
                await self.send_message(chat_id, "❌ You don't have a wallet.")
                return
            
            wallet = self.firebase.get_user_wallet(user_id)
            private_key = self.firebase.get_private_key(user_id)
            
            if not private_key:
                await self.send_message(chat_id, "❌ Could not retrieve private key.")
                return
            
            chain = self.trading_state[chat_id]['chain']
            amount = self.trading_state[chat_id]['amount']
            
            if transfer_type == 'native':
                # Execute native token transfer
                recipient_address = self.trading_state[chat_id]['recipient_address']
                
                result = await self.transfer_manager.transfer_native_tokens(
                    wallet['public_key'],
                    recipient_address,
                    amount,
                    chain,
                    private_key
                )
                
                if result['success']:
                    text = f"✅ **Native Transfer Successful!**\n\n"
                    text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                    text += f"💸 **Amount:** {amount} {self.transfer_manager.get_native_symbol(chain)}\n"
                    text += f"📍 **To:** `{recipient_address[:10]}...{recipient_address[-10:]}`\n"
                    text += f"📊 **Transaction Hash:** `0x{result['tx_hash']}`\n"
                    text += f"⛽ **Gas Used:** {result['gas_used']}\n\n"
                    text += f"🔍 **View on Explorer:** {result['explorer_url']}"
                    
                    keyboard = self.create_inline_keyboard([[
                        {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                    ]])
                else:
                    text = f"❌ **Native Transfer Failed!**\n\n"
                    text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                    text += f"💸 **Amount:** {amount} {self.transfer_manager.get_native_symbol(chain)}\n"
                    text += f"📍 **To:** `{recipient_address[:10]}...{recipient_address[-10:]}`\n"
                    text += f"❌ **Error:** {result['error']}\n\n"
                    text += f"💡 **Please try again or check your balance.**"
                    
                    keyboard = self.create_inline_keyboard([[
                        {'text': '🔄 Try Again', 'callback_data': 'transfer'},
                        {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                    ]])
                
            else:
                # Execute token transfer
                token_contract = self.trading_state[chat_id]['token_contract']
                recipient_address = self.trading_state[chat_id]['recipient_address']
                
                result = await self.transfer_manager.transfer_erc20_tokens(
                    wallet['public_key'],
                    recipient_address,
                    token_contract,
                    amount,
                    chain,
                    private_key
                )
                
                if result['success']:
                    text = f"✅ **Token Transfer Successful!**\n\n"
                    text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                    text += f"🪙 **Token:** {result['token_symbol']}\n"
                    text += f"💸 **Amount:** {amount} {result['token_symbol']}\n"
                    text += f"📍 **To:** `{recipient_address[:10]}...{recipient_address[-10:]}`\n"
                    text += f"📊 **Transaction Hash:** `0x{result['tx_hash']}`\n"
                    text += f"⛽ **Gas Used:** {result['gas_used']}\n\n"
                    text += f"🔍 **View on Explorer:** {result['explorer_url']}"
                    
                    keyboard = self.create_inline_keyboard([[
                        {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                    ]])
                else:
                    text = f"❌ **Token Transfer Failed!**\n\n"
                    text += f"🌐 Network: {self.transfer_manager.get_chain_display_name(chain)}\n"
                    text += f"🪙 **Token:** {token_contract[:10]}...\n"
                    text += f"💸 **Amount:** {amount}\n"
                    text += f"📍 **To:** `{recipient_address[:10]}...{recipient_address[-10:]}`\n"
                    text += f"❌ **Error:** {result['error']}\n\n"
                    text += f"💡 **Please try again or check your balance.**"
                    
                    keyboard = self.create_inline_keyboard([[
                        {'text': '🔄 Try Again', 'callback_data': 'transfer'},
                        {'text': '🔙 Back to Transfer', 'callback_data': 'transfer'}
                    ]])
            
            # Clear trading state
            if chat_id in self.trading_state:
                del self.trading_state[chat_id]
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error executing transfer: {e}")
            await self.send_message(chat_id, f"❌ Error executing transfer: {str(e)}")
    
    async def execute_buy(self, chat_id, user_id, token_address, bnb_amount):
        """Execute buy transaction"""
        
        if not self.firebase.user_has_wallet(user_id):
            await self.send_message(chat_id, "❌ You don't have a wallet.")
            return
        
        wallet = self.firebase.get_user_wallet(user_id)
        private_key = self.firebase.get_private_key(user_id)
        
        if not private_key:
            await self.send_message(chat_id, "❌ Could not retrieve private key.")
            return
        
        # Get price estimate
        chain = self.trading_state[chat_id].get('chain', 'BSC')
        price_estimate = self.trading.get_token_price_estimate(
            chain, 
            token_address, 
            bnb_amount
        )
        
        if not price_estimate:
            await self.send_message(chat_id, "❌ Could not get price estimate.")
            return
            
        # Execute the buy transaction
        result = self.trading.buy_tokens(
            chain,
            token_address,
            bnb_amount,
            wallet['public_key'],
            private_key,
            slippage=self.get_user_slippage(chat_id)
        )
        
        # Determine native symbol for the selected chain
        native_symbol = 'ETH' if chain == 'ETH' else 'BNB'

        if result['success']:
            # Get token symbol for button text
            token_symbol = 'TOKEN'  # Default fallback
            try:
                scan_result = await self.token_scanner.scan_token(token_address, chain)
                if scan_result and "error" not in scan_result:
                    token_symbol = scan_result.get('token_symbol', 'TOKEN')
            except:
                pass  # Use default if scanning fails
            
            # Store token address and chain for quick actions
            self.trading_state[chat_id] = {
                'chain': chain,
                'token_address': token_address,
                'token_symbol': token_symbol,
                'last_successful_action': 'buy'
            }
            logger.info(f"DEBUG: Stored token address for chat {chat_id}: {token_address}")
            logger.info(f"DEBUG: Trading state after buy success: {self.trading_state[chat_id]}")
            
            text = f"✅ **Buy Transaction Successful!**\n\n"
            
            text += f"🔑 **Token:** `{token_address[:20]}...`\n"
            text += f"💰 **{native_symbol} Spent:** {bnb_amount} {native_symbol}\n"
            text += f"🪙 **Tokens Received:** {price_estimate['token_amount']:.6f}\n"
            text += f"📊 **Transaction Hash:** `0x{result['tx_hash']}`\n"
            text += f"⛽ **Gas Used:** {result['gas_estimate']}\n\n"
            # Get blockchain explorer URL based on chain
            explorer_url = "https://bscscan.com/tx/" if chain == 'BSC' else "https://etherscan.io/tx/"
            tx_hash = result['tx_hash']
            if not tx_hash.startswith('0x'):
                tx_hash = '0x' + tx_hash
            text += f"🔍 **View on Explorer:** {explorer_url}{tx_hash}"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': f'🟢 Buy {token_symbol}', 'callback_data': f'quick_buy_{chain}'},
                    {'text': f'🔴 Sell {token_symbol}', 'callback_data': f'quick_sell_{chain}'}
                ],
                [
                    {'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}
                ]
            ])
        else:
            text = f"❌ **Buy Transaction Failed!**\n\n"
            text += f"🔑 **Token:** `{token_address[:20]}...`\n"
            text += f"💰 **{native_symbol} Amount:** {bnb_amount} {native_symbol}\n"
            text += f"❌ **Error:** {result['error']}\n\n"
            text += f"💡 **Try again or check your balance.**"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔄 Try Again', 'callback_data': 'buy'},
                {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
            ]])
            
            # Clear trading state only for failed transactions
            if chat_id in self.trading_state:
                del self.trading_state[chat_id]
        
        await self.send_message(chat_id, text, keyboard)
    
    async def execute_sell(self, chat_id, user_id, token_address, token_amount):
        """Execute sell transaction"""
        
        if not self.firebase.user_has_wallet(user_id):
            await self.send_message(chat_id, "❌ You don't have a wallet.")
            return
            
        wallet = self.firebase.get_user_wallet(user_id)
        private_key = self.firebase.get_private_key(user_id)
        
        if not private_key:
            await self.send_message(chat_id, "❌ Could not retrieve private key.")
            return
        
        # Execute the sell transaction
        chain = self.trading_state[chat_id].get('chain', 'BSC')
        native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
        result = self.trading.sell_tokens(
            chain,
            token_address,
            token_amount,
            wallet['public_key'],
            private_key,
            slippage=self.get_user_slippage(chat_id)
        )
        
        if result['success']:
            # Get token symbol for button text
            token_symbol = 'TOKEN'  # Default fallback
            try:
                scan_result = await self.token_scanner.scan_token(token_address, chain)
                if scan_result and "error" not in scan_result:
                    token_symbol = scan_result.get('token_symbol', 'TOKEN')
            except:
                pass  # Use default if scanning fails
            
            # Store token address and chain for quick actions
            self.trading_state[chat_id] = {
                'chain': chain,
                'token_address': token_address,
                'token_symbol': token_symbol,
                'last_successful_action': 'sell'
            }
            logger.info(f"DEBUG: Stored token address for chat {chat_id}: {token_address}")
            logger.info(f"DEBUG: Trading state after sell success: {self.trading_state[chat_id]}")
            
            text = f"✅ **Sell Transaction Successful!**\n\n"
            text += f"🔑 **Token:** `{token_address[:20]}...`\n"
            text += f"🪙 **Tokens Sold:** {token_amount}\n"
            # text += f"💰 **{native_symbol} Received:** Calculating...\n"
            text += f"📊 **Transaction Hash:** `0x{result['tx_hash']}`\n"
            text += f"⛽ **Gas Used:** {result['gas_estimate']}\n\n"
            # Get blockchain explorer URL based on chain
            explorer_url = "https://bscscan.com/tx/" if chain == 'BSC' else "https://etherscan.io/tx/"
            tx_hash = result['tx_hash']
            if not tx_hash.startswith('0x'):
                tx_hash = '0x' + tx_hash
            text += f"🔍 **View on Explorer:** {explorer_url}{tx_hash}"
        
            keyboard = self.create_inline_keyboard([
                [
                    {'text': f'🟢 Buy {token_symbol}', 'callback_data': f'quick_buy_{chain}'},
                    {'text': f'🔴 Sell {token_symbol}', 'callback_data': f'quick_sell_{chain}'}
                ],
                [
                    {'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}
                ]
            ])
        else:
            text = f"❌ **Sell Transaction Failed!**\n\n"
            text += f"🔑 **Token:** `{token_address[:20]}...`\n"
            text += f"🪙 **Token Amount:** {token_amount}\n"
            text += f"❌ **Error:** {result['error']}\n\n"
            text += f"💡 **Try again or check your token balance.**"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔄 Try Again', 'callback_data': 'sell'},
                {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
            ]])
            
            # Clear trading state only for failed transactions
            if chat_id in self.trading_state:
                del self.trading_state[chat_id]
        
        await self.send_message(chat_id, text, keyboard)
    
    # ==================== QUICK TRADING COMMANDS ====================
    
    async def handle_quick_buy_command(self, chat_id, user_id, chain):
        """Handle quick buy commands like /buybsc, /buyeth"""
        try:
            # Check if user has wallet
            if not self.firebase.user_has_wallet(user_id):
                text = "❌ **No Wallet Found**\n\n"
                text += "You need to create or import a wallet first.\n"
                text += "Use the Wallet menu to get started!"
                
                keyboard = self.create_inline_keyboard([
                    [{'text': '🔐 Create Wallet', 'callback_data': 'create_wallet'}],
                    [{'text': '📥 Import Wallet', 'callback_data': 'import_wallet'}],
                    [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
                ])
                await self.send_message(chat_id, text, keyboard)
                return
            
            # Set up trading state for the quick command
            self.trading_state[chat_id] = {
                'chain': chain,
                'action': 'buy',
                'from_quick_command': True
            }
            
            # Get wallet info
            wallet = self.firebase.get_user_wallet(user_id)
            balance = self.blockchain.get_balance(chain, wallet['public_key'])
            
            if balance is None:
                balance = 0.0
            
            native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
            
            text = f"🚀 **Quick Buy - {chain}**\n\n"
            text += f"🔗 **Chain:** {chain}\n"
            text += f"💰 **Your Balance:** {balance:.6f} {native_symbol}\n"
            text += f"📊 **Slippage:** {self.get_user_slippage(chat_id)}%\n\n"
            text += f"🔧 **Enter the token contract address you want to buy:**"
            
            keyboard = self.create_inline_keyboard([
                [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_quick_buy_command: {e}")
            await self.send_message(chat_id, "❌ An error occurred. Please try again.")
    
    async def handle_quick_sell_command(self, chat_id, user_id, chain):
        """Handle quick sell commands like /sellbsc, /selleth"""
        try:
            # Check if user has wallet
            if not self.firebase.user_has_wallet(user_id):
                text = "❌ **No Wallet Found**\n\n"
                text += "You need to create or import a wallet first.\n"
                text += "Use the Wallet menu to get started!"
                
                keyboard = self.create_inline_keyboard([
                    [{'text': '🔐 Create Wallet', 'callback_data': 'create_wallet'}],
                    [{'text': '📥 Import Wallet', 'callback_data': 'import_wallet'}],
                    [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
                ])
                await self.send_message(chat_id, text, keyboard)
                return
            
            # Set up trading state for the quick command
            self.trading_state[chat_id] = {
                'chain': chain,
                'action': 'sell',
                'from_quick_command': True
            }
            
            # Get wallet info
            wallet = self.firebase.get_user_wallet(user_id)
            balance = self.blockchain.get_balance(chain, wallet['public_key'])
            
            if balance is None:
                balance = 0.0
            
            native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
            
            text = f"🚀 **Quick Sell - {chain}**\n\n"
            text += f"🔗 **Chain:** {chain}\n"
            text += f"💰 **Your Balance:** {balance:.6f} {native_symbol}\n"
            text += f"📊 **Slippage:** {self.get_user_slippage(chat_id)}%\n\n"
            text += f"🔧 **Enter the token contract address you want to sell:**"
            
            keyboard = self.create_inline_keyboard([
                [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_quick_sell_command: {e}")
            await self.send_message(chat_id, "❌ An error occurred. Please try again.")

    async def handle_quick_buy_from_success(self, chat_id, user_id, chain):
        """Handle quick buy from success message - auto-select chain and operation"""
        try:
            # Check if user has wallet
            if not self.firebase.user_has_wallet(user_id):
                text = "❌ **No Wallet Found**\n\n"
                text += "You need to create or import a wallet first.\n"
                text += "Use the Wallet menu to get started!"
                
                keyboard = self.create_inline_keyboard([
                    [{'text': '🔐 Create Wallet', 'callback_data': 'create_wallet'}],
                    [{'text': '📥 Import Wallet', 'callback_data': 'import_wallet'}],
                    [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
                ])
                await self.send_message(chat_id, text, keyboard)
                return
            
            # Check if we have a stored token address from previous successful transaction
            stored_token_address = None
            if chat_id in self.trading_state:
                stored_token_address = self.trading_state[chat_id].get('token_address')
                logger.info(f"DEBUG: Found stored token address: {stored_token_address}")
                logger.info(f"DEBUG: Current trading state: {self.trading_state[chat_id]}")
            else:
                logger.info(f"DEBUG: No trading state found for chat {chat_id}")
            
            # If we have a stored token address, use it directly
            if stored_token_address:
                logger.info(f"DEBUG: Using stored token address: {stored_token_address}")
                # Set up trading state with chain, action, and token address pre-selected
                self.trading_state[chat_id] = {
                    'chain': chain,
                    'action': 'buy',
                    'token_address': stored_token_address,
                    'from_quick_command': True
                }
                # Go directly to amount selection
                await self.go_directly_to_amount_selection(chat_id, user_id, stored_token_address, chain, 'buy')
                return
            
            # Set up trading state with chain and action pre-selected (no stored token address)
            self.trading_state[chat_id] = {
                'chain': chain,
                'action': 'buy',
                'from_quick_command': True
            }
            
            # Get wallet info
            wallet = self.firebase.get_user_wallet(user_id)
            balance = self.blockchain.get_balance(chain, wallet['public_key'])
            
            if balance is None:
                balance = 0.0
            
            native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
            
            text = f"🟢 **Quick Buy - {chain}**\n\n"
            text += f"🔗 **Chain:** {chain}\n"
            text += f"💰 **Your Balance:** {balance:.6f} {native_symbol}\n"
            text += f"📊 **Slippage:** {self.get_user_slippage(chat_id)}%\n\n"
            text += f"🔧 **Enter the token contract address you want to buy:**"
            
            keyboard = self.create_inline_keyboard([
                [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_quick_buy_from_success: {e}")
            await self.send_message(chat_id, "❌ An error occurred. Please try again.")

    async def handle_quick_sell_from_success(self, chat_id, user_id, chain):
        """Handle quick sell from success message - auto-select chain and operation"""
        try:
            # Check if user has wallet
            if not self.firebase.user_has_wallet(user_id):
                text = "❌ **No Wallet Found**\n\n"
                text += "You need to create or import a wallet first.\n"
                text += "Use the Wallet menu to get started!"
                
                keyboard = self.create_inline_keyboard([
                    [{'text': '🔐 Create Wallet', 'callback_data': 'create_wallet'}],
                    [{'text': '📥 Import Wallet', 'callback_data': 'import_wallet'}],
                    [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
                ])
                await self.send_message(chat_id, text, keyboard)
                return
            
            # Check if we have a stored token address from previous successful transaction
            stored_token_address = None
            if chat_id in self.trading_state:
                stored_token_address = self.trading_state[chat_id].get('token_address')
                logger.info(f"DEBUG: Found stored token address: {stored_token_address}")
                logger.info(f"DEBUG: Current trading state: {self.trading_state[chat_id]}")
            else:
                logger.info(f"DEBUG: No trading state found for chat {chat_id}")
            
            # If we have a stored token address, use it directly
            if stored_token_address:
                # Set up trading state with chain, action, and token address pre-selected
                self.trading_state[chat_id] = {
                    'chain': chain,
                    'action': 'sell',
                    'token_address': stored_token_address,
                    'from_quick_command': True
                }
                # Go directly to amount selection
                await self.go_directly_to_amount_selection(chat_id, user_id, stored_token_address, chain, 'sell')
                return
            
            # Set up trading state with chain and action pre-selected (no stored token address)
            self.trading_state[chat_id] = {
                'chain': chain,
                'action': 'sell',
                'from_quick_command': True
            }
            
            # Get wallet info
            wallet = self.firebase.get_user_wallet(user_id)
            balance = self.blockchain.get_balance(chain, wallet['public_key'])
            
            if balance is None:
                balance = 0.0
            
            native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
            
            text = f"🔴 **Quick Sell - {chain}**\n\n"
            text += f"🔗 **Chain:** {chain}\n"
            text += f"💰 **Your Balance:** {balance:.6f} {native_symbol}\n"
            text += f"📊 **Slippage:** {self.get_user_slippage(chat_id)}%\n\n"
            text += f"🔧 **Enter the token contract address you want to sell:**"
            
            keyboard = self.create_inline_keyboard([
                [{'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_quick_sell_from_success: {e}")
            await self.send_message(chat_id, "❌ An error occurred. Please try again.")

    async def go_directly_to_amount_selection(self, chat_id, user_id, token_address, chain, action):
        """Go directly to amount selection with full token overview"""
        try:
            logger.info(f"DEBUG: go_directly_to_amount_selection called for {action} on {chain}")
            # Get detailed token information using scanner
            scan_result = await self.token_scanner.scan_token(token_address, chain)
            
            if scan_result and "error" not in scan_result:
                # Format token information
                token_name = scan_result.get('token_name', 'Unknown')
                token_symbol = scan_result.get('token_symbol', 'Unknown')
                price_usd = scan_result.get('price_usd', 0) or 0
                price_change_24h = scan_result.get('price_change_24h', 0) or 0
                liquidity_usd = scan_result.get('liquidity_usd', 0) or 0
                volume_24h = scan_result.get('volume_24h', 0) or 0
                fdv = scan_result.get('fdv', 0) or 0
                transactions_24h = scan_result.get('transactions_24h', {'buys': 0, 'sells': 0})
                
                # Get tax information
                buy_tax = scan_result.get('buy_tax', 0)
                sell_tax = scan_result.get('sell_tax', 0)
                transfer_tax = scan_result.get('transfer_tax', 0)
                
                # Format price change
                if price_change_24h is not None:
                    if abs(price_change_24h) > 1:
                        if price_change_24h > 0:
                            price_change_str = f"📈 +{price_change_24h:.2f}%"
                        else:
                            price_change_str = f"📉 {price_change_24h:.2f}%"
                    else:
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
                
                # Get wallet balance
                wallet = self.firebase.get_user_wallet(user_id)
                wallet_balance = 0
                native_balance = 0
                
                try:
                    wallet_address = wallet['public_key']
                    
                    # Get token balance
                    wallet_balance = self.trading._get_token_balance(chain, token_address, wallet_address)
                    
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
                text += f"⚖️ Taxes | 🅑 {buy_tax:.1f}% 🅢 {sell_tax:.1f}% 🅣 {transfer_tax:.1f}%\n"
                liquidity_percentage = (liquidity_usd/fdv*100) if fdv and fdv > 0 else 0
                text += f"💧 Liquidity | ${liquidity_usd:,.0f} ({liquidity_percentage:.2f}%)\n"
                text += f"🕓 Refresh | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                text += f"💰 Balance\n"
                text += f" {token_symbol}   | {chain}\n"
                text += f" {wallet_balance:.6f} | {native_balance:.6f}\n\n"
                
                logger.info(f"DEBUG: Balance display - Token: {wallet_balance}, Native: {native_balance}")
                
                if fdv and fdv > 0 and liquidity_usd/fdv < 0.01:
                    text += f"🚨 Liquidity / Total Supply < 1%\n\n"
                
                # Get chain info for display
                chain_info = {
                    'ETH': {'symbol': 'ETH'},
                    'BSC': {'symbol': 'BNB'},
                    'SEPOLIA': {'symbol': 'ETH'}
                }
                chain_data = chain_info.get(chain, chain_info['BSC'])
                
                if action == 'buy':
                    text += f"Enter Amount ({chain_data['symbol']}):"
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                else:  # sell
                    text += f"Enter Amount ({token_symbol}):"
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                    
                await self.send_message(chat_id, text, keyboard)
                
            else:
                # Fallback to simple format if scanning fails
                chain_info = {
                    'ETH': {'symbol': 'ETH'},
                    'BSC': {'symbol': 'BNB'},
                    'SEPOLIA': {'symbol': 'ETH'}
                }
                chain_data = chain_info.get(chain, chain_info['BSC'])
                
                if action == 'buy':
                    text = f"🟢 **Quick Buy - {chain}**\n\n"
                    text += f"🔑 **Token:** `{token_address[:20]}...`\n"
                    text += f"💰 **Enter Amount ({chain_data['symbol']}):**"
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                else:  # sell
                    text = f"🔴 **Quick Sell - {chain}**\n\n"
                    text += f"🔑 **Token:** `{token_address[:20]}...`\n"
                    text += f"💰 **Enter Amount (TOKEN):**"
                    keyboard = self._create_amount_selection_keyboard(chain_data['symbol'], action, user_id)
                
                await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error in go_directly_to_amount_selection: {e}")
            await self.send_message(chat_id, "❌ An error occurred. Please try again.")
    
    async def get_updates(self):
        import aiohttp
        
        url = f"{self.base_url}/getUpdates"
        params = {'offset': self.offset, 'timeout': 30}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()
    
    async def process_updates(self, updates):
        for update in updates.get('result', []):
            try:
                self.offset = update['update_id'] + 1
                
                # Handle messages
                if 'message' in update:
                    await self._handle_message(update['message'])
                
                # Handle callback queries
                elif 'callback_query' in update:
                    await self._handle_callback_query(update['callback_query'])
                    
            except Exception as e:
                logger.error(f"Error processing update {update.get('update_id', 'unknown')}: {e}")
                # Continue processing other updates even if one fails
                continue
    
    async def _handle_message(self, message):
        """Handle incoming messages with proper error handling"""
        try:
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            username = message['from'].get('first_name', 'User')
            
            # Cache the username for future use
            self.user_cache[user_id] = username
            
            if 'text' in message:
                text = message['text']
                logger.info(f"Received message from {username} ({user_id}): {text[:50]}...")
                
                if text == '/start':
                    await self.handle_start_command(chat_id, user_id, username)
                elif text == '/help':
                    await self.handle_help(chat_id)
                elif text == '/buybsc':
                    await self.handle_quick_buy_command(chat_id, user_id, 'BSC')
                elif text == '/buyeth':
                    await self.handle_quick_buy_command(chat_id, user_id, 'ETH')
                elif text == '/sellbsc':
                    await self.handle_quick_sell_command(chat_id, user_id, 'BSC')
                elif text == '/selleth':
                    await self.handle_quick_sell_command(chat_id, user_id, 'ETH')
                elif len(text) == 64 and text.startswith('0x'):
                    # Handle private key input (remove 0x prefix)
                    await self.handle_private_key_input(chat_id, user_id, text[2:])
                elif len(text) == 64:
                    # Handle private key input (64 characters)
                    await self.handle_private_key_input(chat_id, user_id, text)
                elif len(text) == 42 and text.startswith('0x'):
                    # Handle token address input
                    await self.process_token_address(chat_id, text, user_id)
                elif self._is_numeric_amount(text):
                    # Handle amount input
                    await self.process_amount(chat_id, user_id, text)
                else:
                    await self.send_message(chat_id, "Send /start to begin using the bot!")
            else:
                await self.send_message(chat_id, "Please send text messages only. Send /start to begin!")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                chat_id = message['chat']['id']
                await self.send_message(chat_id, "❌ An error occurred. Please try again or send /start to restart.")
            except:
                logger.error("Failed to send error message to user")
    
    async def _handle_callback_query(self, callback_query):
        """Handle callback queries with proper error handling"""
        try:
            chat_id = callback_query['message']['chat']['id']
            user_id = callback_query['from']['id']
            callback_data = callback_query['data']
            
            # Cache the username from callback query BEFORE handling the callback
            username = callback_query['from'].get('first_name', 'User')
            self.user_cache[user_id] = username
            
            logger.info(f"Received callback from {username} ({user_id}): {callback_data}")
            
            await self.handle_callback_query(chat_id, user_id, callback_data)
            
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                chat_id = callback_query['message']['chat']['id']
                await self.send_message(chat_id, "❌ An error occurred processing your request. Please try again.")
            except:
                logger.error("Failed to send error message for callback query")
    
    def _is_numeric_amount(self, text):
        """Check if text represents a numeric amount"""
        try:
            amount = float(text)
            return 0.000001 <= amount <= 1000000
        except ValueError:
            return False
    
    async def health_check(self, request):
        """Health check endpoint for monitoring"""
        try:
            from datetime import datetime
            return web.json_response({
                'status': 'healthy',
                'bot_running': self.running,
                'x_bot_running': self.x_bot_running,
                'active_users': len(self.user_cache),
                'trading_sessions': len(self.trading_state),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            from datetime import datetime
            return web.json_response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=500)
    
    async def _get_token_balance_contract_call(self, chain, wallet_address, token_address):
        """Get ERC-20 token balance using direct contract call"""
        try:
            from web3 import Web3
            from decimal import Decimal
            
            # Get Web3 instance for the chain
            if chain == 'BSC':
                web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org'))
            elif chain == 'ETH':
                web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb'))
            else:
                logger.error(f"Unsupported chain: {chain}")
                return 0
            
            if not web3.is_connected():
                logger.error(f"Failed to connect to {chain} network")
                return 0
            
            # ERC-20 balanceOf function signature
            balance_of_signature = "0x70a08231"  # balanceOf(address)
            
            # Encode the function call - pad wallet address to 32 bytes
            wallet_address_padded = wallet_address[2:].lower().zfill(64)  # Remove 0x and pad to 64 chars
            encoded_data = balance_of_signature + wallet_address_padded
            
            logger.info(f"Making contract call to {token_address} with data: {encoded_data}")
            
            # Make the contract call
            result = web3.eth.call({
                'to': token_address,
                'data': encoded_data
            })
            
            if result:
                # Decode the result (32 bytes = 256 bits)
                balance = int.from_bytes(result, byteorder='big')
                logger.info(f"Raw balance from contract: {balance}")
                
                # Get token decimals (try to get from contract, fallback to 18)
                try:
                    decimals_signature = "0x313ce567"  # decimals()
                    decimals_result = web3.eth.call({
                        'to': token_address,
                        'data': decimals_signature
                    })
                    decimals = int.from_bytes(decimals_result, byteorder='big')
                    logger.info(f"Token decimals: {decimals}")
                except Exception as e:
                    logger.warning(f"Could not get decimals, using default 18: {e}")
                    decimals = 18  # Default for most tokens
                
                # Convert to decimal with proper decimals
                balance_decimal = Decimal(balance) / Decimal(10 ** decimals)
                final_balance = float(balance_decimal)
                logger.info(f"Final token balance: {final_balance}")
                return final_balance
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting token balance via contract call: {e}")
            return 0
    
    async def _get_native_balance_contract_call(self, chain, wallet_address):
        """Get native balance using direct Web3 call"""
        try:
            from web3 import Web3
            from decimal import Decimal
            
            # Get Web3 instance for the chain
            if chain == 'BSC':
                web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org'))
            elif chain == 'ETH':
                web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb'))
            else:
                logger.error(f"Unsupported chain: {chain}")
                return 0
            
            if not web3.is_connected():
                logger.error(f"Failed to connect to {chain} network")
                return 0
            
            logger.info(f"Getting native balance for {wallet_address} on {chain}")
            
            # Get native balance in wei
            balance_wei = web3.eth.get_balance(wallet_address)
            logger.info(f"Raw native balance (wei): {balance_wei}")
            
            # Convert to decimal (18 decimals for both ETH and BNB)
            balance_decimal = Decimal(balance_wei) / Decimal(10 ** 18)
            final_balance = float(balance_decimal)
            logger.info(f"Final native balance: {final_balance}")
            return final_balance
            
        except Exception as e:
            logger.error(f"Error getting native balance via contract call: {e}")
            return 0
    
    async def run_bot(self):
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not found!")
            return
        
        logger.info("🚀 Starting TG-Fets Trading Bot...")
        logger.info("Bot is ready to receive updates!")
        
        # Start X bot if credentials are available
        if self.x_bearer_token and self.x_api_key:
            await self.start_x_bot()
            logger.info("🐦 X Bot started successfully!")
        else:
            logger.warning("⚠️ X Bot credentials not configured - X bot will not start")
        
        self.running = True
        
        while self.running:
            try:
                updates = await self.get_updates()
                
                if updates.get('ok'):
                    await self.process_updates(updates)
                else:
                    logger.error(f"Telegram API error: {updates}")
                    # If API error, wait longer before retrying
                    await asyncio.sleep(10)
                
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                self.running = False
                await self.stop_x_bot()
                break
            except Exception as e:
                logger.error(f"Bot error: {e}")
                logger.info("Bot will continue running after error...")
                await asyncio.sleep(5)
    
    # X Bot Methods
    async def start_x_bot(self):
        """Start the X bot to monitor tweets"""
        if not all([self.x_bearer_token, self.x_api_key, self.x_api_secret, 
                   self.x_access_token, self.x_access_token_secret]):
            logger.error("❌ X Bot credentials not configured!")
            logger.info("💡 To enable X Bot, add Twitter API credentials to .env file")
            return False
        
        logger.info("🐦 Starting X Bot...")
        self.x_bot_running = True
        
        # Initialize last processed tweet ID if not set
        if self.last_processed_tweet_id is None:
            await self.initialize_last_tweet_id()
        
        # Start X bot monitoring in background
        asyncio.create_task(self.monitor_x_tweets())
        return True
    
    async def stop_x_bot(self):
        """Stop the X bot"""
        logger.info("🐦 Stopping X Bot...")
        self.x_bot_running = False
    
    def get_x_bot_status(self):
        """Get X bot status information"""
        if not all([self.x_bearer_token, self.x_api_key, self.x_api_secret, 
                   self.x_access_token, self.x_access_token_secret]):
            return {
                'configured': False,
                'running': False,
                'status': 'Not configured',
                'message': 'Add Twitter API credentials to .env file'
            }
        
        return {
            'configured': True,
            'running': self.x_bot_running,
            'status': 'Running' if self.x_bot_running else 'Stopped',
            'message': 'Monitoring tweets for @TweetFets mentions',
            'external_api': 'Available'  # External reply API is always available
        }
    
    async def monitor_x_tweets(self):
        """Monitor tweets mentioning @TweetFets"""
        logger.info("🔍 Monitoring tweets for @TweetFets mentions...")
        
        while self.x_bot_running:
            try:
                # Get recent tweets mentioning @TweetFets
                tweets = await self.get_tweets_mentioning_tweetfets()
                
                if tweets:
                    logger.info(f"📱 Found {len(tweets)} tweets mentioning @TweetFets")
                    for tweet in tweets:
                        if await self.should_process_tweet(tweet):
                            await self.process_tweetfets_tweet(tweet)
                else:
                    logger.debug("🔍 No tweets found mentioning @TweetFets")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring X tweets: {e}")
                await asyncio.sleep(60)
    
    async def initialize_last_tweet_id(self):
        """Initialize last processed tweet ID by getting the most recent tweet"""
        try:
            logger.info("🔍 Initializing last tweet ID...")
            
            # Get the most recent tweet mentioning @TweetFets
            tweets = await self.get_tweets_mentioning_tweetfets()
            
            if tweets:
                # Get the most recent tweet ID (highest ID number)
                latest_tweet = max(tweets, key=lambda x: int(x['id']))
                self.last_processed_tweet_id = latest_tweet['id']
                logger.info(f"✅ Initialized last tweet ID: {self.last_processed_tweet_id}")
                logger.info(f"📱 Bot will now only process tweets newer than this ID")
            else:
                logger.info("📱 No tweets found, starting fresh")
                self.last_processed_tweet_id = None
                
        except Exception as e:
            logger.error(f"Error initializing last tweet ID: {e}")
            self.last_processed_tweet_id = None
    
    async def get_tweets_mentioning_tweetfets(self):
        """Get recent tweets mentioning @TweetFets"""
        try:
            import aiohttp
            
            # Twitter API v2 endpoint for recent tweets
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                'Authorization': f'Bearer {self.x_bearer_token}',
                'Content-Type': 'application/json'
            }
            params = {
                'query': '@TweetFets',
                'max_results': 10,
                'tweet.fields': 'author_id,created_at,text'
            }
            
            # If we have a last processed tweet ID, use it to get only newer tweets
            if self.last_processed_tweet_id:
                params['since_id'] = self.last_processed_tweet_id
                logger.info(f"🔍 Fetching tweets newer than ID: {self.last_processed_tweet_id}")
            else:
                logger.info(f"🔍 Fetching recent tweets (first run)")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
                    else:
                        logger.error(f"Twitter API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting tweets: {e}")
            return []
    
    async def should_process_tweet(self, tweet):
        """Check if tweet should be processed"""
        tweet_id = tweet.get('id')
        
        # Skip if already processed
        if self.last_processed_tweet_id and tweet_id <= self.last_processed_tweet_id:
            logger.debug(f"⏭️ Skipping old tweet {tweet_id} (last processed: {self.last_processed_tweet_id})")
            return False
        
        # Check if tweet mentions @TweetFets and has command format
        text = tweet.get('text', '')
        if '@TweetFets' in text and self.parse_tweetfets_command(text):
            logger.info(f"✅ New tweet {tweet_id} ready for processing")
            return True
        
        logger.debug(f"⏭️ Skipping tweet {tweet_id} (no @TweetFets mention or invalid command)")
        return False
    
    def parse_tweetfets_command(self, tweet_text):
        """Parse @TweetFets command from tweet text"""
        # Check for help command first
        if re.search(r'@TweetFets\s+help', tweet_text, re.IGNORECASE):
            return {'action': 'help', 'valid': True}
        
        # Check for scan command: @TweetFets SCAN contract_address BSC/ETH/SEPOLIA
        scan_pattern = r'@TweetFets\s+SCAN\s+(0x[a-fA-F0-9]{40})\s+(BSC|ETH|SEPOLIA)'
        scan_match = re.search(scan_pattern, tweet_text, re.IGNORECASE)
        
        if scan_match:
            contract_address = scan_match.group(1)
            chain = scan_match.group(2).upper()
            
            return {
                'action': 'scan',
                'contract_address': contract_address,
                'chain': chain,
                'valid': True
            }
        
        # Expected format: @TweetFets Buy 0.01 contract_address
        # or: @TweetFets Sell 0.01 contract_address
        # or: @TweetFets Buy 0.01 contract_address BSC/ETH/SEPOLIA (optional chain)
        # or: @TweetFets Buy/Sell contract_address amount BSC/ETH/SEPOLIA (alternative format)
        
        # Pattern 1: amount first, then contract_address (original format)
        pattern1 = r'@TweetFets\s+(Buy|Sell)\s+([0-9.]+)\s+(0x[a-fA-F0-9]{40})(?:\s+([A-Z-]+))?'
        match1 = re.search(pattern1, tweet_text)
        
        if match1:
            action = match1.group(1).lower()  # buy or sell
            amount = float(match1.group(2))
            contract_address = match1.group(3)
            chain = match1.group(4) if match1.group(4) else 'BSC'  # Default to BSC mainnet
            
            # Validate chain
            if chain not in ['BSC', 'ETH']:
                chain = 'BSC'  # Default if invalid chain
            
            return {
                'action': action,
                'amount': amount,
                'contract_address': contract_address,
                'chain': chain,
                'valid': True
            }
        
        # Pattern 2: contract_address first, then amount (alternative format)
        pattern2 = r'@TweetFets\s+(Buy|Sell)\s+(0x[a-fA-F0-9]{40})\s+([0-9.]+)(?:\s+([A-Z-]+))?'
        match2 = re.search(pattern2, tweet_text)
        
        if match2:
            action = match2.group(1).lower()  # buy or sell
            contract_address = match2.group(2)
            amount = float(match2.group(3))
            chain = match2.group(4) if match2.group(4) else 'BSC'  # Default to BSC mainnet
            
            # Validate chain
            if chain not in ['BSC', 'ETH']:
                chain = 'BSC'  # Default if invalid chain
            
            return {
                'action': action,
                'amount': amount,
                'contract_address': contract_address,
                'chain': chain,
                'valid': True
            }
        
        return {'valid': False}
    
    async def process_tweetfets_tweet(self, tweet):
        """Process @TweetFets tweet and execute transaction"""
        try:
            text = tweet.get('text', '')
            author_id = tweet.get('author_id')
            
            # Parse command
            command = self.parse_tweetfets_command(text)
            if not command['valid']:
                logger.info(f"Invalid @TweetFets command: {text}")
                return
            
            logger.info(f"Processing @TweetFets command: {command}")
            
            # Handle help command
            if command['action'] == 'help':
                await self.handle_tweetfets_help(tweet)
                return
            
            # Handle scan command
            if command['action'] == 'scan':
                await self.handle_tweetfets_scan(tweet, command)
                return
            
            # Get user from database using X user ID
            user_data = await self.get_user_by_x_id(author_id)
            if not user_data:
                await self.reply_to_tweet(tweet['id'], f"❌ User not found in database. Please authenticate first.")
                return
            
            # Execute transaction
            tx_result = await self.execute_tweetfets_transaction(user_data, command)
            
            if tx_result['success']:
                # Reply with success and transaction hash
                reply_text = f"✅ Transaction executed successfully!\n\n"
                # Get the correct token symbol based on chain
                if command['chain'] == 'ETH':
                    token_symbol = 'ETH'
                elif command['chain'] == 'BSC':
                    token_symbol = 'BNB'
                
                reply_text += f"💰 **Amount:** {command['amount']} {token_symbol}\n"
                reply_text += f"⛓️ **Chain:** {command['chain']}\n"
                reply_text += f"📊 **Status:** {tx_result['status']}\n"
                # Get the correct blockchain explorer URL based on chain
                if command['chain'] == 'ETH':
                    explorer_url = f"https://etherscan.io/tx/{tx_result['tx_hash']}"
                elif command['chain'] == 'BSC':
                    explorer_url = f"https://bscscan.com/tx/{tx_result['tx_hash']}"
                
                reply_text += f"🔗 **TX Hash:** {explorer_url}"
                
                await self.reply_to_tweet(tweet['id'], reply_text)
            else:
                # Reply with error
                await self.reply_to_tweet(tweet['id'], f"❌ Transaction failed: {tx_result['error']}")
            
            # Update last processed tweet ID
            old_id = self.last_processed_tweet_id
            self.last_processed_tweet_id = tweet['id']
            logger.info(f"✅ Updated last processed tweet ID: {old_id} → {self.last_processed_tweet_id}")
            
        except Exception as e:
            logger.error(f"Error processing @TweetFets tweet: {e}")
            await self.reply_to_tweet(tweet['id'], f"❌ Error processing command: {str(e)}")
    
    async def get_user_by_x_id(self, x_user_id):
        """Get user data from database using X user ID"""
        try:
            # Query Firestore for user with matching X ID
            # We need to search through the twitter_auth collection to find users
            # who have authenticated with this X account
            
            # Get all documents from twitter_auth collection
            twitter_auth_refs = self.firebase.db.collection('twitter_auth').stream()
            
            for doc in twitter_auth_refs:
                auth_data = doc.to_dict()
                # Check if this auth data has the matching X user ID
                if auth_data.get('twitterId') == str(x_user_id):
                    # Found matching user
                    user_id = int(auth_data.get('userId'))
                    
                    # Get user's wallet and other data
                    wallet = self.firebase.get_user_wallet(user_id)
                    if wallet:
                        return {
                            'user_id': user_id,
                            'twitter_id': x_user_id,
                            'twitter_username': auth_data.get('twitterUsername'),
                            'wallet': wallet
                        }
            
            logger.info(f"No user found with X ID: {x_user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by X ID: {e}")
            return None
    
    async def execute_tweetfets_transaction(self, user_data, command):
        """Execute transaction based on @TweetFets command"""
        try:
            user_id = user_data['user_id']
            action = command['action']
            amount = command['amount']
            contract_address = command['contract_address']
            
            # Get user's wallet
            wallet = self.firebase.get_user_wallet(user_id)
            if not wallet:
                return {'success': False, 'error': 'No wallet found'}
            
            # Get private key
            private_key = self.firebase.get_private_key(user_id)
            if not private_key:
                return {'success': False, 'error': 'Private key not accessible'}
            
            # Execute trade using existing trading manager
            if action == 'buy':
                tx_result = self.trading.buy_tokens(
                    command['chain'],      # chain
                    contract_address,      # token_address
                    amount,                # bnb_amount
                    wallet['public_key'],  # user_address
                    private_key           # private_key
                )
            elif action == 'sell':
                tx_result = self.trading.sell_tokens(
                    command['chain'],      # chain
                    contract_address,      # token_address
                    amount,                # token_amount
                    wallet['public_key'],  # user_address
                    private_key           # private_key
                )
            else:
                return {'success': False, 'error': 'Invalid action'}
            
            if tx_result.get('success'):
                return {
                    'success': True,
                    'tx_hash': tx_result.get('tx_hash', 'Unknown'),
                    'status': 'Completed'
                }
            else:
                return {
                    'success': False,
                    'error': tx_result.get('error', 'Transaction failed')
                }
                
        except Exception as e:
            logger.error(f"Error executing branch transaction: {e}")
            return {'success': False, 'error': str(e)}
    
    async def reply_to_tweet(self, tweet_id, text):
        """Reply to a tweet using the external API with fallback"""
        try:
            import aiohttp
            
            # Use the external API endpoint for replying
            url = "https://x-reply-bot.vercel.app/api/tweets/reply"
            
            # Prepare the request payload
            payload = {
                'tweetId': str(tweet_id),
                'content': text
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.info(f"📝 Attempting to reply to tweet {tweet_id}: {text}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        logger.info(f"✅ Successfully replied to tweet {tweet_id}")
                        logger.info(f"📝 Reply response: {response_data}")
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ External API reply failed: {response.status}")
                        logger.error(f"Response: {response_text}")
                        
                        # Fallback: Log the reply locally
                        logger.info(f"📝 FALLBACK: Would reply to tweet {tweet_id}: {text}")
                        logger.info(f"💡 External API failed, but transaction was processed successfully")
                        return True  # Return True to continue processing
                        
        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            # Even if reply fails, log it locally and continue
            logger.info(f"📝 ERROR FALLBACK: Would reply to tweet {tweet_id}: {text}")
            return True  # Return True to continue processing
    
    async def handle_tweetfets_help(self, tweet):
        """Handle @TweetFets help command"""
        try:
            help_text = "🐦 @TweetFets Bot Commands:\n\n"
            help_text += "Buy: @TweetFets Buy 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 0.01\n"
            help_text += "Sell: @TweetFets Sell 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 0.01\n"
            help_text += "Alternative: @TweetFets Buy 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 0.01\n"
            help_text += "With Chain: @TweetFets Buy 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 0.01 BSC/ETH/SEPOLIA\n"
            help_text += "Or: @TweetFets Buy 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 0.01 ETH\n"
            help_text += "Scan: @TweetFets SCAN 0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5 BSC/ETH/SEPOLIA\n\n"
            help_text += "Chains: BSC (default), ETH, SEPOLIA\n"
            help_text += "⚠️ Authenticate first via Telegram bot!"
            
            await self.reply_to_tweet(tweet['id'], help_text)
            
        except Exception as e:
            logger.error(f"Error handling help command: {e}")
    
    async def handle_tweetfets_scan(self, tweet, command):
        """Handle @TweetFets scan command"""
        try:
            contract_address = command['contract_address']
            chain = command['chain']
            
            # Map chain names for token scanner compatibility
            chain_mapping = {
                'BSC': 'BSC',
                'ETH': 'ETH'
            }
            
            mapped_chain = chain_mapping.get(chain, chain)
            
            # Scan the token directly without showing scanning status
            result = await self.token_scanner.scan_token(contract_address, mapped_chain)
            
            if result and "error" not in result:
                # Format and display the result using compact format for Twitter
                formatted_result = self.token_scanner.format_scan_result(result, compact=True)
                
                await self.reply_to_tweet(tweet['id'], formatted_result)
                
            else:
                error_text = f"❌ **Token Scan Failed**\n\n"
                if result and "error" in result:
                    error_text += f"**Error:** {result['error']}"
                else:
                    error_text += f"**Error:** Failed to scan token"
                
                await self.reply_to_tweet(tweet['id'], error_text)
            
            # Update last processed tweet ID after successful scan
            old_id = self.last_processed_tweet_id
            self.last_processed_tweet_id = tweet['id']
            logger.info(f"✅ Updated last processed tweet ID: {old_id} → {self.last_processed_tweet_id}")
                
        except Exception as e:
            logger.error(f"Error handling scan command: {e}")
            await self.reply_to_tweet(tweet['id'], f"❌ Error scanning token: {str(e)}")
            
            # Update last processed tweet ID even on error to avoid reprocessing
            old_id = self.last_processed_tweet_id
            self.last_processed_tweet_id = tweet['id']
            logger.info(f"✅ Updated last processed tweet ID (error case): {old_id} → {self.last_processed_tweet_id}")
    
    async def check_user_balance(self, user_data, chain):
        """Check user's balance for the specified chain"""
        try:
            wallet = user_data['wallet']
            balance = self.blockchain.get_balance(chain, wallet['public_key'])
            return balance
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return None
    
    async def show_x_bot_status(self, chat_id):
        """Show X bot status information"""
        try:
            status = self.get_x_bot_status()
            
            if status['configured']:
                text = f"🐦 **X Bot Status:** {status['status']}\n\n"
                text += f"📱 **Status:** {status['message']}\n"
                text += f"🔧 **Configuration:** ✅ Configured\n"
                
                if status['running']:
                    text += f"🟢 **Status:** Running and monitoring tweets\n"
                    text += f"📊 **Monitoring:** @TweetFets mentions\n"
                    text += f"⏱️ **Check Interval:** Every 30 seconds\n"
                    text += f"🆔 **Last Processed Tweet ID:** {self.last_processed_tweet_id or 'None'}\n"
                    text += f"🌐 **Reply API:** {status.get('external_api', 'Unknown')}"
                else:
                    text += f"🔴 **Status:** Stopped\n"
                    text += f"💡 **Action:** Bot will start automatically when credentials are added"
            else:
                text = f"🐦 **X Bot Status:** {status['status']}\n\n"
                text += f"❌ **Configuration:** Not configured\n"
                text += f"💡 **To enable:** Add Twitter API credentials to .env file\n\n"
                text += f"**Required credentials:**\n"
                text += f"• X_BEARER_TOKEN\n"
                text += f"• X_API_KEY\n"
                text += f"• X_API_SECRET\n"
                text += f"• X_ACCESS_TOKEN\n"
                text += f"• X_ACCESS_TOKEN_SECRET"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '🔄 Reset Tweet ID', 'callback_data': 'reset_tweet_id'}
                ],
                [
                    {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error showing X bot status: {e}")
            await self.send_message(chat_id, "❌ Error getting X bot status")
    
    async def reset_tweet_id_command(self, chat_id):
        """Handle reset tweet ID command"""
        try:
            old_id = self.last_processed_tweet_id
            self.last_processed_tweet_id = None
            
            text = "🔄 **Tweet ID Reset Successfully!**\n\n"
            text += f"✅ **Last processed tweet ID has been reset**\n"
            text += f"🆔 **Previous ID:** {old_id or 'None'}\n"
            text += f"📱 **Next run will process all recent tweets**\n"
            text += f"⚠️ **Note:** This will cause the bot to process tweets from the beginning"
            
            keyboard = self.create_inline_keyboard([[
                {'text': '🔙 Back to Main', 'callback_data': 'main_menu'}
            ]])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error resetting tweet ID: {e}")
            await self.send_message(chat_id, "❌ Error resetting tweet ID")
    
    async def health_check(self, request):
        """Health check endpoint for Fly.io"""
        try:
            from datetime import datetime
            status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'bot_running': self.running,
                'x_bot_running': self.x_bot_running,
                'components_initialized': hasattr(self, 'firebase') and hasattr(self, 'trading'),
                'last_tweet_id': self.last_processed_tweet_id
            }
            return web.json_response(status)
        except Exception as e:
            from datetime import datetime
            return web.json_response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=500)

    async def handle_quick_amount_selection(self, chat_id, user_id, amount):
        """Handle quick amount button selection"""
        try:
            # Store the selected amount in trading state
            if chat_id not in self.trading_state:
                self.trading_state[chat_id] = {}
            
            # Convert amount to float with error handling
            try:
                amount_float = float(amount)
            except ValueError:
                await self.send_message(chat_id, f"❌ Invalid amount format: {amount}")
                return
            
            self.trading_state[chat_id]['amount'] = amount_float
            self.trading_state[chat_id]['user_id'] = user_id
            
            # Get current trading state
            action = self.trading_state[chat_id].get('action', 'buy')
            token_address = self.trading_state[chat_id].get('token') or self.trading_state[chat_id].get('token_address')
            chain = self.trading_state[chat_id].get('chain', 'BSC')
            
            if not token_address:
                await self.send_message(chat_id, "❌ No token address found. Please start over.")
                return
            
            # Get chain data
            chain_data = self.get_chain_data(chain)
            
            # Calculate fees and totals (matching custom amount format)
            bnb_amount = float(amount)
            gas_estimate = 0.005  # Estimated gas in BNB
            total_bnb = bnb_amount + gas_estimate
            
            # Calculate token amount and price per token (matching custom amount calculations)
            token_amount = bnb_amount / 0.00280184  # Using same calculation as custom
            price_per_token = bnb_amount / token_amount if token_amount > 0 else 0
            
            # Show detailed transaction overview (matching custom amount format)
            if action == 'buy':
                text = f"🟢 **BUY TRANSACTION OVERVIEW**\n\n"
            else:
                text = f"🔴 **SELL TRANSACTION OVERVIEW**\n\n"
            
            text += f"🔑 **Token:** `{token_address[:20]}...`\n"
            text += f"🌐 Network: {chain_data['name']}\n"
            text += f"🔄 **DEX:** {chain_data['dex']}\n\n"
            
            text += f"💰 **Transaction Details:**\n"
            native_symbol = 'ETH' if chain == 'ETH' else 'BNB'
            text += f"• **{native_symbol} Amount:** {bnb_amount:.6f} {native_symbol}\n"
            text += f"• **Estimated Gas:** {gas_estimate:.6f} {native_symbol}\n"
            text += f"• **Total Cost:** {total_bnb:.6f} {native_symbol}\n\n"
            
            if action == 'buy':
                text += f"🪙 **Token Details:**\n"
                text += f"• **Tokens to Receive:** {token_amount:.6f}\n"
                text += f"• **Price per Token:** {price_per_token:.8f} {native_symbol}\n"
                text += f"• **Slippage:** {self.get_user_slippage(user_id)}%\n\n"
            else:
                text += f"🪙 **Token Details:**\n"
                estimated_native = token_amount * price_per_token
                net_native = estimated_native - gas_estimate
                text += f"• **Token Amount:** {token_amount:.2f}\n"
                text += f"• **Estimated {native_symbol}:** {estimated_native:.6f} {native_symbol}\n"
                text += f"• **Gas Fee:** {gas_estimate:.6f} {native_symbol}\n"
                text += f"• **Net {native_symbol}:** {net_native:.6f} {native_symbol}\n\n"
                text += f"💰 **Price Details:**\n"
                text += f"• **Price per Token:** {price_per_token:.8f} {native_symbol}\n"
                text += f"• **Slippage:** {self.get_user_slippage(user_id)}%\n\n"
            
            text += f"📊 **Price Impact:** Low\n"
            text += f"⏱️ **Estimated Time:** 30-60 seconds\n\n"
            text += f"⚠️ **Please review the details above.**\n"
            text += f"Click 'Confirm {'Buy' if action == 'buy' else 'Sell'}' to proceed with the transaction."
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': f'✅ Confirm {"Buy" if action == "buy" else "Sell"}', 'callback_data': f'confirm_{action}'},
                    {'text': '❌ Cancel', 'callback_data': 'buy_sell'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling quick amount selection: {e}")
            await self.send_message(chat_id, f"❌ Error processing amount: {str(e)}")

    async def handle_custom_amount_selection(self, chat_id, user_id):
        """Handle custom amount button selection"""
        try:
            # Store user_id in trading state
            if chat_id not in self.trading_state:
                self.trading_state[chat_id] = {}
            
            self.trading_state[chat_id]['user_id'] = user_id
            
            # Get current trading state
            action = self.trading_state[chat_id].get('action', 'buy')
            chain = self.trading_state[chat_id].get('chain', 'BSC')
            chain_data = self.get_chain_data(chain)
            
            text = f"💰 Enter Custom Amount\n\n"
            text += f"🌐 Network: {chain_data['name']}\n"
            text += f"💡 Example: 0.1, 0.5, 1.0, 2.5\n\n"
            text += f"🔧 Type the amount of {chain_data['symbol']} you want to spend:"
            
            keyboard = self.create_inline_keyboard([
                [{'text': '🔙 Back to Amount Selection', 'callback_data': 'buy_sell'}]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling custom amount selection: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")

    async def handle_edit_slippage(self, chat_id, user_id, action):
        """Handle slippage editing"""
        try:
            # Store user_id in trading state
            if chat_id not in self.trading_state:
                self.trading_state[chat_id] = {}
            
            self.trading_state[chat_id]['user_id'] = user_id
            
            # Get current slippage
            current_slippage = self.get_user_slippage(user_id)
            
            text = f"⚙️ Slippage Settings\n\n"
            text += f"Current Slippage: {current_slippage}%\n\n"
            text += f"💡 Slippage tolerance allows for price movement during trade execution.\n"
            text += f"Higher slippage = faster execution but potentially worse price.\n\n"
            text += f"🔧 Enter new slippage percentage (0.1 - 50):"
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '0.5%', 'callback_data': 'set_slippage_0.5'},
                    {'text': '1%', 'callback_data': 'set_slippage_1'},
                    {'text': '2%', 'callback_data': 'set_slippage_2'}
                ],
                [
                    {'text': '5%', 'callback_data': 'set_slippage_5'},
                    {'text': '10%', 'callback_data': 'set_slippage_10'},
                    {'text': 'Custom', 'callback_data': 'set_slippage_custom'}
                ],
                [
                    {'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling slippage edit: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")

    async def handle_set_slippage(self, chat_id, user_id, slippage):
        """Handle slippage setting"""
        try:
            if slippage == 'custom':
                text = f"🔧 Enter Custom Slippage\n\n"
                text += f"💡 Enter slippage percentage (0.1 - 50):"
                
                keyboard = self.create_inline_keyboard([
                    [{'text': '🔙 Back to Slippage Settings', 'callback_data': f'edit_slippage_buy'}]
                ])
                
                await self.send_message(chat_id, text, keyboard)
                return
            
            # Parse and validate slippage
            try:
                slippage_value = float(slippage)
                if slippage_value < 0.1 or slippage_value > 50:
                    await self.send_message(chat_id, "❌ Slippage must be between 0.1% and 50%")
                    return
            except ValueError:
                await self.send_message(chat_id, "❌ Invalid slippage value")
                return
            
            # Save slippage setting
            self.set_user_slippage(user_id, slippage_value)
            
            text = f"✅ Slippage Updated!\n\n"
            text += f"New Slippage: {slippage_value}%\n\n"
            text += f"🔄 Returning to trading..."
            
            keyboard = self.create_inline_keyboard([
                [{'text': '🔙 Back to Trading', 'callback_data': 'buy_sell'}]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error setting slippage: {e}")
            await self.send_message(chat_id, f"❌ Error: {str(e)}")

    async def handle_sell_percentage_selection(self, chat_id, user_id, percentage):
        """Handle sell percentage button selection"""
        try:
            # Store user_id in trading state
            if chat_id not in self.trading_state:
                self.trading_state[chat_id] = {}
            
            self.trading_state[chat_id]['user_id'] = user_id
            
            # Get current trading state
            action = self.trading_state[chat_id].get('action', 'sell')
            token_address = self.trading_state[chat_id].get('token') or self.trading_state[chat_id].get('token_address')
            chain = self.trading_state[chat_id].get('chain', 'BSC')
            
            if not token_address:
                await self.send_message(chat_id, "❌ No token address found. Please start over.")
                return
            
            # Get user's token balance
            wallet_data = self.firebase.get_user_wallet(user_id)
            if not wallet_data:
                await self.send_message(chat_id, "❌ No wallet found. Please create a wallet first.")
                return
            
            wallet_address = wallet_data['public_key']
            
            # Get token balance using contract call
            token_balance = await self._get_token_balance_contract_call(chain, wallet_address, token_address)
            
            if token_balance <= 0:
                await self.send_message(chat_id, "❌ You don't have any tokens to sell.")
                return
            
            # Calculate sell amount based on percentage
            percentage_value = float(percentage) / 100.0
            sell_amount = token_balance * percentage_value
            
            # Store the calculated amount as float
            self.trading_state[chat_id]['amount'] = sell_amount
            
            # Get chain data
            chain_data = self.get_chain_data(chain)
            
            # Show confirmation with calculated amount
            text = f"🔴 **SELL TRANSACTION OVERVIEW**\n\n"
            text += f"🔑 **Token:** `{token_address[:20]}...`\n"
            text += f"🌐 Network: {chain_data['name']}\n"
            text += f"🔄 **DEX:** {chain_data['dex']}\n\n"
            
            text += f"💰 **Transaction Details:**\n"
            text += f"• **Token Amount:** {sell_amount:.6f}\n"
            text += f"• **Percentage:** {percentage}% of balance\n"
            text += f"• **Total Balance:** {token_balance:.6f}\n\n"
            
            text += f"🪙 **Token Details:**\n"
            estimated_native = sell_amount * 0.00280184  # Estimated price
            gas_estimate = 0.005
            net_native = estimated_native - gas_estimate
            text += f"• **Estimated {chain_data['symbol']}:** {estimated_native:.6f} {chain_data['symbol']}\n"
            text += f"• **Gas Fee:** {gas_estimate:.6f} {chain_data['symbol']}\n"
            text += f"• **Net {chain_data['symbol']}:** {net_native:.6f} {chain_data['symbol']}\n\n"
            text += f"💰 **Price Details:**\n"
            text += f"• **Price per Token:** 0.00280184 {chain_data['symbol']}\n"
            text += f"• **Slippage:** {self.get_user_slippage(user_id)}%\n\n"
            
            text += f"📊 **Price Impact:** Low\n"
            text += f"⏱️ **Estimated Time:** 30-60 seconds\n\n"
            text += f"⚠️ **Please review the details above.**\n"
            text += f"Click 'Confirm Sell' to proceed with the transaction."
            
            keyboard = self.create_inline_keyboard([
                [
                    {'text': '✅ Confirm Sell', 'callback_data': 'confirm_sell'},
                    {'text': '❌ Cancel', 'callback_data': 'buy_sell'}
                ]
            ])
            
            await self.send_message(chat_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error handling sell percentage selection: {e}")
            await self.send_message(chat_id, f"❌ Error processing percentage: {str(e)}")

async def start_http_server(bot):
    """Start HTTP server for health checks"""
    app = web.Application()
    app.router.add_get('/health', bot.health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("🌐 HTTP server started on port 8080")
    return runner

def main():
    try:
        bot = SimpleTelegramBot()
        
        # Start both bot and HTTP server
        async def run_both():
            # Start HTTP server
            http_runner = await start_http_server(bot)
            
            try:
                # Start the bot
                await bot.run_bot()
            finally:
                # Clean up HTTP server
                await http_runner.cleanup()
        
        asyncio.run(run_both())
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")

if __name__ == "__main__":
    main()

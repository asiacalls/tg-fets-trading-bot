from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any

class KeyboardManager:
    def __init__(self):
        """Initialize keyboard manager"""
        pass
    
    def get_main_menu(self, twitter_username: str = None) -> InlineKeyboardMarkup:
        """Get main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Buy/Sell", callback_data="buy_sell"),
                InlineKeyboardButton("🔐 Wallet", callback_data="wallet")
            ],
            [
                InlineKeyboardButton("💳 Balance", callback_data="balance"),
                InlineKeyboardButton("💸 Transfer", callback_data="transfer")
            ],
            [
                InlineKeyboardButton("🔍 Token Scanner", callback_data="scan_token"),
                InlineKeyboardButton("📋 History", callback_data="scanner_history")
            ],
            [
                InlineKeyboardButton(f"🐦 @{twitter_username}" if twitter_username else "🐦 Twitter Auth", callback_data="twitter_auth"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_buy_sell_menu(self) -> InlineKeyboardMarkup:
        """Get buy/sell selection menu"""
        keyboard = [
            [
                InlineKeyboardButton("🟢 Buy Tokens", callback_data="buy"),
                InlineKeyboardButton("🔴 Sell Tokens", callback_data="sell")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_trading_chain_selection_menu(self) -> InlineKeyboardMarkup:
        """Get trading chain selection menu"""
        keyboard = [
            [
                InlineKeyboardButton("🔵 Ethereum Mainnet", callback_data="trading_chain_ETH"),
                InlineKeyboardButton("🟡 BSC Mainnet", callback_data="trading_chain_BSC")
            ],
            [
                InlineKeyboardButton("🟣 Sepolia Testnet", callback_data="trading_chain_SEPOLIA")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="buy_sell")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_wallet_menu(self) -> InlineKeyboardMarkup:
        """Get wallet menu for users without wallet"""
        keyboard = [
            [
                InlineKeyboardButton("🆕 Create New Wallet", callback_data="create_wallet"),
                InlineKeyboardButton("📥 Import Wallet", callback_data="import_wallet")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_wallet_details_menu(self) -> InlineKeyboardMarkup:
        """Get wallet details menu for users with wallet"""
        keyboard = [
            [
                InlineKeyboardButton("🔑 Show Private Key", callback_data="show_private_key"),
                InlineKeyboardButton("🗑️ Delete Wallet", callback_data="delete_wallet")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_chain_selection_menu(self, action: str) -> InlineKeyboardMarkup:
        """Get chain selection menu for various actions"""
        keyboard = [
            [
                InlineKeyboardButton("🔵 Ethereum Mainnet", callback_data=f"{action}_ETH"),
                InlineKeyboardButton("🟡 BSC Mainnet", callback_data=f"{action}_BSC")
            ],
            [
                InlineKeyboardButton("🟣 Sepolia Testnet", callback_data=f"{action}_SEPOLIA")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data=self._get_back_callback(action))
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_settings_menu(self) -> InlineKeyboardMarkup:
        """Get settings menu"""
        keyboard = [
            [
                InlineKeyboardButton("🔔 Notifications", callback_data="notif_prefs"),
                InlineKeyboardButton("👁️ Privacy", callback_data="toggle_sensitive")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_transfer_menu(self) -> InlineKeyboardMarkup:
        """Get transfer menu"""
        keyboard = [
            [
                InlineKeyboardButton("🟡 Native Token", callback_data="transfer_native"),
                InlineKeyboardButton("🪙 ERC20 Token", callback_data="transfer_token")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_trade_confirmation_menu(self) -> InlineKeyboardMarkup:
        """Get trade confirmation menu"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Trade", callback_data="confirm_trade"),
                InlineKeyboardButton("❌ Cancel Trade", callback_data="cancel_trade")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_confirm_menu(self, action: str) -> InlineKeyboardMarkup:
        """Get confirmation menu for dangerous actions"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, I'm Sure", callback_data=f"confirm_{action}"),
                InlineKeyboardButton("❌ No, Cancel", callback_data=self._get_back_callback(action))
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_cancel_button(self) -> InlineKeyboardMarkup:
        """Get simple cancel button"""
        keyboard = [
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_back_button(self, target: str = "main_menu") -> InlineKeyboardMarkup:
        """Get back button to specified target"""
        keyboard = [
            [
                InlineKeyboardButton("🔙 Back", callback_data=target)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_twitter_auth_keyboard(self) -> InlineKeyboardMarkup:
        """Get Twitter authentication keyboard"""
        keyboard = [
            [InlineKeyboardButton("✅ Complete", callback_data="twitter_auth_complete")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_error_menu(self, error_message: str = "An error occurred") -> InlineKeyboardMarkup:
        """Get error menu with retry option"""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Retry", callback_data="retry"),
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_success_menu(self, next_action: str = "main_menu") -> InlineKeyboardMarkup:
        """Get success menu with next action"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Continue", callback_data=next_action)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_pagination_menu(self, current_page: int, total_pages: int, 
                           action: str, data: str = "") -> InlineKeyboardMarkup:
        """Get pagination menu for lists"""
        keyboard = []
        
        # Navigation buttons
        nav_row = []
        if current_page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Previous", 
                                              callback_data=f"{action}_page_{current_page-1}_{data}"))
        
        nav_row.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", 
                                          callback_data="page_info"))
        
        if current_page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", 
                                              callback_data=f"{action}_page_{current_page+1}_{data}"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        # Back button
        keyboard.append([
            InlineKeyboardButton("🔙 Back", callback_data=self._get_back_callback(action))
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_quick_actions_menu(self) -> InlineKeyboardMarkup:
        """Get quick actions menu for power users"""
        keyboard = [
            [
                InlineKeyboardButton("⚡ Quick Buy", callback_data="quick_buy"),
                InlineKeyboardButton("⚡ Quick Sell", callback_data="quick_sell")
            ],
            [
                InlineKeyboardButton("📊 Portfolio", callback_data="portfolio"),
                InlineKeyboardButton("📈 Charts", callback_data="charts")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_help_menu(self) -> InlineKeyboardMarkup:
        """Get help menu"""
        keyboard = [
            [
                InlineKeyboardButton("📖 User Guide", callback_data="user_guide"),
                InlineKeyboardButton("❓ FAQ", callback_data="faq")
            ],
            [
                InlineKeyboardButton("🆘 Support", callback_data="support"),
                InlineKeyboardButton("🐛 Report Bug", callback_data="report_bug")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_back_callback(self, action: str) -> str:
        """Get appropriate back callback based on action"""
        back_mapping = {
            'wallet': 'wallet',
            'balance': 'balance',
            'settings': 'settings',
            'transfer': 'transfer',
            'buy_sell': 'buy_sell',
            'main_menu': 'main_menu'
        }
        return back_mapping.get(action, 'main_menu')
    
    def create_custom_keyboard(self, buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
        """Create custom keyboard from button definitions"""
        keyboard = []
        
        for row in buttons:
            keyboard_row = []
            for button in row:
                keyboard_row.append(InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button['callback_data']
                ))
            keyboard.append(keyboard_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_scanner_result_menu(self, token_address: str = "") -> InlineKeyboardMarkup:
        """Get scanner result menu with copy address and refresh buttons"""
        keyboard = [
            [
                InlineKeyboardButton("📋 Copy Address", callback_data=f"copy_address_{token_address}"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_scan_{token_address}")
            ],
            [
                InlineKeyboardButton("🔍 Scan Another", callback_data="scan_token"),
                InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_scanner_chain_selection_menu(self) -> InlineKeyboardMarkup:
        """Get scanner chain selection menu"""
        keyboard = [
            [
                InlineKeyboardButton("🔵 Ethereum", callback_data="scanner_chain_ETH"),
                InlineKeyboardButton("🟡 BSC", callback_data="scanner_chain_BSC")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)



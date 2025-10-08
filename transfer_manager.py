import asyncio
import logging
from web3 import Web3
from decimal import Decimal
import json

logger = logging.getLogger(__name__)

class TransferManager:
    def __init__(self):
        # Web3 instances for different chains
        self.web3_instances = {}
        
        # Chain configurations
        self.chain_configs = {
            'ETH': {
                'rpc': 'https://eth.llamarpc.com/',
                'native_symbol': 'ETH',
                'decimals': 18,
                'explorer': 'https://etherscan.io/tx/',
                'gas_limit': 21000,  # Standard ETH transfer
                'max_priority_fee': 5,  # Gwei - increased for faster transactions
                'max_fee': 100  # Gwei - increased for faster transactions
            },
            'BSC': {
                'rpc': 'https://bsc-dataseed.binance.org/',
                'native_symbol': 'BNB',
                'decimals': 18,
                'explorer': 'https://bscscan.com/tx/',
                'gas_limit': 21000,
                'max_priority_fee': 3,  # Gwei - increased for faster transactions
                'max_fee': 10  # Gwei - increased for faster transactions
            },
            'SEPOLIA': {
                'rpc': 'https://sepolia.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb',
                'native_symbol': 'ETH',
                'decimals': 18,
                'explorer': 'https://sepolia.etherscan.io/tx/',
                'gas_limit': 21000,
                'max_priority_fee': 3,  # Gwei - increased for faster transactions
                'max_fee': 50  # Gwei - increased for faster transactions
            }
        }
        
        # Initialize Web3 connections
        self._initialize_web3()
    
    def _get_raw_transaction(self, signed_txn):
        """Get raw transaction bytes - handles Web3.py version compatibility"""
        try:
            return signed_txn.rawTransaction
        except AttributeError:
            return signed_txn.raw_transaction
    
    def _initialize_web3(self):
        """Initialize Web3 connections for different chains"""
        try:
            for chain, config in self.chain_configs.items():
                self.web3_instances[chain] = Web3(Web3.HTTPProvider(config['rpc']))
                logger.info(f"✅ Web3 connection initialized for {chain}")
            
            logger.info("✅ All Web3 connections initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing Web3 connections: {e}")
    
    def get_transfer_menu(self):
        """Get the transfer menu keyboard"""
        return [
            [
                {'text': '🔵 Ethereum', 'callback_data': 'transfer_chain_eth'},
                {'text': '🟡 BSC', 'callback_data': 'transfer_chain_bsc'}
            ],
       
            [
                {'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}
            ]
        ]
    
    def get_transfer_type_menu(self, chain):
        """Get transfer type selection menu"""
        native_symbol = self.chain_configs[chain]['native_symbol']
        # Map chain names for callback data
        chain_callback_mapping = {
            'ETH': 'eth',
            'BSC': 'bsc'
        }
        chain_callback = chain_callback_mapping.get(chain, chain.lower())
        return [
            [
                {'text': f'💰 Native {native_symbol}', 'callback_data': f'transfer_native_{chain_callback}'},
                {'text': '🪙 Token', 'callback_data': f'transfer_token_{chain_callback}'}
            ],
            [
                {'text': '🔙 Back to Chain Selection', 'callback_data': 'transfer'}
            ]
        ]
    
    async def transfer_native_tokens(self, from_address, to_address, amount, chain, private_key):
        """Transfer native tokens (ETH/BNB)"""
        try:
            if chain not in self.web3_instances:
                return {'success': False, 'error': f'Chain {chain} not supported'}
            
            web3_instance = self.web3_instances[chain]
            chain_config = self.chain_configs[chain]
            
            # Convert amount to Wei
            amount_wei = web3_instance.to_wei(amount, 'ether')
            
            # Get nonce
            nonce = web3_instance.eth.get_transaction_count(from_address)
            
            # Get current gas price and boost it for faster transactions
            current_gas_price = web3_instance.eth.gas_price
            gas_price = int(current_gas_price * 1.3)  # Use 130% of current gas price for faster confirmation
            
            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': amount_wei,
                'gas': chain_config['gas_limit'],
                'gasPrice': gas_price,
                'chainId': web3_instance.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = web3_instance.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = web3_instance.eth.send_raw_transaction(self._get_raw_transaction(signed_txn))
            
            # Wait for transaction receipt
            receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt.gasUsed,
                    'explorer_url': f"{chain_config['explorer']}{tx_hash.hex()}"
                }
            else:
                return {'success': False, 'error': 'Transaction failed'}
                
        except Exception as e:
            logger.error(f"Error transferring native tokens: {e}")
            return {'success': False, 'error': str(e)}
    
    async def transfer_erc20_tokens(self, from_address, to_address, token_address, amount, chain, private_key):
        """Transfer ERC-20 tokens"""
        try:
            if chain not in self.web3_instances:
                return {'success': False, 'error': f'Chain {chain} not supported'}
            
            web3_instance = self.web3_instances[chain]
            chain_config = self.chain_configs[chain]
            
            # ERC-20 transfer function signature
            transfer_signature = "0xa9059cbb"  # transfer(address,uint256)
            
            # Get token info
            token_info = await self._get_token_info(web3_instance, token_address)
            if not token_info:
                return {'success': False, 'error': 'Could not get token information'}
            
            # Convert amount to token units
            amount_units = int(amount * (10 ** token_info['decimals']))
            
            # Encode transfer function call
            encoded_data = transfer_signature + "000000000000000000000000" + to_address[2:] + format(amount_units, '064x')
            
            # Get nonce
            nonce = web3_instance.eth.get_transaction_count(from_address)
            
            # Get current gas price and boost it for faster transactions
            current_gas_price = web3_instance.eth.gas_price
            gas_price = int(current_gas_price * 1.3)  # Use 130% of current gas price for faster confirmation
            
            # Estimate gas for token transfer
            gas_estimate = web3_instance.eth.estimate_gas({
                'from': from_address,
                'to': token_address,
                'data': encoded_data
            })
            
            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': token_address,
                'value': 0,  # No ETH/BNB sent with token transfer
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'data': encoded_data,
                'chainId': web3_instance.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = web3_instance.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = web3_instance.eth.send_raw_transaction(self._get_raw_transaction(signed_txn))
            
            # Wait for transaction receipt
            receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt.gasUsed,
                    'explorer_url': f"{chain_config['explorer']}{tx_hash.hex()}",
                    'token_symbol': token_info['symbol']
                }
            else:
                return {'success': False, 'error': 'Transaction failed'}
                
        except Exception as e:
            logger.error(f"Error transferring ERC-20 tokens: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_token_info(self, web3_instance, contract_address):
        """Get basic token information (name, symbol, decimals)"""
        try:
            # ERC-20 function signatures
            name_signature = "0x06fdde03"      # name()
            symbol_signature = "0x95d89b41"    # symbol()
            decimals_signature = "0x313ce567"  # decimals()
            
            # Get name
            try:
                name_result = web3_instance.eth.call({
                    'to': contract_address,
                    'data': name_signature
                })
                # Handle different encoding possibilities
                if name_result:
                    try:
                        name = name_result.decode('utf-8').rstrip('\x00')
                    except UnicodeDecodeError:
                        try:
                            name = name_result.decode('ascii').rstrip('\x00')
                        except:
                            name = "Unknown Token"
                else:
                    name = "Unknown Token"
            except Exception:
                name = "Unknown Token"
            
            # Get symbol
            try:
                symbol_result = web3_instance.eth.call({
                    'to': contract_address,
                    'data': symbol_signature
                })
                # Handle different encoding possibilities
                if symbol_result:
                    try:
                        symbol = symbol_result.decode('utf-8').rstrip('\x00')
                    except UnicodeDecodeError:
                        try:
                            symbol = symbol_result.decode('ascii').rstrip('\x00')
                        except:
                            symbol = "UNKNOWN"
                else:
                    symbol = "UNKNOWN"
            except Exception:
                symbol = "UNKNOWN"
            
            # Get decimals
            try:
                decimals_result = web3_instance.eth.call({
                    'to': contract_address,
                    'data': decimals_signature
                })
                decimals = int.from_bytes(decimals_result, byteorder='big')
            except Exception:
                decimals = 18  # Default to 18 decimals
            
            # Validate that we got meaningful data
            if not name or name == "Unknown Token":
                name = f"Token ({contract_address[:8]}...)"
            if not symbol or symbol == "UNKNOWN":
                symbol = "UNKNOWN"
            
            return {
                'name': name,
                'symbol': symbol,
                'decimals': decimals
            }
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            # Return fallback info
            return {
                'name': f"Token ({contract_address[:8]}...)",
                'symbol': "UNKNOWN",
                'decimals': 18
            }
    
    def validate_address(self, address):
        """Validate Ethereum address format"""
        try:
            return Web3.is_address(address)
        except:
            return False
    
    def validate_amount(self, amount_str):
        """Validate amount format"""
        try:
            amount = float(amount_str)
            return amount > 0
        except ValueError:
            return False
    
    def get_chain_display_name(self, chain):
        """Get display name for chain"""
        display_names = {
            'ETH': 'Ethereum',
            'BSC': 'Binance Smart Chain',
            'BSC-TEST': 'BSC Testnet'
        }
        return display_names.get(chain, chain)
    
    def get_native_symbol(self, chain):
        """Get native token symbol for chain"""
        return self.chain_configs[chain]['native_symbol']
    
    def format_transfer_summary(self, transfer_type, chain, amount, token_symbol=None, to_address=None):
        """Format transfer summary for user confirmation"""
        chain_name = self.get_chain_display_name(chain)
        native_symbol = self.get_native_symbol(chain)
        
        if transfer_type == 'native':
            text = f"💰 Native {native_symbol} Transfer\n\n"
            text += f"🌐 Network: {chain_name}\n"
            text += f"💸 Amount: {amount} {native_symbol}\n"
        else:
            text = f"🪙 Token Transfer\n\n"
            text += f"🌐 Network: {chain_name}\n"
            text += f"🪙 Token: {token_symbol}\n"
            text += f"💸 Amount: {amount} {token_symbol}\n"
        
        if to_address:
            text += f"📍 To Address: `{to_address[:10]}...{to_address[-10:]}`\n"
        
        text += f"\n⚠️ Please confirm the details above before proceeding."
        
        return text

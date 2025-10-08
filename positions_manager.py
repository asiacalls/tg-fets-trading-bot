import asyncio
import aiohttp
import logging
from web3 import Web3
from decimal import Decimal
import json

logger = logging.getLogger(__name__)

class PositionsManager:
    def __init__(self):
        # API endpoints
        self.bsc_api_url = "https://bsc-mainnet.nodereal.io/v1/2cd6744897f3420786e87a4a1efb4baf"
        self.eth_api_url = "https://eth.blockscout.com/api/v2"
        self.dexview_api_url = "https://openapi.dexview.com/latest/dex/tokens"
        self.mobula_api_url = "https://explorer-api.mobula.io/api/1/wallet/portfolio"
        self.mobula_api_key = "42a362e2-3b37-425c-a9c5-1c938b828aa4"
        
        # Web3 instances for balance checking
        self.web3_instances = {}
        
        # Initialize Web3 connections
        self._initialize_web3()
    
    def _initialize_web3(self):
        """Initialize Web3 connections for different chains"""
        try:
            # BSC Mainnet
            self.web3_instances['BSC'] = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
            
            # Ethereum Mainnet
            self.web3_instances['ETH'] = Web3(Web3.HTTPProvider('https://eth.llamarpc.com/'))
            
            logger.info("✅ Web3 connections initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing Web3 connections: {e}")
    
    async def get_mobula_portfolio(self, wallet_address):
        """Get portfolio data from Mobula API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.mobula_api_key}'
            }
            
            params = {
                'wallet': wallet_address
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.mobula_api_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    else:
                        logger.error(f"Mobula API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching Mobula portfolio: {e}")
            return None
    
    async def format_mobula_portfolio_by_chain(self, portfolio_data):
        """Format Mobula portfolio data by chain"""
        try:
            if not portfolio_data or 'assets' not in portfolio_data:
                return {"BSC": [], "ETH": []}
            
            # Chain mapping from Mobula to our format
            chain_mapping = {
                'evm:56': 'BSC',  # BSC
                'evm:1': 'ETH',   # Ethereum
                '56': 'BSC',
                '1': 'ETH'
            }
            
            bsc_assets = []
            eth_assets = []
            
            for asset in portfolio_data['assets']:
                if asset['token_balance'] <= 0:  # Skip zero balance assets
                    continue
                
                # Determine chain from contracts_balances
                chain = 'BSC'  # Default to BSC
                for contract_balance in asset.get('contracts_balances', []):
                    chain_id = contract_balance.get('chainId', '')
                    if 'evm:1' in chain_id or chain_id == '1':
                        chain = 'ETH'
                        break
                    elif 'evm:56' in chain_id or chain_id == '56':
                        chain = 'BSC'
                        break
                
                # Format asset data
                asset_info = {
                    'symbol': asset['asset']['symbol'],
                    'name': asset['asset']['name'],
                    'balance': asset['token_balance'],
                    'price_usd': asset['price'],
                    'value_usd': asset['estimated_balance'],
                    'price_change_24h': asset['price_change_24h'],
                    'logo': asset['asset']['logo'],
                    'contract_address': asset['contracts_balances'][0]['address'] if asset.get('contracts_balances') else '',
                    'allocation': asset.get('allocation', 0)
                }
                
                if chain == 'BSC':
                    bsc_assets.append(asset_info)
                else:
                    eth_assets.append(asset_info)
            
            return {
                'BSC': bsc_assets,
                'ETH': eth_assets,
                'total_value': portfolio_data.get('total_wallet_balance', 0)
            }
            
        except Exception as e:
            logger.error(f"Error formatting Mobula portfolio: {e}")
            return {"BSC": [], "ETH": []}
    
    async def get_chain_portfolio(self, wallet_address, chain):
        """Get portfolio data for a specific chain using Mobula API"""
        try:
            # Get portfolio data from Mobula
            portfolio_data = await self.get_mobula_portfolio(wallet_address)
            
            if not portfolio_data:
                return []
            
            # Format data by chain
            formatted_data = await self.format_mobula_portfolio_by_chain(portfolio_data)
            
            # Return data for requested chain
            return formatted_data.get(chain.upper(), [])
            
        except Exception as e:
            logger.error(f"Error getting chain portfolio: {e}")
            return []
    
    async def get_bsc_token_holdings(self, wallet_address):
        """Fetch BSC token holdings using NodeReal API"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "nr_getTokenHoldings",
                "params": [wallet_address, "0x1", "0x12"],  # page 1, 18 items per page
                "id": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.bsc_api_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            return data['result']
                        else:
                            logger.error(f"BSC API error: {data}")
                            return None
                    else:
                        logger.error(f"BSC API request failed: {response.status}")
                        return None
                
        except Exception as e:
            logger.error(f"Error fetching BSC token holdings: {e}")
            return None
    
    async def get_eth_token_holdings(self, wallet_address):
        """Fetch ETH token holdings using Blockscout API"""
        try:
            api_url = f"{self.eth_api_url}/addresses/{wallet_address}/tokens?type=ERC-20"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    else:
                        logger.error(f"ETH API request failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching ETH token holdings: {e}")
            return []
    
    async def get_token_price_from_dexview(self, token_address, chain):
        """Get token price from DexView API"""
        try:
            # Map chain names for DexView API
            chain_mapping = {
                'ETH': 'ETH',
                'BSC': 'BSC'
            }
            
            mapped_chain = chain_mapping.get(chain, chain)
            api_url = f"{self.dexview_api_url}/{token_address}"
            
            params = {'chain': mapped_chain}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'pairs' and len(data['pairs']) > 0:
                            # Get the first pair (usually the most liquid)
                            pair = data['pairs'][0]
                            return {
                                'price_usd': pair.get('priceUsd', 0),
                                'price_native': pair.get('priceNative', 0),
                                'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                                'volume_24h': pair.get('volume', {}).get('h24', 0)
                            }
                        else:
                            return None
                    else:
                        logger.error(f"DexView API request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching token price from DexView: {e}")
            return None
    
    def get_token_balance(self, web3_instance, token_address, wallet_address, decimals):
        """Get token balance using Web3 contract call"""
        try:
            # ERC-20 balanceOf function signature
            balance_of_signature = "0x70a08231"  # balanceOf(address)
            
            # Encode the function call
            encoded_data = balance_of_signature + "000000000000000000000000" + wallet_address[2:]  # Remove 0x prefix
            
            # Make the call
            result = web3_instance.eth.call({
                'to': token_address,
                'data': encoded_data
            })
            
            if result:
                # Decode the result (32 bytes = 256 bits)
                balance = int.from_bytes(result, byteorder='big')
                # Convert to decimal with proper decimals
                balance_decimal = Decimal(balance) / Decimal(10 ** decimals)
                return float(balance_decimal)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0
    
    async def get_all_token_balances(self, wallet_address, chain):
        """Get all token balances for a specific chain using Mobula API"""
        try:
            # Use new Mobula API
            logger.info(f"Fetching {chain} token balances via Mobula API")
            balances = await self.get_chain_portfolio(wallet_address, chain)
            
            # Format the data to match the expected structure
            formatted_balances = []
            for asset in balances:
                formatted_balances.append({
                    'symbol': asset['symbol'],
                    'name': asset['name'],
                    'balance': asset['balance'],
                    'price_usd': asset['price_usd'],
                    'value_usd': asset['value_usd'],
                    'price_change_24h': asset['price_change_24h'],
                    'contract_address': asset['contract_address'],
                    'allocation': asset['allocation']
                })
            
            return {
                'chain': chain,
                'balances': formatted_balances,
                'total_value': sum(asset['value_usd'] for asset in formatted_balances)
            }
            
        except Exception as e:
            logger.error(f"Error getting token balances for {chain}: {e}")
            return {
                'chain': chain,
                'balances': [],
                'total_value': 0,
                'error': str(e)
            }
    
    async def _get_bsc_balances_fallback(self, wallet_address):
        """Fallback method for BSC balances (placeholder)"""
        # This is a placeholder - you'll need to implement with actual API key
        logger.info("BSC token holdings require API key implementation")
        return []
    
    async def _get_native_eth_balance(self, wallet_address):
        """Get native ETH balance"""
        try:
            web3_instance = self.web3_instances['ETH']
            balance_wei = web3_instance.eth.get_balance(wallet_address)
            balance_eth = web3_instance.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            logger.error(f"Error getting native ETH balance: {e}")
            return 0
    
    async def _get_native_bnb_balance(self, wallet_address):
        """Get native BNB balance"""
        try:
            web3_instance = self.web3_instances['BSC']
            balance_wei = web3_instance.eth.get_balance(wallet_address)
            balance_bnb = web3_instance.from_wei(balance_wei, 'ether')
            return float(balance_bnb)
        except Exception as e:
            logger.error(f"Error getting native BNB balance: {e}")
            return 0
    
    async def check_specific_contract_balance(self, wallet_address, contract_address, chain):
        """Check balance of a specific token contract"""
        try:
            if chain not in self.web3_instances:
                return {'error': f'Chain {chain} not supported'}
            
            web3_instance = self.web3_instances[chain]
            
            # Get token info (name, symbol, decimals)
            token_info = await self._get_token_info(web3_instance, contract_address)
            
            if not token_info:
                return {'error': 'Could not get token information'}
            
            # Get balance
            balance = self.get_token_balance(
                web3_instance, 
                contract_address, 
                wallet_address, 
                token_info['decimals']
            )
            
            if balance > 0:
                # Get price from DexView
                price_data = await self.get_token_price_from_dexview(contract_address, chain)
                
                # Only return if token has meaningful value
                price_usd = price_data['price_usd'] if price_data and price_data.get('price_usd') else 0
                value_usd = price_usd * balance if price_usd > 0 else 0
                
                # Filter out tokens with 0 or null values - only show tokens with actual USD value
                if value_usd > 0.01:  # Only show tokens worth more than $0.01
                    return {
                        'address': contract_address,
                        'name': token_info['name'],
                        'symbol': token_info['symbol'],
                        'decimals': token_info['decimals'],
                        'balance': balance,
                        'price_usd': price_usd,
                        'value_usd': value_usd,
                        'liquidity_usd': price_data['liquidity_usd'] if price_data else 0,
                        'volume_24h': price_data['volume_24h'] if price_data else 0,
                        'chain': chain
                    }
                else:
                    return {
                        'address': contract_address,
                        'name': token_info['name'],
                        'symbol': token_info['symbol'],
                        'decimals': token_info['decimals'],
                        'balance': 0,
                        'message': 'Token balance too low to display'
                    }
            else:
                return {
                    'address': contract_address,
                    'name': token_info['name'],
                    'symbol': token_info['symbol'],
                    'decimals': token_info['decimals'],
                    'balance': 0,
                    'message': 'No balance found for this token'
                }
                
        except Exception as e:
            logger.error(f"Error checking contract balance: {e}")
            return {'error': str(e)}
    
    async def _get_token_info(self, web3_instance, contract_address):
        """Get basic token information (name, symbol, decimals)"""
        try:
            # ERC-20 function signatures
            name_signature = "0x06fdde03"      # name()
            symbol_signature = "0x95d89b41"    # symbol()
            decimals_signature = "0x313ce567"  # decimals()
            
            # Get name
            name_result = web3_instance.eth.call({
                'to': contract_address,
                'data': name_signature
            })
            name = name_result.decode('utf-8').rstrip('\x00')
            
            # Get symbol
            symbol_result = web3_instance.eth.call({
                'to': contract_address,
                'data': symbol_signature
            })
            symbol = symbol_result.decode('utf-8').rstrip('\x00')
            
            # Get decimals
            decimals_result = web3_instance.eth.call({
                'to': contract_address,
                'data': decimals_signature
            })
            decimals = int.from_bytes(decimals_result, byteorder='big')
            
            return {
                'name': name,
                'symbol': symbol,
                'decimals': decimals
            }
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return None
    
    def format_balance_message(self, balance_data):
        """Format balance data into a readable message"""
        if not balance_data or 'balances' not in balance_data:
            return "❌ No token balances found or error occurred."
        
        chain = balance_data.get('chain', 'Unknown')
        balances = balance_data.get('balances', [])
        total_value = balance_data.get('total_value', 0)
        
        if not balances:
            return f"❌ No token balances found on {chain} chain."
        
        # Professional header with emoji
        chain_emoji = {'BSC': '🟡', 'ETH': '🔵'}
        chain_icon = chain_emoji.get(chain, '📊')
        text = f"{chain_icon} **{chain} Portfolio**\n"
        text += "─" * 20 + "\n\n"
        
        # Sort tokens by value (highest first)
        sorted_balances = sorted(balances, key=lambda x: x.get('value_usd', 0), reverse=True)
        
        for i, token in enumerate(sorted_balances):
            symbol = token['symbol']
            name = token['name']
            balance = token['balance']
            price = token.get('price_usd', 0)
            value = token.get('value_usd', 0)
            change = token.get('price_change_24h', 0)
            allocation = token.get('allocation', 0)
            
            # Check if it's a native token (BNB, ETH)
            is_native = symbol in ['BNB', 'ETH'] and token.get('contract_address', '').lower() in ['0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', '']
            
            # Professional token display with emojis
            text += f"🪙 **{symbol}** ({name})\n"
            text += f"💰 Balance: {balance:,.6f} {symbol}\n"
            text += f"💎 Value: ${value:,.2f}\n"
            
            # Price and change
            if price > 0:
                change_emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
                text += f"💵 Price: ${price:,.4f}"
                if change != 0:
                    text += f" {change_emoji} {change:+.2f}%\n"
                else:
                    text += f" {change_emoji}\n"
            
            # Allocation
            if allocation > 1:
                text += f"📊 Allocation: {allocation:.1f}%\n"
            
            # Contract address only for non-native tokens
            if not is_native and token.get('contract_address'):
                text += f"🔗 Contract: `{token['contract_address'][:10]}...{token['contract_address'][-6:]}`\n"
            
            # Add spacing between tokens
            if i < len(sorted_balances) - 1:
                text += "\n"
        
        # Professional footer with emoji
        if total_value > 0:
            text += "\n" + "─" * 20 + "\n"
            text += f"💎 **Total Value: ${total_value:,.2f}**"
            
            return text
    
    def format_contract_balance_message(self, balance_data):
        """Format contract balance data into a readable message"""
        if 'error' in balance_data:
            return f"❌ **Error:** {balance_data['error']}"
        
        if balance_data.get('balance', 0) == 0:
            return f"❌ **No Balance Found**\n\n📍 **Contract:** `{balance_data['address'][:10]}...`\n🪙 **Token:** {balance_data['symbol']} ({balance_data['name']})\n💰 **Balance:** 0"
        
        # Professional header with chain branding
        chain_emoji = {'BSC': '🟡', 'ETH': '🔵'}
        chain_icon = chain_emoji.get(balance_data.get('chain', ''), '⛓️')
        
        text = f"✅ **Token Balance Found**\n"
        text += "─" * 25 + "\n\n"
        
        # Token information
        text += f"🪙 **{balance_data['symbol']}** ({balance_data['name']})\n"
        text += f"{chain_icon} **{balance_data['chain']}** • `{balance_data['address'][:10]}...{balance_data['address'][-6:]}`\n\n"
        
        # Balance and value
        text += f"💰 **Balance:** {balance_data['balance']:,.6f} {balance_data['symbol']}\n"
        
        if balance_data.get('value_usd', 0) > 0:
            text += f"💎 **Value:** ${balance_data['value_usd']:,.2f}\n"
        
        # Price information
        if balance_data.get('price_usd') and balance_data['price_usd'] > 0:
            text += f"💵 **Price:** ${balance_data['price_usd']:,.6f}\n"
        
        # Additional metrics
        if balance_data.get('liquidity_usd') and balance_data['liquidity_usd'] > 0:
            text += f"💧 **Liquidity:** ${balance_data['liquidity_usd']:,.0f}\n"
        
        if balance_data.get('volume_24h') and balance_data['volume_24h'] > 0:
            text += f"📊 **24h Volume:** ${balance_data['volume_24h']:,.0f}\n"
        
        return text
    
    def get_positions_menu(self):
        """Get the positions menu keyboard"""
        return [
            [
                {'text': '🔵 ETH', 'callback_data': 'positions_chain_eth'},
                {'text': '🟡 BSC', 'callback_data': 'positions_chain_bsc'}
            ],
          
            [
                {'text': '🔙 Back to Main Menu', 'callback_data': 'main_menu'}
            ]
        ]

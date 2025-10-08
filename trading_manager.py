import json
import logging
from typing import Dict, Any, Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError, Web3ValidationError as ValidationError
from eth_account import Account
from config import PANCAKESWAP_CONTRACT, RPC_ENDPOINTS, TRADING_CONFIG

logger = logging.getLogger(__name__)

class TradingManager:
    def __init__(self):
        self.web3_instances = {}
        self.router_contracts = {}
        self.trading_contracts = {}  # New custom trading contracts
        self._initialize_contracts()
    
    def _initialize_contracts(self):
        """Initialize Web3 instances and router contracts for supported chains"""
        for chain in ['BSC', 'ETH', 'SEPOLIA']:
            if chain in RPC_ENDPOINTS:
                try:
                    # Initialize Web3
                    self.web3_instances[chain] = Web3(Web3.HTTPProvider(RPC_ENDPOINTS[chain]))
                    
                    # Add POA middleware for BSC (BSC uses Geth POA)
                    if chain == 'BSC':
                        try:
                            from web3.middleware import geth_poa_middleware
                            self.web3_instances[chain].middleware_onion.inject(geth_poa_middleware, layer=0)
                            logger.info(f"✅ Added POA middleware for {chain}")
                        except ImportError:
                            try:
                                # Try alternative import path for newer web3 versions
                                from web3.middleware.geth import geth_poa_middleware
                                self.web3_instances[chain].middleware_onion.inject(geth_poa_middleware, layer=0)
                                logger.info(f"✅ Added POA middleware for {chain} (alternative import)")
                            except ImportError:
                                try:
                                    # Try the most recent import path
                                    from web3.middleware import geth_poa_middleware
                                    self.web3_instances[chain].middleware_onion.inject(geth_poa_middleware, layer=0)
                                    logger.info(f"✅ Added POA middleware for {chain} (recent import)")
                                except ImportError:
                                    logger.warning(f"⚠️ Could not import POA middleware for {chain} - transactions may fail")
                                    # Try to install it if missing
                                    try:
                                        import subprocess
                                        subprocess.run(['pip3', 'install', 'web3[geth]'], check=True, capture_output=True)
                                        from web3.middleware import geth_poa_middleware
                                        self.web3_instances[chain].middleware_onion.inject(geth_poa_middleware, layer=0)
                                        logger.info(f"✅ Added POA middleware for {chain} after installation")
                                    except Exception as install_error:
                                        logger.error(f"❌ Failed to install POA middleware: {install_error}")
                    
                    # Check connection
                    if self.web3_instances[chain].is_connected():
                        logger.info(f"✅ Connected to {chain}")
                        
                        # Initialize router contract based on chain
                        if chain == 'BSC':
                            router_address = PANCAKESWAP_CONTRACT[chain]['router']
                            router_abi = self._get_router_abi()
                        elif chain in ['ETH', 'SEPOLIA']:
                            from config import UNISWAP_CONTRACT
                            router_address = UNISWAP_CONTRACT[chain]['router']
                            router_abi = self._get_uniswap_router_abi()
                        
                        self.router_contracts[chain] = self.web3_instances[chain].eth.contract(
                            address=Web3.to_checksum_address(router_address),
                            abi=router_abi
                        )
                        logger.info(f"✅ Router contract initialized for {chain}")
                        
                        # Initialize custom trading contract (placeholder addresses; update if needed)
                        if chain == 'BSC':
                            trading_contract_address = '0xec27f2173da0c7c7870a47bc545fa24ae72b7395'
                        elif chain == 'ETH':
                            trading_contract_address = '0xdbd7b068e21f28ca3d904ca4720786e6d6b08d47'
                        elif chain == 'SEPOLIA':
                            trading_contract_address = '0x0729E422d6a96c27a71239f5e2d4dFa4535e6996'
                        
                        trading_contract_abi = self._get_trading_contract_abi()
                        
                        self.trading_contracts[chain] = self.web3_instances[chain].eth.contract(
                            address=Web3.to_checksum_address(trading_contract_address) if trading_contract_address != '0x0000000000000000000000000000000000000000' else trading_contract_address,
                            abi=trading_contract_abi
                        )
                        logger.info(f"✅ Custom trading contract initialized for {chain}")
                    else:
                        logger.warning(f"❌ Could not connect to {chain}")
                        
                except Exception as e:
                    logger.error(f"❌ Error initializing {chain}: {e}")
    
    def _get_router_abi(self):
        """Get PancakeSwap router ABI"""
        return [
            {"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
            {"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},
            {"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
            {"stateMutability":"payable","type":"receive"}
        ]
    
    def _get_uniswap_router_abi(self):
        """Get Uniswap V2 router ABI"""
        return [
            {"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
            {"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},
            {"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts"}],"stateMutability":"payable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts"}],"stateMutability":"nonpayable","type":"function"},
            {"stateMutability":"payable","type":"receive"}
        ]
    
    def _get_trading_contract_abi(self):
        """Get custom trading contract ABI"""
        return [
            {"inputs":[{"internalType":"address","name":"_router","type":"address"},{"internalType":"address","name":"_wbnb","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
            {"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"oldFee","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"newFee","type":"uint256"}],"name":"FeeUpdated","type":"event"},
            {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"token","type":"address"}],"name":"FeeWithdrawn","type":"event"},
            {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},
            {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"oldRouter","type":"address"},{"indexed":True,"internalType":"address","name":"newRouter","type":"address"}],"name":"RouterUpdated","type":"event"},
            {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":True,"internalType":"address","name":"tokenIn","type":"address"},{"indexed":True,"internalType":"address","name":"tokenOut","type":"address"},{"indexed":False,"internalType":"uint256","name":"amountIn","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"amountOut","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"feeCollected","type":"uint256"}],"name":"SwapExecuted","type":"event"},
            {"inputs":[],"name":"BASIS_POINTS","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"calculateAmountAfterFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"calculateFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"dexRouter","outputs":[{"internalType":"contract IDEXRouter","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"emergencyWithdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[],"name":"feePercentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getBNBBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getFeePercentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getFeePercentageDecimal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getRouter","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"getTokenBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"getWBNB","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"newFee","type":"uint256"}],"name":"setFee","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"address","name":"newRouter","type":"address"}],"name":"setRouter","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[],"name":"wbnb","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdrawBNB","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdrawToken","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"stateMutability":"payable","type":"receive"}
        ]
    
    def get_token_price_estimate(self, chain: str, token_address: str, bnb_amount: float) -> Optional[Dict[str, Any]]:
        """Get estimated token amount for a given BNB amount"""
        try:
            if chain not in self.router_contracts:
                logger.error(f"Router not available for {chain}")
                return None
            
            web3 = self.web3_instances[chain]
            router = self.router_contracts[chain]
            
            logger.info(f"Getting price estimate for {bnb_amount} BNB -> {token_address[:20]}...")
            
            # Convert BNB amount to Wei
            bnb_amount_wei = web3.to_wei(bnb_amount, 'ether')
            logger.info(f"BNB amount in wei: {bnb_amount_wei}")
            
            # Create path: WBNB/WETH -> Token
            if chain == 'BSC':
                wbnb_address = PANCAKESWAP_CONTRACT[chain]['wbnb']
            elif chain in ['ETH', 'SEPOLIA']:
                from config import UNISWAP_CONTRACT
                wbnb_address = UNISWAP_CONTRACT[chain]['weth']
            else:
                logger.error(f"Unsupported chain: {chain}")
                return None
                
            path = [Web3.to_checksum_address(wbnb_address), Web3.to_checksum_address(token_address)]
            logger.info(f"Trading path: {' -> '.join(path)}")
            
            # Validate addresses
            if not web3.is_address(wbnb_address):
                logger.error(f"Invalid wrapped token address: {wbnb_address}")
                return None
            
            if not web3.is_address(token_address):
                logger.error(f"Invalid token address: {token_address}")
                return None
            
            # Check if router contract is properly initialized
            if not router:
                logger.error("Router contract not initialized")
                return None
            
            # Get amounts out with better error handling
            try:
                logger.info("Calling getAmountsOut...")
                amounts_out = router.functions.getAmountsOut(
                    bnb_amount_wei,
                    path
                ).call()
                logger.info(f"Amounts out received: {amounts_out}")
            except Exception as e:
                logger.error(f"Error calling getAmountsOut: {e}")
                # Try alternative method or provide fallback
                return None
            
            if amounts_out and len(amounts_out) >= 2:
                token_amount_wei = amounts_out[1]
                
                # Try to get token decimals for more accurate calculation
                try:
                    # ERC20 token contract for decimals
                    token_contract = web3.eth.contract(
                        address=Web3.to_checksum_address(token_address),
                        abi=[{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]
                    )
                    decimals = token_contract.functions.decimals().call()
                    # Convert using actual token decimals
                    token_amount = token_amount_wei / (10 ** decimals)
                    logger.info(f"Using token decimals: {decimals}")
                except Exception as e:
                    # Fallback to 18 decimals (most common)
                    logger.warning(f"Could not get token decimals, using fallback: {e}")
                    token_amount = web3.from_wei(token_amount_wei, 'ether')
                    decimals = 18
                
                logger.info(f"Price estimate: {bnb_amount} BNB -> {token_amount} tokens (decimals: {decimals})")
                logger.info(f"Raw amounts: {bnb_amount_wei} wei -> {token_amount_wei} wei")
                logger.info(f"Path: {' -> '.join(path)}")
                
                return {
                    'bnb_amount': bnb_amount,
                    'token_amount': token_amount,
                    'token_amount_wei': token_amount_wei,
                    'path': path
                }
            else:
                logger.error(f"Invalid amounts out response: {amounts_out}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting price estimate: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Try fallback estimation
            logger.info("Trying fallback price estimation...")
            fallback_estimate = self._get_fallback_price_estimate(chain, token_address, bnb_amount)
            if fallback_estimate:
                logger.info("Fallback estimation successful")
                return fallback_estimate
            
            return None
    
    def _get_fallback_price_estimate(self, chain: str, token_address: str, bnb_amount: float) -> Optional[Dict[str, Any]]:
        """Fallback price estimation method"""
        try:
            if chain not in self.web3_instances:
                return None
            
            web3 = self.web3_instances[chain]
            
            # Convert BNB amount to Wei
            bnb_amount_wei = web3.to_wei(bnb_amount, 'ether')
            
            # Simple estimation based on common token prices
            # This is a rough estimate and should not be used for actual trading
            estimated_tokens = bnb_amount * 1000  # Rough estimate: 1 BNB ≈ 1000 tokens
            
            logger.info(f"Fallback estimate: {bnb_amount} BNB -> ~{estimated_tokens} tokens")
            
            return {
                'bnb_amount': bnb_amount,
                'token_amount': estimated_tokens,
                'token_amount_wei': web3.to_wei(estimated_tokens, 'ether'),
                'path': ['WBNB', token_address[:20] + '...'],
                'is_fallback': True
            }
            
        except Exception as e:
            logger.error(f"Fallback estimation failed: {e}")
            return None

    def get_token_sell_estimate(self, chain: str, token_address: str, token_amount: float) -> Optional[Dict[str, Any]]:
        """Estimate native out for selling a given token amount."""
        try:
            if chain not in self.router_contracts:
                logger.error(f"Router not available for {chain}")
                return None
            web3 = self.web3_instances[chain]
            router = self.router_contracts[chain]

            # Determine wrapped native address
            if chain == 'BSC':
                wrapped_native = PANCAKESWAP_CONTRACT[chain]['wbnb']
            elif chain in ['ETH', 'SEPOLIA']:
                from config import UNISWAP_CONTRACT
                wrapped_native = UNISWAP_CONTRACT[chain]['weth']
            else:
                logger.error(f"Unsupported chain: {chain}")
                return None

            # Get token decimals
            token_contract = web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=[{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]
            )
            try:
                decimals = token_contract.functions.decimals().call()
            except Exception:
                decimals = 18

            amount_in_wei = int(token_amount * (10 ** decimals))
            path = [Web3.to_checksum_address(token_address), Web3.to_checksum_address(wrapped_native)]

            amounts_out = router.functions.getAmountsOut(amount_in_wei, path).call()
            if not amounts_out or len(amounts_out) < 2:
                return None

            native_out_wei = amounts_out[-1]
            native_out = float(web3.from_wei(native_out_wei, 'ether'))
            return {
                'token_amount': token_amount,
                'token_amount_wei': amount_in_wei,
                'native_out': native_out,
                'native_out_wei': native_out_wei,
                'path': path,
            }
        except Exception as e:
            logger.error(f"Error getting sell estimate: {e}")
            return None
    
    def buy_tokens(self, chain: str, token_address: str, bnb_amount: float, 
                   user_address: str, private_key: str, slippage: float = None) -> Dict[str, Any]:
        """Buy tokens with BNB using custom trading contract"""
        try:
            if chain not in self.trading_contracts:
                return {'success': False, 'error': f'Chain {chain} not supported'}
            
            # Use slippage from settings if not provided
            if slippage is None:
                slippage = TRADING_CONFIG.get(chain, {}).get('slippage', 0.5)
            
            web3 = self.web3_instances[chain]
            trading_contract = self.trading_contracts[chain]
            
            # Check if trading contract exists and has code
            try:
                contract_code = web3.eth.get_code(trading_contract.address)
                if contract_code == b'':
                    logger.error(f"Trading contract has no code at {trading_contract.address}")
                    return {'success': False, 'error': 'Trading contract not deployed or invalid'}
                logger.info(f"Trading contract validated at {trading_contract.address}")
            except Exception as e:
                logger.error(f"Error checking trading contract: {e}")
                return {'success': False, 'error': f'Trading contract validation error: {str(e)}'}
            
            # Validate inputs
            if not web3.is_address(token_address):
                return {'success': False, 'error': 'Invalid token address'}
            
            if bnb_amount <= 0:
                return {'success': False, 'error': 'Invalid BNB amount'}
            
            # Get price estimate
            price_estimate = self.get_token_price_estimate(chain, token_address, bnb_amount)
            if not price_estimate:
                return {'success': False, 'error': 'Could not get price estimate'}
            
            # Log amount calculations
            logger.info(f"🔢 BUY AMOUNT CALCULATIONS:")
            logger.info(f"   Input BNB Amount: {bnb_amount} BNB")
            logger.info(f"   Price Estimate: {price_estimate}")
            logger.info(f"   Token Amount (Wei): {price_estimate['token_amount_wei']}")
            logger.info(f"   Token Amount (Decimal): {price_estimate['token_amount_wei'] / 10**18}")
            logger.info(f"   Slippage: {slippage}%")
            
            # Calculate minimum tokens with slippage
            min_tokens = int(price_estimate['token_amount_wei'] * (1 - slippage / 100))
            # Ensure min_tokens is not negative or zero
            if min_tokens <= 0:
                min_tokens = int(price_estimate['token_amount_wei'] * 0.95)  # 5% slippage minimum
                logger.warning(f"Min tokens was {min_tokens}, adjusted to {min_tokens} (5% slippage)")
            logger.info(f"   Min Tokens (Wei): {min_tokens}")
            logger.info(f"   Min Tokens (Decimal): {min_tokens / 10**18}")
            
            # Convert BNB amount to Wei
            bnb_amount_wei = web3.to_wei(bnb_amount, 'ether')
            logger.info(f"   BNB Amount (Wei): {bnb_amount_wei}")
            logger.info(f"   BNB Amount (Decimal): {bnb_amount_wei / 10**18}")
            
            # Create path: WBNB/WETH -> Token
            if chain == 'BSC':
                wbnb_address = PANCAKESWAP_CONTRACT[chain]['wbnb']
            elif chain in ['ETH', 'SEPOLIA']:
                from config import UNISWAP_CONTRACT
                wbnb_address = UNISWAP_CONTRACT[chain]['weth']
            else:
                return {'success': False, 'error': f'Unsupported chain: {chain}'}
                
            path = [Web3.to_checksum_address(wbnb_address), Web3.to_checksum_address(token_address)]
            user_address_checksum = Web3.to_checksum_address(user_address)
            
            # Log path and addresses
            logger.info(f"🛤️  TRANSACTION PATH:")
            logger.info(f"   Chain: {chain}")
            logger.info(f"   Wrapped Native: {wbnb_address}")
            logger.info(f"   Token Address: {token_address}")
            logger.info(f"   Path: {path}")
            logger.info(f"   User Address: {user_address_checksum}")
            
            # Get current block timestamp + 20 minutes
            try:
                latest_block = web3.eth.get_block('latest')
                deadline = latest_block['timestamp'] + 1200
                logger.info(f"   Deadline: {deadline} (timestamp)")
            except Exception as e:
                logger.warning(f"Could not get latest block, using fallback deadline: {e}")
                import time
                deadline = int(time.time()) + 1200
                logger.info(f"   Fallback Deadline: {deadline} (timestamp)")
            
            # Try custom trading contract first, fallback to PancakeSwap router
            try:
                logger.info(f"🔄 Trying custom trading contract...")
                swap_function = trading_contract.functions.swapExactETHForTokens(
                    min_tokens,  # amountOutMin
                    path,        # path
                    user_address_checksum, # to
                    deadline     # deadline
                )
                logger.info(f"✅ Custom trading contract function created")
            except Exception as e:
                logger.warning(f"⚠️ Custom trading contract failed, falling back to PancakeSwap router: {e}")
                # Fallback to PancakeSwap router
                router = self.router_contracts[chain]
                swap_function = router.functions.swapExactETHForTokens(
                    min_tokens,  # amountOutMin
                    path,        # path
                    user_address_checksum, # to
                    deadline     # deadline
                )
                logger.info(f"✅ PancakeSwap router fallback function created")
            
            # Estimate gas with better error handling
            try:
                gas_estimate = swap_function.estimate_gas({
                    'from': user_address_checksum,
                    'value': bnb_amount_wei
                })
            except Exception as e:
                error_msg = str(e)
                if 'Panic error 0x11' in error_msg:
                    logger.error(f"Arithmetic underflow/overflow in gas estimation. Check token amounts and slippage: {e}")
                    return {'success': False, 'error': 'Invalid token amounts or slippage causing arithmetic error. Please try with different amounts.'}
                elif 'INSUFFICIENT_OUTPUT_AMOUNT' in error_msg.upper():
                    logger.error(f"Insufficient output amount during gas estimation: {e}")
                    return {'success': False, 'error': 'Insufficient output amount. Try increasing slippage or reducing amount.'}
                elif 'UNISWAPV2: K' in error_msg.upper():
                    logger.warning(f"UniswapV2 K error during gas estimation, trying with higher slippage: {e}")
                    # Try gas estimation with higher slippage tolerance
                    try:
                        # Increase slippage buffer for gas estimation
                        min_tokens_gas_retry = int(min_tokens * 0.70)  # 30% slippage for gas estimation
                        logger.info(f"Retrying gas estimation with min_tokens: {min_tokens_gas_retry}")
                        
                        # Rebuild swap function with higher slippage for gas estimation
                        try:
                            swap_function_gas_retry = trading_contract.functions.swapExactETHForTokens(
                                min_tokens_gas_retry,
                                path,
                                user_address_checksum,
                                deadline
                            )
                        except Exception:
                            swap_function_gas_retry = router.functions.swapExactETHForTokens(
                                min_tokens_gas_retry,
                                path,
                                user_address_checksum,
                                deadline
                            )
                        
                        gas_estimate = swap_function_gas_retry.estimate_gas({
                            'from': user_address_checksum,
                            'value': bnb_amount_wei
                        })
                        logger.info(f"Gas estimation successful with higher slippage: {gas_estimate}")
                    except Exception as e2:
                        logger.warning(f"Buy gas estimation failed with 30% slippage, trying with 50% slippage: {e2}")
                        # Try with even more aggressive slippage
                        try:
                            min_tokens_gas_retry2 = int(min_tokens * 0.50)  # 50% slippage for gas estimation
                            logger.info(f"Retrying buy gas estimation with 50% slippage, min_tokens: {min_tokens_gas_retry2}")
                            
                            # Rebuild swap function with even higher slippage
                            try:
                                swap_function_gas_retry2 = trading_contract.functions.swapExactETHForTokens(
                                    min_tokens_gas_retry2,
                                    path,
                                    user_address_checksum,
                                    deadline
                                )
                            except Exception:
                                swap_function_gas_retry2 = router.functions.swapExactETHForTokens(
                                    min_tokens_gas_retry2,
                                    path,
                                    user_address_checksum,
                                    deadline
                                )
                            
                            gas_estimate = swap_function_gas_retry2.estimate_gas({
                                'from': user_address_checksum,
                                'value': bnb_amount_wei
                            })
                            logger.info(f"Buy gas estimation successful with 50% slippage: {gas_estimate}")
                        except Exception as e3:
                            logger.error(f"Buy gas estimation failed even with 50% slippage: {e3}")
                            # Calculate suggested smaller trade size
                            suggested_amount = bnb_amount * 0.1  # 10% of original amount
                            return {'success': False, 'error': f'Severe pool liquidity issue (UniswapV2: K). This trade cannot be executed due to:\n• Extremely low liquidity in the pool\n• Trade size too large for available reserves\n• Pool may be nearly empty\n\nSuggested solution:\n• Try buying with {suggested_amount:.6f} BNB instead of {bnb_amount}\n• Or reduce trade size by 90% or more\n• Try a different token pair\n• Wait for liquidity to improve\n• Use a different DEX or network'}
                else:
                    logger.warning(f"Gas estimation failed, using default: {e}")
                gas_estimate = 300000  # Default gas limit for swaps
            
            # Get gas price with fallback - use higher gas price for faster transactions
            try:
                current_gas_price = web3.eth.gas_price
                # Use 150% of current gas price for faster confirmation
                gas_price = int(current_gas_price * 1.5)
                logger.info(f"Using boosted gas price: {web3.from_wei(gas_price, 'gwei')} gwei (150% of current: {web3.from_wei(current_gas_price, 'gwei')} gwei)")
            except Exception as e:
                logger.warning(f"Gas price fetch failed, using high default: {e}")
                # Use higher default gas price for faster transactions
                gas_price = web3.to_wei(20, 'gwei') if chain == 'ETH' else web3.to_wei(10, 'gwei')  # Higher default gas price
            
            # Get nonce with fallback - use 'pending' to include unconfirmed transactions
            try:
                nonce = web3.eth.get_transaction_count(user_address_checksum, 'pending')
                logger.info(f"Using pending nonce: {nonce}")
            except Exception as e:
                try:
                    # Fallback to confirmed nonce
                    nonce = web3.eth.get_transaction_count(user_address_checksum)
                    logger.info(f"Using confirmed nonce: {nonce}")
                except Exception as e2:
                    logger.warning(f"Nonce fetch failed, using default: {e2}")
                    nonce = 0
            
            # Build transaction
            try:
                transaction = swap_function.build_transaction({
                    'from': user_address_checksum,
                    'value': bnb_amount_wei,
                    'gas': int(gas_estimate * 1.5),  # Add 50% buffer for faster processing
                    'gasPrice': gas_price,
                    'nonce': nonce
                })
                logger.info(f"Transaction built successfully: {transaction}")
            except Exception as e:
                logger.error(f"Error building transaction: {e}")
                return {'success': False, 'error': f'Transaction build error: {str(e)}'}
            
            # Sign transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction with fallback for INSUFFICIENT_OUTPUT_AMOUNT
            def _extract_raw_tx(signed):
                try:
                    return signed.raw_transaction
                except AttributeError:
                    return signed.rawTransaction if hasattr(signed, 'rawTransaction') else signed.raw_transaction

            try:
                tx_hash = web3.eth.send_raw_transaction(_extract_raw_tx(signed_txn))
            except Exception as e:
                if 'INSUFFICIENT_OUTPUT_AMOUNT' in str(e).upper() or 'UNISWAPV2: K' in str(e).upper():
                    error_type = "INSUFFICIENT_OUTPUT_AMOUNT" if 'INSUFFICIENT_OUTPUT_AMOUNT' in str(e).upper() else "UniswapV2: K"
                    logger.warning(f"Retrying with increased slippage due to {error_type}")
                    
                    # Increase slippage buffer and rebuild
                    if 'UNISWAPV2: K' in str(e).upper():
                        min_tokens_retry = int(min_tokens * 0.80)  # additional ~20% buffer for K error
                    else:
                        min_tokens_retry = int(min_tokens * 0.85)  # additional ~15% buffer for insufficient output
                    
                    try:
                        # Manually override amountOutMin in input data if applicable is complex.
                        # Safer: rebuild swap_function with new min_tokens_retry
                        try:
                            swap_function_retry = trading_contract.functions.swapExactETHForTokens(
                                min_tokens_retry,
                                path,
                                user_address_checksum,
                                deadline
                            )
                        except Exception:
                            swap_function_retry = router.functions.swapExactETHForTokens(
                                min_tokens_retry,
                                path,
                                user_address_checksum,
                                deadline
                            )
                        transaction_retry = swap_function_retry.build_transaction({
                            'from': user_address_checksum,
                            'value': bnb_amount_wei,
                            'gas': int(gas_estimate * 1.6),  # Higher buffer for retry
                            'gasPrice': gas_price,
                            'nonce': nonce
                        })
                        signed_txn_retry = web3.eth.account.sign_transaction(transaction_retry, private_key)
                        tx_hash = web3.eth.send_raw_transaction(_extract_raw_tx(signed_txn_retry))
                    except Exception as e2:
                        logger.error(f"Retry failed: {e2}")
                        return {'success': False, 'error': f'{error_type} - retry failed: {str(e2)}'}
                else:
                    logger.error(f"Send transaction failed: {e}")
                    return {'success': False, 'error': f'Transaction send error: {str(e)}'}
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'bnb_amount': bnb_amount,
                'estimated_tokens': price_estimate['token_amount'],
                'min_tokens': web3.from_wei(min_tokens, 'ether'),
                'gas_estimate': gas_estimate,
                'path': path
            }
            
        except ContractLogicError as e:
            logger.error(f"Contract logic error: {e}")
            return {'success': False, 'error': f'Contract error: {str(e)}'}
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            # Check if it's a POA chain error
            if "extraData" in str(e) and "POA" in str(e):
                return {'success': False, 'error': 'POA chain error - please ensure proper middleware is configured'}
            return {'success': False, 'error': f'Validation error: {str(e)}'}
        except Exception as e:
            logger.error(f"Error buying tokens: {e}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def sell_tokens(self, chain: str, token_address: str, token_amount: float,
                    user_address: str, private_key: str, slippage: float = None) -> Dict[str, Any]:
        """Sell tokens for BNB using custom trading contract"""
        try:
            if chain not in self.trading_contracts:
                return {'success': False, 'error': f'Chain {chain} not supported'}
            
            # Use slippage from settings if not provided
            if slippage is None:
                slippage = TRADING_CONFIG.get(chain, {}).get('slippage', 0.5)
            
            web3 = self.web3_instances[chain]
            trading_contract = self.trading_contracts[chain]
            
            # Check if trading contract exists and has code
            try:
                contract_code = web3.eth.get_code(trading_contract.address)
                if contract_code == b'':
                    logger.error(f"Trading contract has no code at {trading_contract.address}")
                    return {'success': False, 'error': 'Trading contract not deployed or invalid'}
                logger.info(f"Trading contract validated at {trading_contract.address}")
            except Exception as e:
                logger.error(f"Error checking trading contract: {e}")
                return {'success': False, 'error': f'Trading contract validation error: {str(e)}'}
            
            native_symbol = 'ETH' if chain in ['ETH', 'SEPOLIA'] else 'BNB'
            logger.info(f"Selling {token_amount} tokens of {token_address[:20]}... for {native_symbol}")
            
            # Validate inputs
            if not web3.is_address(token_address):
                return {'success': False, 'error': 'Invalid token address'}
            
            if token_amount <= 0:
                return {'success': False, 'error': 'Invalid token amount'}
            
            # Get token decimals and convert token amount to Wei
            try:
                decimals_abi = [{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]
                decimals_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=decimals_abi)
                decimals = decimals_contract.functions.decimals().call()
                token_amount_wei = int(token_amount * (10 ** decimals))
                logger.info(f"Token decimals: {decimals}, converted {token_amount} tokens to {token_amount_wei} wei")
            except Exception as e:
                logger.warning(f"Could not get token decimals, using 18 as fallback: {e}")
                token_amount_wei = web3.to_wei(token_amount, 'ether')
                decimals = 18
            
            # Log amount calculations
            logger.info(f"🔢 SELL AMOUNT CALCULATIONS:")
            logger.info(f"   Input Token Amount: {token_amount} tokens")
            logger.info(f"   Token Amount (Wei): {token_amount_wei}")
            logger.info(f"   Token Amount (Decimal): {token_amount_wei / 10**decimals}")
            logger.info(f"   Slippage: {slippage}%")
            
            # Check if user has enough tokens
            token_balance = self._get_token_balance(chain, token_address, user_address)
            # Format balance for logging to avoid scientific notation
            formatted_balance_log = f"{token_balance:.8f}".rstrip('0').rstrip('.')
            logger.info(f"   User Token Balance: {formatted_balance_log} tokens")
            if token_balance < token_amount:
                # Format balance to avoid scientific notation for small numbers
                formatted_balance = f"{token_balance:.8f}".rstrip('0').rstrip('.')
                return {'success': False, 'error': f'Insufficient token balance. You have {formatted_balance} tokens. Please buy more tokens first or reduce the amount you want to sell.'}
            
            # Check and set token approval for the trading contract
            if chain == 'BSC':
                trading_contract_address = '0xec27f2173da0c7c7870a47bc545fa24ae72b7395'
            elif chain == 'ETH':
                trading_contract_address = '0xdbd7b068e21f28ca3d904ca4720786e6d6b08d47'
            elif chain == 'SEPOLIA':
                trading_contract_address = '0x0729E422d6a96c27a71239f5e2d4dFa4535e6996'
            else:
                return {'success': False, 'error': f'Unsupported chain: {chain}'}
            approval_result = self._ensure_token_approval_for_contract(chain, token_address, user_address, private_key, token_amount_wei, trading_contract_address)
            if not approval_result['success']:
                return approval_result
            
            # Create path: Token -> WBNB/WETH
            if chain == 'BSC':
                wbnb_address = PANCAKESWAP_CONTRACT[chain]['wbnb']
            elif chain in ['ETH', 'SEPOLIA']:
                from config import UNISWAP_CONTRACT
                wbnb_address = UNISWAP_CONTRACT[chain]['weth']
            else:
                return {'success': False, 'error': f'Unsupported chain: {chain}'}
                
            path = [Web3.to_checksum_address(token_address), Web3.to_checksum_address(wbnb_address)]
            
            # Log path and addresses for sell
            logger.info(f"🛤️  SELL TRANSACTION PATH:")
            logger.info(f"   Chain: {chain}")
            logger.info(f"   Token Address: {token_address}")
            logger.info(f"   Wrapped Native: {wbnb_address}")
            logger.info(f"   Path: {path}")
            logger.info(f"   User Address: {user_address}")
            
            # Get current block timestamp + 20 minutes with fallback
            try:
                latest_block = web3.eth.get_block('latest')
                deadline = latest_block['timestamp'] + 1200
                logger.info(f"   Deadline: {deadline} (timestamp)")
            except Exception as e:
                logger.warning(f"Could not get latest block, using fallback deadline: {e}")
                import time
                deadline = int(time.time()) + 1200
                logger.info(f"   Fallback Deadline: {deadline} (timestamp)")
            
            # Get price estimate for sell
            sell_estimate = self.get_token_sell_estimate(chain, token_address, token_amount)
            if sell_estimate:
                min_native = int(sell_estimate['native_out_wei'] * (1 - slippage / 100))
                # Ensure min_native is not negative or zero
                if min_native <= 0:
                    min_native = int(sell_estimate['native_out_wei'] * 0.95)  # 5% slippage minimum
                    logger.warning(f"Min native was {min_native}, adjusted to {min_native} (5% slippage)")
                logger.info(f"💰 SELL PRICE ESTIMATE:")
                logger.info(f"   Estimated {native_symbol}: {sell_estimate['native_out_wei'] / 10**18}")
                logger.info(f"   Min {native_symbol} (Wei): {min_native}")
                logger.info(f"   Min {native_symbol} (Decimal): {min_native / 10**18}")
            else:
                min_native = 0
                logger.warning(f"⚠️ Could not get sell price estimate, using 0 as min amount")
            
            # Try custom trading contract first, fallback to PancakeSwap router
            try:
                logger.info(f"🔄 Trying custom trading contract for sell...")
                swap_function = trading_contract.functions.swapExactTokensForETH(
                    token_amount_wei,  # amountIn
                    min_native,        # amountOutMin (calculated with slippage)
                    path,              # path
                    user_address,      # to
                    deadline          # deadline
                )
                logger.info(f"✅ Custom trading contract sell function created")
            except Exception as e:
                logger.warning(f"⚠️ Custom trading contract sell failed, falling back to PancakeSwap router: {e}")
                # Fallback to PancakeSwap router
                router = self.router_contracts[chain]
                swap_function = router.functions.swapExactTokensForETH(
                    token_amount_wei,  # amountIn
                    min_native,        # amountOutMin (calculated with slippage)
                    path,              # path
                    user_address,      # to
                    deadline          # deadline
                )
                logger.info(f"✅ PancakeSwap router sell fallback function created")
            
            # Estimate gas with better error handling
            try:
                gas_estimate = swap_function.estimate_gas({
                    'from': user_address,
                    'value': 0
                })
            except Exception as e:
                error_msg = str(e)
                if 'Panic error 0x11' in error_msg:
                    logger.error(f"Arithmetic underflow/overflow in gas estimation. Check token amounts and slippage: {e}")
                    return {'success': False, 'error': 'Invalid token amounts or slippage causing arithmetic error. Please try with different amounts.'}
                elif 'INSUFFICIENT_OUTPUT_AMOUNT' in error_msg.upper():
                    logger.error(f"Insufficient output amount during gas estimation: {e}")
                    return {'success': False, 'error': 'Insufficient output amount. Try increasing slippage or reducing amount.'}
                elif 'UNISWAPV2: K' in error_msg.upper():
                    logger.warning(f"UniswapV2 K error during sell gas estimation, trying with higher slippage: {e}")
                    # Try gas estimation with higher slippage tolerance
                    try:
                        # Increase slippage buffer for gas estimation (for sell operation)
                        min_native_gas_retry = int(min_native * 0.70)  # 30% slippage for gas estimation
                        logger.info(f"Retrying sell gas estimation with min_native: {min_native_gas_retry}")
                        
                        # Rebuild swap function with higher slippage for gas estimation
                        try:
                            swap_function_gas_retry = trading_contract.functions.swapExactTokensForETH(
                                token_amount_wei,
                                min_native_gas_retry,
                                path,
                                user_address,
                                deadline
                            )
                        except Exception:
                            swap_function_gas_retry = router.functions.swapExactTokensForETH(
                                token_amount_wei,
                                min_native_gas_retry,
                                path,
                                user_address,
                                deadline
                            )
                        
                        gas_estimate = swap_function_gas_retry.estimate_gas({
                            'from': user_address,
                            'value': 0
                        })
                        logger.info(f"Sell gas estimation successful with higher slippage: {gas_estimate}")
                    except Exception as e2:
                        logger.warning(f"Sell gas estimation failed with 30% slippage, trying with 50% slippage: {e2}")
                        # Try with even more aggressive slippage
                        try:
                            min_native_gas_retry2 = int(min_native * 0.50)  # 50% slippage for gas estimation
                            logger.info(f"Retrying sell gas estimation with 50% slippage, min_native: {min_native_gas_retry2}")
                            
                            # Rebuild swap function with even higher slippage
                            try:
                                swap_function_gas_retry2 = trading_contract.functions.swapExactTokensForETH(
                                    token_amount_wei,
                                    min_native_gas_retry2,
                                    path,
                                    user_address,
                                    deadline
                                )
                            except Exception:
                                swap_function_gas_retry2 = router.functions.swapExactTokensForETH(
                                    token_amount_wei,
                                    min_native_gas_retry2,
                                    path,
                                    user_address,
                                    deadline
                                )
                            
                            gas_estimate = swap_function_gas_retry2.estimate_gas({
                                'from': user_address,
                                'value': 0
                            })
                            logger.info(f"Sell gas estimation successful with 50% slippage: {gas_estimate}")
                        except Exception as e3:
                            logger.error(f"Sell gas estimation failed even with 50% slippage: {e3}")
                            # Calculate suggested smaller trade size
                            suggested_amount = token_amount * 0.1  # 10% of original amount
                            return {'success': False, 'error': f'Severe pool liquidity issue (UniswapV2: K). This trade cannot be executed due to:\n• Extremely low liquidity in the pool\n• Trade size too large for available reserves\n• Pool may be nearly empty\n\nSuggested solution:\n• Try selling {suggested_amount:.6f} tokens instead of {token_amount}\n• Or reduce trade size by 90% or more\n• Try a different token pair\n• Wait for liquidity to improve\n• Use a different DEX or network'}
                else:
                    logger.warning(f"Gas estimation failed, using default: {e}")
                gas_estimate = 300000  # Default gas limit for swaps
            
            # Get gas price with fallback - use higher gas price for faster transactions
            try:
                current_gas_price = web3.eth.gas_price
                # Use 150% of current gas price for faster confirmation
                gas_price = int(current_gas_price * 1.5)
                logger.info(f"Using boosted gas price: {web3.from_wei(gas_price, 'gwei')} gwei (150% of current: {web3.from_wei(current_gas_price, 'gwei')} gwei)")
            except Exception as e:
                logger.warning(f"Gas price fetch failed, using high default: {e}")
                # Use higher default gas price for faster transactions
                gas_price = web3.to_wei(20, 'gwei') if chain == 'ETH' else web3.to_wei(10, 'gwei')  # Higher default gas price
            
            # Get nonce with fallback - use 'pending' to include unconfirmed transactions
            try:
                nonce = web3.eth.get_transaction_count(user_address, 'pending')
                logger.info(f"Using pending nonce: {nonce}")
            except Exception as e:
                try:
                    # Fallback to confirmed nonce
                    nonce = web3.eth.get_transaction_count(user_address)
                    logger.info(f"Using confirmed nonce: {nonce}")
                except Exception as e2:
                    logger.warning(f"Nonce fetch failed, using default: {e2}")
                    nonce = 0
            
            # Build transaction
            transaction = swap_function.build_transaction({
                'from': user_address,
                'value': 0,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': nonce
            })
            
            # Sign transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction - handle both old and new web3 versions
            try:
                # Try new attribute name first
                raw_tx = signed_txn.raw_transaction
            except AttributeError:
                try:
                    # Try old attribute name
                    raw_tx = signed_txn.rawTransaction
                except AttributeError:
                    # Fallback: try to get raw transaction data
                    raw_tx = signed_txn.rawTransaction if hasattr(signed_txn, 'rawTransaction') else signed_txn.raw_transaction
            
            # Send transaction with retry logic for nonce issues and UniswapV2: K errors
            try:
                tx_hash = self._send_transaction_with_retry(web3, signed_txn)
            except Exception as e:
                if 'UNISWAPV2: K' in str(e).upper() or 'INSUFFICIENT_OUTPUT_AMOUNT' in str(e).upper():
                    error_type = "UniswapV2: K" if 'UNISWAPV2: K' in str(e).upper() else "INSUFFICIENT_OUTPUT_AMOUNT"
                    logger.warning(f"Retrying sell with increased slippage due to {error_type}")
                    
                    # Increase slippage buffer and rebuild
                    if 'UNISWAPV2: K' in str(e).upper():
                        min_native_retry = int(min_native * 0.80)  # additional ~20% buffer for K error
                    else:
                        min_native_retry = int(min_native * 0.85)  # additional ~15% buffer for insufficient output
                    
                    try:
                        # Rebuild swap function with new min_native_retry
                        try:
                            swap_function_retry = trading_contract.functions.swapExactTokensForETH(
                                token_amount_wei,
                                min_native_retry,
                                path,
                                user_address,
                                deadline
                            )
                        except Exception:
                            swap_function_retry = router.functions.swapExactTokensForETH(
                                token_amount_wei,
                                min_native_retry,
                                path,
                                user_address,
                                deadline
                            )
                        
                        transaction_retry = swap_function_retry.build_transaction({
                            'from': user_address,
                            'value': 0,
                            'gas': int(gas_estimate * 1.6),  # Higher buffer for retry
                            'gasPrice': gas_price,
                            'nonce': nonce
                        })
                        signed_txn_retry = web3.eth.account.sign_transaction(transaction_retry, private_key)
                        tx_hash = self._send_transaction_with_retry(web3, signed_txn_retry)
                    except Exception as e2:
                        logger.error(f"Sell retry failed: {e2}")
                        return {'success': False, 'error': f'{error_type} - retry failed: {str(e2)}'}
                else:
                    logger.error(f"Sell transaction failed: {e}")
                    return {'success': False, 'error': f'Sell transaction error: {str(e)}'}
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'token_amount': token_amount,
                'gas_estimate': gas_estimate,
                'path': path
            }
            
        except ContractLogicError as e:
            logger.error(f"Contract logic error: {e}")
            return {'success': False, 'error': f'Contract error: {str(e)}'}
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': f'Validation error: {str(e)}'}
        except Exception as e:
            logger.error(f"Error selling tokens: {e}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def get_transaction_status(self, chain: str, tx_hash: str) -> Dict[str, Any]:
        """Get transaction status and details"""
        try:
            if chain not in self.web3_instances:
                return {'success': False, 'error': f'Chain {chain} not supported'}
            
            web3 = self.web3_instances[chain]
            
            # Get transaction receipt
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            
            if receipt:
                return {
                    'success': True,
                    'status': 'success' if receipt['status'] == 1 else 'failed',
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'effective_gas_price': receipt['effectiveGasPrice'],
                    'contract_address': receipt.get('contractAddress'),
                    'logs': len(receipt['logs'])
                }
            else:
                return {'success': False, 'error': 'Transaction not found or pending'}
                
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return {'success': False, 'error': f'Error: {str(e)}'}
    
    def validate_token_address(self, chain: str, token_address: str) -> bool:
        """Validate if a token address is valid and tradeable"""
        try:
            if chain not in self.web3_instances:
                return False
            
            web3 = self.web3_instances[chain]
            # Normalize to checksum address
            try:
                checksum_address = Web3.to_checksum_address(token_address)
            except Exception:
                return False
            
            # Check if contract exists
            code = web3.eth.get_code(checksum_address)
            if code == b'':
                return False
            
            # Check if token has basic ERC20 functions
            try:
                token_contract = web3.eth.contract(
                    address=checksum_address,
                    abi=[
                        {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
                        {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"}
                    ]
                )
                
                # Try to call basic functions
                decimals = token_contract.functions.decimals().call()
                symbol = token_contract.functions.symbol().call()
                
                logger.info(f"Token validation: {token_address[:20]}... - Decimals: {decimals}, Symbol: {symbol}")
                return True
                
            except Exception as e:
                logger.warning(f"Token validation failed for {token_address[:20]}...: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error validating token address: {e}")
            return False
    
    def get_token_info(self, chain: str, token_address: str) -> Optional[Dict[str, Any]]:
        """Get detailed token information"""
        try:
            if chain not in self.web3_instances:
                return None
            
            web3 = self.web3_instances[chain]
            
            # Basic ERC20 ABI
            erc20_abi = [
                {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
                {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
                {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
                {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}
            ]
            
            token_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
            
            info = {
                'address': token_address,
                'decimals': token_contract.functions.decimals().call(),
                'symbol': token_contract.functions.symbol().call(),
                'name': token_contract.functions.name().call(),
                'total_supply': token_contract.functions.totalSupply().call()
            }
            
            logger.info(f"Token info: {info['symbol']} ({info['name']}) - Decimals: {info['decimals']}")
            return info
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return None
    
    def _get_token_balance(self, chain: str, token_address: str, user_address: str) -> float:
        """Get token balance for a user"""
        try:
            if chain not in self.web3_instances:
                return 0.0
            
            web3 = self.web3_instances[chain]
            
            # ERC20 balanceOf function
            balance_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
            
            token_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=balance_abi)
            balance_wei = token_contract.functions.balanceOf(Web3.to_checksum_address(user_address)).call()
            
            # Get token decimals
            try:
                decimals_abi = [{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]
                decimals_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=decimals_abi)
                decimals = decimals_contract.functions.decimals().call()
                balance = balance_wei / (10 ** decimals)
                logger.info(f"Token decimals: {decimals}, balance_wei: {balance_wei}, calculated balance: {balance}")
            except Exception as e:
                logger.warning(f"Could not get token decimals, using 18 as fallback: {e}")
                # Fallback to 18 decimals
                balance = web3.from_wei(balance_wei, 'ether')
            
            # Format balance for logging to avoid scientific notation
            formatted_balance = f"{balance:.8f}".rstrip('0').rstrip('.')
            logger.info(f"Token balance: {formatted_balance} tokens")
            return float(balance)
            
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0.0
    
    def _ensure_token_approval(self, chain: str, token_address: str, user_address: str, 
                              private_key: str, amount: int) -> Dict[str, Any]:
        """Ensure token approval for PancakeSwap router (legacy method)"""
        router_address = PANCAKESWAP_CONTRACT[chain]['router']
        return self._ensure_token_approval_for_contract(chain, token_address, user_address, private_key, amount, router_address)
    
    def _ensure_token_approval_for_contract(self, chain: str, token_address: str, user_address: str, 
                                          private_key: str, amount: int, spender_address: str) -> Dict[str, Any]:
        """Ensure token approval for a specific contract"""
        try:
            if chain not in self.web3_instances:
                return {'success': False, 'error': f'Chain {chain} not supported'}
            
            web3 = self.web3_instances[chain]
            
            # ERC20 approve function
            approve_abi = [
                {"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
                {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
            ]
            
            token_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=approve_abi)
            
            # Check current allowance
            current_allowance = token_contract.functions.allowance(
                Web3.to_checksum_address(user_address),
                Web3.to_checksum_address(spender_address)
            ).call()
            
            if current_allowance >= amount:
                logger.info(f"Token already approved for {spender_address[:20]}... Allowance: {current_allowance}, Required: {amount}")
                return {'success': True, 'message': 'Token already approved'}
            
            logger.info(f"Setting token approval for {spender_address[:20]}... Current: {current_allowance}, Setting: {amount}")
            
            # Build approval transaction
            approve_function = token_contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                amount
            )
            
            # Estimate gas
            try:
                gas_estimate = approve_function.estimate_gas({'from': Web3.to_checksum_address(user_address)})
            except Exception as e:
                logger.warning(f"Gas estimation failed, using default: {e}")
                gas_estimate = 50000  # Default gas for approvals
            
            # Get gas price
            try:
                gas_price = web3.eth.gas_price
            except Exception as e:
                logger.warning(f"Gas price fetch failed, using default: {e}")
                gas_price = web3.to_wei(5, 'gwei')
            
            # Get nonce
            try:
                nonce = web3.eth.get_transaction_count(user_address, 'pending')
                logger.info(f"Using pending nonce for approval: {nonce}")
            except Exception as e:
                try:
                    # Fallback to confirmed nonce
                    nonce = web3.eth.get_transaction_count(user_address)
                    logger.info(f"Using confirmed nonce for approval: {nonce}")
                except Exception as e2:
                    logger.warning(f"Nonce fetch failed, using default: {e2}")
                    nonce = 0
            
            # Build transaction
            transaction = approve_function.build_transaction({
                'from': Web3.to_checksum_address(user_address),
                'gas': int(gas_estimate * 1.2),
                'gasPrice': gas_price,
                'nonce': nonce
            })
            
            # Sign and send approval transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
            
            # Handle both old and new web3 versions
            try:
                raw_tx = signed_txn.raw_transaction
            except AttributeError:
                try:
                    raw_tx = signed_txn.rawTransaction
                except AttributeError:
                    raw_tx = signed_txn.rawTransaction if hasattr(signed_txn, 'rawTransaction') else signed_txn.raw_transaction
            
            tx_hash = web3.eth.send_raw_transaction(raw_tx)
            logger.info(f"Approval transaction sent: {tx_hash.hex()}")
            
            return {'success': True, 'tx_hash': tx_hash.hex(), 'message': 'Token approval successful'}
            
        except Exception as e:
            logger.error(f"Error setting token approval: {e}")
            return {'success': False, 'error': f'Approval failed: {str(e)}'}
    
    def get_trading_fee_info(self, chain: str) -> Optional[Dict[str, Any]]:
        """Get trading fee information from the custom contract"""
        try:
            if chain not in self.trading_contracts:
                return None
            
            trading_contract = self.trading_contracts[chain]
            
            fee_percentage = trading_contract.functions.feePercentage().call()
            basis_points = trading_contract.functions.BASIS_POINTS().call()
            
            # Calculate actual fee percentage
            actual_fee = (fee_percentage / basis_points) * 100
            
            return {
                'fee_percentage': actual_fee,
                'basis_points': basis_points,
                'raw_fee': fee_percentage
            }
            
        except Exception as e:
            logger.error(f"Error getting trading fee info: {e}")
            return None
    
    def _send_transaction_with_retry(self, web3, signed_txn, max_retries=3):
        """Send transaction with retry logic for nonce issues"""
        for attempt in range(max_retries):
            try:
                # Handle both old and new web3 versions
                try:
                    raw_tx = signed_txn.raw_transaction
                except AttributeError:
                    try:
                        raw_tx = signed_txn.rawTransaction
                    except AttributeError:
                        raw_tx = signed_txn.rawTransaction if hasattr(signed_txn, 'rawTransaction') else signed_txn.raw_transaction
                
                tx_hash = web3.eth.send_raw_transaction(raw_tx)
                logger.info(f"Transaction sent successfully on attempt {attempt + 1}")
                return tx_hash
                
            except Exception as e:
                error_msg = str(e)
                if "nonce too low" in error_msg.lower():
                    logger.warning(f"Nonce issue on attempt {attempt + 1}: {error_msg}")
                    if attempt < max_retries - 1:
                        # Wait a bit and try again
                        import time
                        time.sleep(2)
                        continue
                    else:
                        raise Exception(f"Nonce issue after {max_retries} attempts: {error_msg}")
                else:
                    # Non-nonce error, don't retry
                    raise e
        
        raise Exception(f"Transaction failed after {max_retries} attempts")

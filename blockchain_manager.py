from web3 import Web3
from eth_account import Account
from typing import Optional, Dict, Any
from config import RPC_ENDPOINTS, SUPPORTED_CHAINS

class BlockchainManager:
    def __init__(self):
        self.web3_instances = {}
        self._initialize_web3_instances()
    
    def _initialize_web3_instances(self):
        """Initialize Web3 instances for all supported chains"""
        for chain in SUPPORTED_CHAINS:
            try:
                rpc_url = RPC_ENDPOINTS.get(chain)
                if rpc_url:
                    self.web3_instances[chain] = Web3(Web3.HTTPProvider(rpc_url))
                    
                    # Add POA middleware for BSC mainnet (Geth POA)
                    if chain == 'BSC':
                        try:
                            from web3.middleware import geth_poa_middleware
                            self.web3_instances[chain].middleware_onion.inject(geth_poa_middleware, layer=0)
                            print(f"✅ Added POA middleware for {chain}")
                        except ImportError:
                            try:
                                # Try alternative import path for newer web3 versions
                                from web3.middleware.geth import geth_poa_middleware
                                self.web3_instances[chain].middleware_onion.inject(geth_poa_middleware, layer=0)
                                print(f"✅ Added POA middleware for {chain} (alternative import)")
                            except ImportError:
                                print(f"⚠️ Could not import POA middleware for {chain} - transactions may fail")
                    
                    # Test connection
                    if not self.web3_instances[chain].is_connected():
                        print(f"Warning: Could not connect to {chain} RPC")
            except Exception as e:
                print(f"Error initializing {chain} Web3 instance: {e}")
    
    def create_wallet(self) -> Dict[str, str]:
        """Create a new wallet and return keypair"""
        try:
            account = Account.create()
            return {
                'public_key': account.address,
                'private_key': account.key.hex().replace('0x', '')
            }
        except Exception as e:
            print(f"Error creating wallet: {e}")
            raise
    
    def validate_private_key(self, private_key: str) -> Optional[str]:
        """Validate private key and return public address"""
        try:
            # Clean the private key
            clean_key = private_key.replace('0x', '').strip()
            
            # Validate format
            if len(clean_key) != 64:
                print(f"Private key length error: {len(clean_key)} (expected 64)")
                return None
            
            # Validate hex format
            try:
                int(clean_key, 16)
            except ValueError:
                print("Private key is not valid hexadecimal")
                return None
            
            # Try to create account
            account = Account.from_key('0x' + clean_key)
            return account.address
            
        except Exception as e:
            print(f"Error validating private key: {e}")
            return None
    
    def get_balance(self, chain: str, address: str) -> Optional[float]:
        """Get native token balance for a given address on specified chain"""
        try:
            if chain not in self.web3_instances:
                return None
            
            web3 = self.web3_instances[chain]
            if not web3.is_connected():
                return None
            
            balance_wei = web3.eth.get_balance(address)
            balance_eth = web3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            print(f"Error getting balance for {chain}: {e}")
            return None
    
    def estimate_gas(self, chain: str, from_address: str, to_address: str, 
                    value_wei: int) -> Optional[int]:
        """Estimate gas for a transfer"""
        try:
            if chain not in self.web3_instances:
                return None
            
            web3 = self.web3_instances[chain]
            if not web3.is_connected():
                return None
            
            transaction = {
                'from': from_address,
                'to': to_address,
                'value': value_wei
            }
            
            gas_estimate = web3.eth.estimate_gas(transaction)
            return gas_estimate
        except Exception as e:
            print(f"Error estimating gas for {chain}: {e}")
            return None
    
    def is_chain_supported(self, chain: str) -> bool:
        """Check if a chain is supported"""
        return chain in SUPPORTED_CHAINS
    
    def get_chain_info(self, chain: str) -> Dict[str, Any]:
        """Get information about a specific chain"""
        if chain not in self.web3_instances:
            return {}
        
        web3 = self.web3_instances[chain]
        try:
            return {
                'connected': web3.is_connected(),
                'latest_block': web3.eth.block_number if web3.is_connected() else None,
                'chain_id': web3.eth.chain_id if web3.is_connected() else None
            }
        except Exception as e:
            print(f"Error getting chain info for {chain}: {e}")
            return {}

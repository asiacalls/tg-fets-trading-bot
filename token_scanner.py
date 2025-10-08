import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import json

class TokenScanner:
    def __init__(self):
        self.base_url = "https://openapi.dexview.com/latest/dex/tokens"
        self.goplus_url = "https://api.gopluslabs.io/api/v1/token_security"
        self.supported_chains = ["BSC", "ETH"]
        
    async def scan_token(self, token_address: str, chain: str) -> Optional[Dict[str, Any]]:
        """
        Scan a token using the DexView API and GoPlus Labs security API
        
        Args:
            token_address: The token contract address
            chain: The blockchain (BSC or ETH)
            
        Returns:
            Token data dictionary or None if error
        """
        try:
            # Validate chain
            if chain.upper() not in self.supported_chains:
                return {"error": f"Unsupported chain. Supported chains: {', '.join(self.supported_chains)}"}
            
            # Make both API requests in parallel
            dexview_task = self._get_dexview_data(token_address)
            security_task = self.get_token_security_info(token_address, chain.upper())
            
            # Wait for both requests to complete
            dexview_data, security_data = await asyncio.gather(
                dexview_task, security_task, return_exceptions=True
            )
            
            # Process DexView data
            if isinstance(dexview_data, Exception):
                return {"error": f"DexView API error: {str(dexview_data)}"}
            
            token_info = self._process_response(dexview_data, chain.upper())
            
            # Add security information if available
            if not isinstance(security_data, Exception) and 'error' not in security_data:
                token_info.update(security_data)
            else:
                # Add placeholder tax info if security API fails
                token_info.update({
                    'buy_tax': 0,
                    'sell_tax': 0,
                    'transfer_tax': 0,
                    'holder_count': 0,
                    'holders': [],
                    'security_warning': 'Security data unavailable'
                })
            
            return token_info
                        
        except Exception as e:
            return {"error": f"Error scanning token: {str(e)}"}
    
    async def _get_dexview_data(self, token_address: str) -> Dict[str, Any]:
        """Get data from DexView API"""
        url = f"{self.base_url}/{token_address}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'accept': '*/*'}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"DexView API request failed with status {response.status}")
    
    async def get_token_security_info(self, token_address: str, chain: str) -> Optional[Dict[str, Any]]:
        """
        Get token security information including taxes and holders from GoPlus Labs API
        
        Args:
            token_address: The token contract address
            chain: The blockchain (BSC or ETH)
            
        Returns:
            Security data dictionary or None if error
        """
        try:
            # Map chain to GoPlus Labs chain ID
            chain_mapping = {
                'ETH': '1',  # Ethereum mainnet
                'BSC': '56',  # BSC mainnet
                'SEPOLIA': '11155111'  # Sepolia testnet
            }
            
            chain_id = chain_mapping.get(chain.upper())
            if not chain_id:
                return {"error": f"Unsupported chain for security check: {chain}"}
            
            # Make API request to GoPlus Labs
            url = f"{self.goplus_url}/{chain_id}"
            params = {'contract_addresses': token_address}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers={'accept': '*/*'}) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_security_response(data, token_address)
                    else:
                        return {"error": f"GoPlus API request failed with status {response.status}"}
                        
        except Exception as e:
            return {"error": f"Error fetching security info: {str(e)}"}
    
    def _process_security_response(self, data: Dict[str, Any], token_address: str) -> Dict[str, Any]:
        """
        Process the GoPlus Labs API response
        """
        try:
            if data.get('code') != 1:
                return {"error": f"GoPlus API error: {data.get('message', 'Unknown error')}"}
            
            result = data.get('result', {})
            token_data = result.get(token_address.lower())
            
            if not token_data:
                return {"error": "Token data not found in GoPlus response"}
            
            # Extract relevant information
            security_info = {
                'buy_tax': float(token_data.get('buy_tax', 0)) * 100,  # Convert to percentage
                'sell_tax': float(token_data.get('sell_tax', 0)) * 100,  # Convert to percentage
                'transfer_tax': float(token_data.get('transfer_tax', 0)) * 100,  # Convert to percentage
                'is_honeypot': token_data.get('is_honeypot', '0') == '1',
                'is_mintable': token_data.get('is_mintable', '0') == '1',
                'is_open_source': token_data.get('is_open_source', '0') == '1',
                'is_proxy': token_data.get('is_proxy', '0') == '1',
                'is_blacklisted': token_data.get('is_blacklisted', '0') == '1',
                'cannot_buy': token_data.get('cannot_buy', '0') == '1',
                'cannot_sell_all': token_data.get('cannot_sell_all', '0') == '1',
                'holder_count': int(token_data.get('holder_count', 0)),
                'holders': self._process_holders(token_data.get('holders', [])),
                'lp_holders': self._process_lp_holders(token_data.get('lp_holders', [])),
                'dex_info': self._process_dex_info(token_data.get('dex', []))
            }
            
            return security_info
            
        except Exception as e:
            return {"error": f"Error processing security response: {str(e)}"}
    
    def _process_holders(self, holders_data: List[Dict]) -> List[Dict]:
        """Process holders data from GoPlus API"""
        processed_holders = []
        
        for holder in holders_data[:10]:  # Limit to top 10 holders
            try:
                processed_holder = {
                    'address': holder.get('address', ''),
                    'tag': holder.get('tag', ''),
                    'balance': float(holder.get('balance', 0)),
                    'percent': float(holder.get('percent', 0)) * 100,  # Convert to percentage
                    'is_locked': holder.get('is_locked', 0) == 1,
                    'is_contract': holder.get('is_contract', 0) == 1
                }
                
                # Add locked detail if available
                if holder.get('locked_detail'):
                    processed_holder['locked_detail'] = holder['locked_detail']
                
                processed_holders.append(processed_holder)
                
            except (ValueError, TypeError) as e:
                continue  # Skip invalid holder data
        
        return processed_holders
    
    def _process_lp_holders(self, lp_holders_data: List[Dict]) -> List[Dict]:
        """Process LP holders data from GoPlus API"""
        processed_lp_holders = []
        
        for lp_holder in lp_holders_data:
            try:
                processed_lp_holder = {
                    'address': lp_holder.get('address', ''),
                    'tag': lp_holder.get('tag', ''),
                    'balance': float(lp_holder.get('balance', 0)),
                    'percent': float(lp_holder.get('percent', 0)) * 100,  # Convert to percentage
                    'is_locked': lp_holder.get('is_locked', 0) == 1,
                    'is_contract': lp_holder.get('is_contract', 0) == 1
                }
                
                # Add locked detail if available
                if lp_holder.get('locked_detail'):
                    processed_lp_holder['locked_detail'] = lp_holder['locked_detail']
                
                processed_lp_holders.append(processed_lp_holder)
                
            except (ValueError, TypeError) as e:
                continue  # Skip invalid LP holder data
        
        return processed_lp_holders
    
    def _process_dex_info(self, dex_data: List[Dict]) -> List[Dict]:
        """Process DEX information from GoPlus API"""
        processed_dex = []
        
        for dex in dex_data:
            try:
                processed_dex_item = {
                    'name': dex.get('name', ''),
                    'liquidity_type': dex.get('liquidity_type', ''),
                    'liquidity': float(dex.get('liquidity', 0)),
                    'pair': dex.get('pair', '')
                }
                processed_dex.append(processed_dex_item)
                
            except (ValueError, TypeError) as e:
                continue  # Skip invalid DEX data
        
        return processed_dex
    
    def _process_response(self, data: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """
        Process the API response and filter by chain
        """
        try:
            if "pairs" not in data:
                return {"error": "No pairs data found in response"}
            
            # Filter pairs by chain
            chain_lower = chain.lower()
            filtered_pairs = [pair for pair in data["pairs"] if pair.get("chainId", "").lower() == chain_lower]
            
            if not filtered_pairs:
                return {"error": f"No pairs found for chain {chain}"}
            
            # Get the first pair (usually the main one)
            pair = filtered_pairs[0]
            
            # Format the response
            result = {
                "chain": chain,
                "token_address": pair["baseToken"]["address"],
                "token_name": pair["baseToken"]["name"],
                "token_symbol": pair["baseToken"]["symbol"],
                "decimals": pair["baseToken"]["decimals"],
                "quote_token": pair["quoteToken"]["symbol"],
                "price_usd": pair["priceUsd"],
                "price_native": pair["priceNative"],
                "price_change_24h": pair["priceChange"]["h24"],
                "liquidity_usd": pair["liquidity"]["usd"],
                "volume_24h": pair["volume"]["h24"],
                "transactions_24h": {
                    "buys": pair["txns"]["h24"]["buys"],
                    "sells": pair["txns"]["h24"]["sells"]
                },
                "fdv": pair["fdv"],
                "dex_url": pair["url"]
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Error processing response: {str(e)}"}
    
    def format_scan_result(self, result: Dict[str, Any], compact: bool = False) -> str:
        """
        Format the scan result into a readable string
        
        Args:
            result: Token scan result
            compact: If True, creates a shorter format for Twitter
        """
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        try:
            # Normalize numeric fields (handle None/strings)
            def to_float(value, default=0.0):
                try:
                    if value is None:
                        return default
                    return float(value)
                except Exception:
                    return default

            price_change = to_float(result.get("price_change_24h"), 0.0)
            price_usd = to_float(result.get("price_usd"), 0.0)
            price_native = to_float(result.get("price_native"), 0.0)
            liquidity_usd = to_float(result.get("liquidity_usd"), 0.0)
            volume_24h = to_float(result.get("volume_24h"), 0.0)
            fdv = to_float(result.get("fdv"), 0.0)
            quote_token = result.get("quote_token") or "NATIVE"

            # Format price changes with colors - handle both percentage and decimal formats
            if price_change != 0:
                # Check if the value is already a percentage (e.g., 5.5 for 5.5%)
                # or a decimal (e.g., 0.055 for 5.5%)
                if abs(price_change) > 1:
                    # Already a percentage, format directly
                    if price_change > 0:
                        price_change_str = f"📈 +{price_change:.2f}%"
                    else:
                        price_change_str = f"📉 {price_change:.2f}%"
                else:
                    # It's a decimal, convert to percentage
                    if price_change > 0:
                        price_change_str = f"📈 +{price_change:.2%}"
                    else:
                        price_change_str = f"📉 {price_change:.2%}"
            else:
                price_change_str = "➡️ 0.00%"
            
            # Format prices properly (handle scientific notation)
            if price_usd < 0.000001:
                price_usd_str = f"${price_usd:.12f}"
            elif price_usd < 0.01:
                price_usd_str = f"${price_usd:.8f}"
            elif price_usd < 1:
                price_usd_str = f"${price_usd:.6f}"
            else:
                price_usd_str = f"${price_usd:.4f}"
            
            if price_native < 0.000000000001:
                price_native_str = f"{price_native:.18f}"
            elif price_native < 0.000001:
                price_native_str = f"{price_native:.12f}"
            elif price_native < 0.01:
                price_native_str = f"{price_native:.8f}"
            elif price_native < 1:
                price_native_str = f"{price_native:.6f}"
            else:
                price_native_str = f"{price_native:.4f}"
            
            # Get tax information
            buy_tax = result.get('buy_tax', 0)
            sell_tax = result.get('sell_tax', 0)
            transfer_tax = result.get('transfer_tax', 0)
            holder_count = result.get('holder_count', 0)
            holders = result.get('holders', [])
            
            # Format tax information
            tax_info = f"🅱️ {buy_tax:.1f}% 🅢 {sell_tax:.1f}% 🅣 {transfer_tax:.1f}%"
            
            if compact:
                text = f"🔍 Token Scanner - {result['chain']}\n\n"
                text += f"🪙 Token: {result['token_name']} ({result['token_symbol']})\n"
                text += f"💰 Price $: {price_usd_str}\n"
                text += f"🔄 Price Change 24h: {price_change_str}\n"
                text += f"💧 Liq: ${liquidity_usd:,.2f}\n"
                text += f"📊 Vol 24h: ${volume_24h:,.2f}\n"
                text += f"🛒 Txn 24h: {result['transactions_24h']['buys']} buys, {result['transactions_24h']['sells']} sells\n"
                text += f"🏦 FDV: ${fdv:,.2f}\n"
                text += f"⚖️ Taxes: {tax_info}\n"
                text += f"👥 Holders: {holder_count}"
            else:
                # Full format for Telegram
                text = f"🔍 Token Scanner - {result['chain']}\n\n"
                text += f"🪙 Token: {result['token_name']} ({result['token_symbol']})\n"
                text += f"📍 Address: `{result['token_address']}`\n"
                text += f"💰 Price USD: {price_usd_str}\n"
                text += f"🪙 Price {quote_token}: {price_native_str}\n"
                text += f"🔄 Price Change 24h: {price_change_str}\n"
                text += f"💧 Liquidity: ${liquidity_usd:,.2f}\n"
                text += f"📊 Volume 24h: ${volume_24h:,.2f}\n"
                text += f"🛒 Transactions 24h: {result['transactions_24h']['buys']} buys, {result['transactions_24h']['sells']} sells\n"
                text += f"🏦 FDV: ${fdv:,.2f}\n\n"
                text += f"⚖️ **Taxes:** {tax_info}\n"
                text += f"👥 **Holders:** {holder_count}\n\n"
                
                # Add security warnings if any
                if result.get('is_honeypot'):
                    text += f"⚠️ **HONEYPOT DETECTED** - Cannot sell tokens!\n"
                if result.get('cannot_buy'):
                    text += f"⚠️ **CANNOT BUY** - Trading restrictions detected!\n"
                if result.get('cannot_sell_all'):
                    text += f"⚠️ **CANNOT SELL ALL** - Partial sell restrictions!\n"
                if result.get('is_mintable'):
                    text += f"⚠️ **MINTABLE** - Token supply can be increased!\n"
            
            return text
            
        except Exception as e:
            return f"❌ Error formatting result: {str(e)}"
    
    def get_token_address(self, result: Dict[str, Any]) -> str:
        """
        Extract token address from scan result
        
        Args:
            result: Token scan result
            
        Returns:
            Token address string
        """
        if "error" in result:
            return ""
        return result.get("token_address", "")
    
    def create_scan_result_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of scan result for storage and quick access
        
        Args:
            result: Token scan result
            
        Returns:
            Summary dictionary with key information
        """
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            return {
                "token_address": result.get("token_address", ""),
                "token_name": result.get("token_name", ""),
                "token_symbol": result.get("token_symbol", ""),
                "chain": result.get("chain", ""),
                "price_usd": result.get("price_usd", 0),
                "price_change_24h": result.get("price_change_24h", 0),
                "liquidity_usd": result.get("liquidity_usd", 0),
                "volume_24h": result.get("volume_24h", 0),
                "fdv": result.get("fdv", 0),
                "scan_timestamp": result.get("scan_timestamp", "")
            }
        except Exception as e:
            return {"error": f"Error creating summary: {str(e)}"}

# Test function
async def test_scanner():
    scanner = TokenScanner()
    
    # Test with a sample token
    test_address = "0xf4A509313437dfC64E2EFeD14e2b607B1AED30c5"
    result = await scanner.scan_token(test_address, "BSC")
    
    print("Test Result:")
    print(json.dumps(result, indent=2))
    
    print("\nFormatted Result:")
    print(scanner.format_scan_result(result))
    
    print("\nCompact Result:")
    print(scanner.format_scan_result(result, compact=True))
    print(f"Length: {len(scanner.format_scan_result(result, compact=True))} chars")

if __name__ == "__main__":
    asyncio.run(test_scanner())

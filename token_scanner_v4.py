"""
Token Scanner v4.0 - Multi-Chain Token Balance Detection
Uses Moralis API to scan ALL tokens across ALL networks
"""

import sys
from pathlib import Path

# CRITICAL FIX: Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from typing import Dict, List
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TokenScanner:
    """Scan wallet for all tokens across multiple chains"""
    
    def __init__(self, web3_instance: Web3 = None):
        self.web3 = web3_instance
        
        # API keys - try .env first, then hardcoded
        self.moralis_api_key = os.getenv('MORALIS_API_KEY') or \
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjYyNjYxZWFjLWRiOTAtNDc1MC04OTBjLWUwYjliOTliYTAyOCIsIm9yZ0lkIjoiNDc3OTIxIiwidXNlcklkIjoiNDkxNjg2IiwidHlwZUlkIjoiYWYzMjMzYjMtY2YzNi00ZDBlLWJjZGYtZGY5YTk3MmZjOTdmIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NjE0NDk4NTEsImV4cCI6NDkxNzIwOTg1MX0.Karo35aYvHbcdI80h11M3dS_Gy-rJXoUyrKuMSCPoJE'
        
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY') or 'CG-57CKRSL1ZQZ81A9F7UC1bGMw'
        
        # Moralis API endpoints
        self.moralis_base_url = 'https://deep-index.moralis.io/api/v2.2'
        
        # Chain ID mapping for Moralis
        self.chain_map = {
            '0x1': 'eth',  # Ethereum
            '0x38': 'bsc',  # BSC
            '0x89': 'polygon',  # Polygon
            '0xa4b1': 'arbitrum',  # Arbitrum
            '0xa': 'optimism',  # Optimism
            '0xa86a': 'avalanche',  # Avalanche
            '0x171': 'pulsechain',  # PulseChain
            'pulsechain': 'pulsechain',
            'ethereum': 'eth',
            'bsc': 'bsc',
            'polygon': 'polygon',
            'arbitrum': 'arbitrum',
            'optimism': 'optimism',
            'avalanche': 'avalanche'
        }
        
        # Token cache
        self.token_cache = {}
        
    def scan_wallet(self, wallet_address: str, network: str = 'all') -> Dict:
        """Scan wallet for all tokens"""
        try:
            print(f"🔍 Scanning wallet: {wallet_address}")
            
            all_tokens = []
            total_value_usd = 0
            
            # Determine which chains to scan
            if network == 'all':
                chains_to_scan = list(self.chain_map.values())
            else:
                chains_to_scan = [self.chain_map.get(network, network)]
            
            # Scan each chain
            for chain in set(chains_to_scan):  # Remove duplicates
                try:
                    print(f"   📡 Scanning {chain}...")
                    
                    # Get native balance first
                    native_balance = self.get_native_balance(wallet_address, chain)
                    if native_balance:
                        all_tokens.append(native_balance)
                        total_value_usd += native_balance.get('value_usd', 0)
                    
                    # Get ERC20 tokens using Moralis
                    tokens = self.get_erc20_tokens_moralis(wallet_address, chain)
                    
                    if tokens:
                        all_tokens.extend(tokens)
                        for token in tokens:
                            total_value_usd += token.get('value_usd', 0)
                        
                        print(f"      ✓ Found {len(tokens)} tokens on {chain}")
                    
                except Exception as e:
                    print(f"      ⚠️ Error scanning {chain}: {e}")
                    continue
            
            print(f"   ✅ Scan complete! Found {len(all_tokens)} tokens total")
            print(f"   💰 Total value: ${total_value_usd:.2f}")
            
            return {
                'success': True,
                'wallet': wallet_address,
                'tokens': all_tokens,
                'total_tokens': len(all_tokens),
                'total_value_usd': total_value_usd
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tokens': []
            }
    
    def get_native_balance(self, wallet_address: str, chain: str) -> Dict:
        """Get native token balance (ETH, BNB, PLS, etc.)"""
        try:
            # Use Moralis for native balance
            url = f"{self.moralis_base_url}/{wallet_address}/balance"
            
            headers = {
                'X-API-Key': self.moralis_api_key
            }
            
            params = {
                'chain': chain
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                balance_wei = int(data.get('balance', 0))
                balance_native = balance_wei / 10**18
                
                # Get native token info
                native_info = self.get_native_token_info(chain)
                
                # Try to get price
                price_usd = self.get_token_price(native_info['symbol'])
                value_usd = balance_native * price_usd if price_usd else 0
                
                return {
                    'symbol': native_info['symbol'],
                    'name': native_info['name'],
                    'balance': balance_native,
                    'balance_formatted': f"{balance_native:.6f}",
                    'decimals': 18,
                    'chain': chain,
                    'is_native': True,
                    'price_usd': price_usd,
                    'value_usd': value_usd
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting native balance: {e}")
            return None
    
    def get_erc20_tokens_moralis(self, wallet_address: str, chain: str) -> List[Dict]:
        """Get ERC20 tokens using Moralis API"""
        try:
            url = f"{self.moralis_base_url}/{wallet_address}/erc20"
            
            headers = {
                'X-API-Key': self.moralis_api_key
            }
            
            params = {
                'chain': chain
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"Moralis API error: {response.status_code}")
                return []
            
            data = response.json()
            tokens = []
            
            for token_data in data:
                try:
                    decimals = int(token_data.get('decimals', 18))
                    balance_raw = int(token_data.get('balance', 0))
                    balance = balance_raw / (10 ** decimals)
                    
                    # Skip tokens with 0 balance
                    if balance == 0:
                        continue
                    
                    symbol = token_data.get('symbol', 'UNKNOWN')
                    
                    # Try to get price
                    price_usd = self.get_token_price(symbol)
                    value_usd = balance * price_usd if price_usd else 0
                    
                    token_info = {
                        'address': token_data.get('token_address'),
                        'symbol': symbol,
                        'name': token_data.get('name', symbol),
                        'balance': balance,
                        'balance_formatted': f"{balance:.6f}",
                        'decimals': decimals,
                        'chain': chain,
                        'is_native': False,
                        'price_usd': price_usd,
                        'value_usd': value_usd
                    }
                    
                    tokens.append(token_info)
                    
                except Exception as e:
                    print(f"Error processing token: {e}")
                    continue
            
            return tokens
            
        except Exception as e:
            print(f"Error getting ERC20 tokens: {e}")
            return []
    
    def get_token_price(self, symbol: str) -> float:
        """Get token price in USD"""
        try:
            # Check cache first
            if symbol in self.token_cache:
                cache_time, price = self.token_cache[symbol]
                # Cache for 60 seconds
                import time
                if time.time() - cache_time < 60:
                    return price
            
            # Try CoinGecko
            symbol_lower = symbol.lower()
            
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'eth': 'ethereum',
                'weth': 'ethereum',
                'bnb': 'binancecoin',
                'wbnb': 'binancecoin',
                'matic': 'matic-network',
                'wmatic': 'matic-network',
                'avax': 'avalanche-2',
                'wavax': 'avalanche-2',
                'pls': 'pulsechain',
                'wpls': 'pulsechain',
                'hex': 'hex',
                'plsx': 'pulsex',
                'usdt': 'tether',
                'usdc': 'usd-coin',
                'dai': 'dai',
                'btc': 'bitcoin',
                'wbtc': 'wrapped-bitcoin'
            }
            
            coin_id = symbol_map.get(symbol_lower, symbol_lower)
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'x_cg_demo_api_key': self.coingecko_api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = data.get(coin_id, {}).get('usd', 0)
                
                # Cache the price
                import time
                self.token_cache[symbol] = (time.time(), price)
                
                return price
            
            return 0
            
        except Exception as e:
            return 0
    
    def get_native_token_info(self, chain: str) -> Dict:
        """Get info about native token for a chain"""
        native_tokens = {
            'eth': {'symbol': 'ETH', 'name': 'Ethereum'},
            'bsc': {'symbol': 'BNB', 'name': 'BNB'},
            'polygon': {'symbol': 'MATIC', 'name': 'Polygon'},
            'arbitrum': {'symbol': 'ETH', 'name': 'Ethereum'},
            'optimism': {'symbol': 'ETH', 'name': 'Ethereum'},
            'avalanche': {'symbol': 'AVAX', 'name': 'Avalanche'},
            'pulsechain': {'symbol': 'PLS', 'name': 'Pulse'}
        }
        
        return native_tokens.get(chain, {'symbol': 'UNKNOWN', 'name': 'Unknown'})
    
    def get_token_info(self, token_address: str, chain: str) -> Dict:
        """Get detailed token information"""
        try:
            url = f"{self.moralis_base_url}/erc20/metadata"
            
            headers = {
                'X-API-Key': self.moralis_api_key
            }
            
            params = {
                'chain': chain,
                'addresses': [token_address]
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    token_data = data[0]
                    return {
                        'success': True,
                        'address': token_data.get('address'),
                        'name': token_data.get('name'),
                        'symbol': token_data.get('symbol'),
                        'decimals': int(token_data.get('decimals', 18)),
                        'chain': chain
                    }
            
            return {'success': False, 'error': 'Token not found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def refresh_balances(self, wallet_address: str, network: str = 'all') -> Dict:
        """Refresh and return updated balances"""
        return self.scan_wallet(wallet_address, network)

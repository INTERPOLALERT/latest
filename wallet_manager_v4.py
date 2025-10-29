"""
Wallet Manager v4.0 - Enhanced Wallet Management with Real Transactions
🆕 ENHANCED: Now scans and displays ALL ERC20 tokens in wallet!
Handles wallet connection, balance checking, and transaction signing
"""

import sys
from pathlib import Path

# CRITICAL FIX: Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from eth_account import Account
from typing import Dict, Optional, List
import json
import requests
from datetime import datetime, timedelta

try:
    from token_scanner_v4 import TokenScanner
    from abi_manager_v4 import abi_manager
except:
    TokenScanner = None
    abi_manager = None

class WalletManager:
    """Manage wallet connections and transactions"""
    
    def __init__(self):
        self.web3 = None
        self.account = None
        self.address = None
        self.private_key = None
        self.connected = False
        self.network = None
        
        # Token scanner for balance detection
        self.token_scanner = None
        
        # Cached balances
        self.balances = {}
        
        # Common token addresses for each network
        self.common_tokens = {}
    
    def connect_with_private_key(self, private_key: str, web3_instance: Web3, network: str = 'pulsechain') -> Dict:
        """Connect wallet using private key"""
        try:
            # Clean private key
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Validate length
            if len(private_key) != 64:
                return {
                    'success': False,
                    'error': 'Invalid private key length (must be 64 hex characters)'
                }
            
            # Create account
            self.account = Account.from_key(private_key)
            self.address = self.account.address
            self.private_key = '0x' + private_key
            self.web3 = web3_instance
            self.network = network
            self.connected = True
            
            # Initialize token scanner
            if TokenScanner:
                self.token_scanner = TokenScanner(web3_instance)
            
            # Load common tokens for this network
            self._load_common_tokens()
            
            # Get initial balance
            balance = self.get_native_balance()
            
            return {
                'success': True,
                'address': self.address,
                'balance': balance,
                'network': network
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection failed: {str(e)}'
            }
    
    def connect_with_seed_phrase(self, seed_phrase: str, web3_instance: Web3, network: str = 'pulsechain', index: int = 0) -> Dict:
        """Connect wallet using seed phrase"""
        try:
            # Enable mnemonic features
            Account.enable_unaudited_hdwallet_features()
            
            # Derive account from seed phrase
            self.account = Account.from_mnemonic(seed_phrase, account_path=f"m/44'/60'/0'/0/{index}")
            self.address = self.account.address
            self.private_key = self.account.key.hex()
            self.web3 = web3_instance
            self.network = network
            self.connected = True
            
            # Initialize token scanner
            if TokenScanner:
                self.token_scanner = TokenScanner(web3_instance)
            
            # Load common tokens for this network
            self._load_common_tokens()
            
            # Get initial balance
            balance = self.get_native_balance()
            
            return {
                'success': True,
                'address': self.address,
                'balance': balance,
                'network': network,
                'derivation_index': index
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection failed: {str(e)}'
            }
    
    def _load_common_tokens(self):
        """Load common token addresses for current network"""
        try:
            networks_file = Path(__file__).parent / 'networks_v7.json'
            if networks_file.exists():
                with open(networks_file, 'r') as f:
                    networks_data = json.load(f)
                    self.common_tokens = networks_data.get(self.network, {}).get('common_tokens', {})
        except Exception as e:
            print(f"⚠️ Could not load common tokens: {e}")
            # Fallback for PulseChain
            if self.network == 'pulsechain':
                self.common_tokens = {
                    'WPLS': '0xA1077a294dDE1B09bB078844df40758a5D0f9a27',
                    'HEX': '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39',
                    'PLSX': '0x95B303987A60C71504D99Aa1b13B4DA07b0790ab',
                    'INC': '0x2fa878Ab3F87CC1C9737Fc071108F904c0B0C95d',
                    'USDC': '0x15D38573d2feeb82e7ad5187aB8c1D52810B1f07'
                }
    
    def disconnect(self):
        """Disconnect wallet"""
        self.account = None
        self.address = None
        self.private_key = None
        self.connected = False
        self.web3 = None
        self.network = None
        self.balances = {}
        self.common_tokens = {}
    
    def get_native_balance(self) -> float:
        """Get native token balance (ETH, BNB, PLS, etc.)"""
        try:
            if not self.connected or not self.web3:
                return 0.0
            
            balance_wei = self.web3.eth.get_balance(self.address)
            balance_native = Web3.from_wei(balance_wei, 'ether')
            
            return float(balance_native)
            
        except Exception as e:
            print(f"Error getting native balance: {e}")
            return 0.0
    
    def get_token_balance(self, token_address: str) -> float:
        """Get ERC20 token balance"""
        try:
            if not self.connected or not self.web3 or not abi_manager:
                return 0.0
            
            # Get token contract
            token_abi = abi_manager.get_abi('erc20')
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=token_abi
            )
            
            # Get balance
            balance_raw = token_contract.functions.balanceOf(
                Web3.to_checksum_address(self.address)
            ).call()
            
            # Get decimals
            decimals = token_contract.functions.decimals().call()
            
            # Convert to human-readable
            balance = balance_raw / (10 ** decimals)
            
            return float(balance)
            
        except Exception as e:
            print(f"Error getting token balance for {token_address}: {e}")
            return 0.0
    
    def get_token_symbol(self, token_address: str) -> str:
        """Get token symbol"""
        try:
            if not self.connected or not self.web3 or not abi_manager:
                return "UNKNOWN"
            
            token_abi = abi_manager.get_abi('erc20')
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=token_abi
            )
            
            symbol = token_contract.functions.symbol().call()
            return symbol
            
        except Exception as e:
            return "UNKNOWN"
    
    def scan_all_tokens(self) -> List[Dict]:
        """
        🆕 ENHANCED: Scan wallet for ALL common tokens
        Returns list of tokens with balances > 0
        """
        try:
            if not self.connected:
                return []
            
            detected_tokens = []
            
            # Scan all common tokens for this network
            for symbol, address in self.common_tokens.items():
                if address == 'native':
                    continue  # Skip native token marker
                
                try:
                    balance = self.get_token_balance(address)
                    
                    if balance > 0:
                        price_usd = self.get_token_price_usd(symbol)
                        value_usd = balance * price_usd
                        
                        detected_tokens.append({
                            'symbol': symbol,
                            'address': address,
                            'balance': balance,
                            'price_usd': price_usd,
                            'value_usd': value_usd
                        })
                except Exception as e:
                    print(f"   ⚠️ Error scanning {symbol}: {e}")
                    continue
            
            return detected_tokens
            
        except Exception as e:
            print(f"Error scanning tokens: {e}")
            return []
    
    def sign_transaction(self, transaction: Dict) -> Dict:
        """Sign a transaction"""
        try:
            if not self.connected or not self.account:
                return {
                    'success': False,
                    'error': 'Wallet not connected'
                }
            
            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(
                transaction,
                self.private_key
            )
            
            return {
                'success': True,
                'signed_transaction': signed_tx,
                'raw_transaction': signed_tx.raw_transaction
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Signing failed: {str(e)}'
            }
    
    def send_transaction(self, signed_transaction) -> Dict:
        """Send a signed transaction"""
        try:
            if not self.connected or not self.web3:
                return {
                    'success': False,
                    'error': 'Wallet not connected'
                }
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_transaction.raw_transaction)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Transaction failed: {str(e)}'
            }
    
    def get_nonce(self) -> int:
        """Get current nonce for wallet"""
        try:
            if not self.connected or not self.web3:
                return 0
            
            return self.web3.eth.get_transaction_count(self.address)
            
        except Exception as e:
            print(f"Error getting nonce: {e}")
            return 0
    
    def get_token_price_usd(self, token_symbol: str) -> float:
        """Get token price in USD from CoinGecko"""
        try:
            # Map token symbols to CoinGecko IDs
            token_map = {
                'PLS': 'pulsechain',
                'PLSX': 'pulsex',
                'HEX': 'hex',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'USDC': 'usd-coin',
                'USDT': 'tether',
                'DAI': 'dai',
                'WETH': 'ethereum',
                'WBNB': 'binancecoin',
                'WPLS': 'pulsechain'
            }
            
            token_id = token_map.get(token_symbol.upper())
            if not token_id:
                return 0.0
            
            # Fetch from CoinGecko (free API, no key needed)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get(token_id, {}).get('usd', 0.0)
            else:
                # Fallback prices (rough estimates)
                fallback = {
                    'PLS': 0.00001,
                    'WPLS': 0.00001,
                    'PLSX': 0.00001,
                    'HEX': 0.005,
                    'ETH': 2000.0,
                    'BNB': 300.0,
                    'USDC': 1.0,
                    'USDT': 1.0,
                    'DAI': 1.0
                }
                return fallback.get(token_symbol.upper(), 0.0)
                
        except Exception as e:
            print(f"Error fetching price for {token_symbol}: {e}")
            return 0.0
    
    def get_wallet_info(self) -> Dict:
        """
        🆕 ENHANCED: Get complete wallet information with ALL tokens
        Now scans and displays ALL ERC20 tokens!
        """
        try:
            if not self.connected:
                return {
                    'connected': False
                }
            
            native_balance = self.get_native_balance()
            
            # Get native token price
            native_token_symbol = self._get_native_token_symbol()
            native_price = self.get_token_price_usd(native_token_symbol)
            native_value_usd = native_balance * native_price
            
            print(f"💰 Wallet USD Calculation: {native_balance:.2f} {native_token_symbol} × ${native_price:.6f} = ${native_value_usd:.2f}")
            
            # 🆕 SCAN ALL TOKENS!
            print(f"🔍 Scanning for ERC20 tokens...")
            erc20_tokens = self.scan_all_tokens()
            
            if erc20_tokens:
                print(f"✅ Found {len(erc20_tokens)} ERC20 tokens with balance")
                for token in erc20_tokens:
                    print(f"   {token['symbol']}: {token['balance']:.4f} = ${token['value_usd']:.2f}")
            else:
                print(f"📍 No ERC20 tokens detected with balance")
            
            # Calculate total value
            erc20_total_value = sum(t['value_usd'] for t in erc20_tokens)
            total_value_usd = native_value_usd + erc20_total_value
            
            return {
                'connected': True,
                'address': self.address,
                'network': self.network,
                'native_balance': native_balance,
                'native_symbol': native_token_symbol,
                'native_price_usd': native_price,
                'native_value_usd': native_value_usd,
                'nonce': self.get_nonce(),
                'tokens': erc20_tokens,  # 🆕 Now includes all tokens!
                'erc20_total_value_usd': erc20_total_value,
                'total_value_usd': total_value_usd
            }
            
        except Exception as e:
            print(f"❌ Error getting wallet info: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
    
    def _get_native_token_symbol(self) -> str:
        """Get native token symbol for current network"""
        network_tokens = {
            'pulsechain': 'PLS',
            'ethereum': 'ETH',
            'bsc': 'BNB',
            'polygon': 'MATIC',
            'avalanche': 'AVAX',
            'fantom': 'FTM',
            'arbitrum': 'ETH',
            'optimism': 'ETH'
        }
        return network_tokens.get(self.network, 'ETH')
    
    def export_wallet_info(self, include_private_key: bool = False) -> Dict:
        """Export wallet information (CAREFUL with private key!)"""
        info = self.get_wallet_info()
        
        if include_private_key and self.connected:
            info['private_key'] = self.private_key
            info['WARNING'] = 'NEVER SHARE THIS DATA!'
        
        return info
    
    def is_connected(self) -> bool:
        """Check if wallet is connected"""
        return self.connected and self.address is not None
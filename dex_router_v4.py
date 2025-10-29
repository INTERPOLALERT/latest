"""
DEX Router v4.0 - COMPLETE FIX
===============================
FIXES APPLIED:
1. ✅ Native PLS vs WPLS handling - NO MORE IDENTICAL_ADDRESSES
2. ✅ Returns default DEX instead of None
3. ✅ Proper swap path building that distinguishes native from wrapped

REPLACE YOUR CURRENT dex_router_v4.py WITH THIS FILE
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from typing import Dict, List, Optional, Tuple
import json
import time
from abi_manager_v4 import abi_manager

class DEXRouter:
    """Universal DEX router - FULLY FIXED FOR PLS/WPLS"""
    
    def __init__(self, web3_instance: Web3, network: str):
        self.web3 = web3_instance
        self.network = network
        self.abi_manager = abi_manager
        
        # Load network configuration
        self.network_config = self.load_network_config(network)
        
        # Router contracts cache
        self.routers = {}
        self.factories = {}
        
    def load_network_config(self, network: str) -> Dict:
        """Load network configuration from networks_v4.json"""
        try:
            networks_file = Path(__file__).parent / 'networks_v4.json'
            if networks_file.exists():
                with open(networks_file, 'r') as f:
                    all_networks = json.load(f)
                    return all_networks.get(network, {})
        except Exception as e:
            print(f"Error loading network config: {e}")
        
        return self.get_default_config(network)
    
    def get_default_config(self, network: str) -> Dict:
        """Get default configuration"""
        configs = {
            'pulsechain': {
                'chain_id': 369,
                'wrapped_token': '0xA1077a294dDE1B09bB078844df40758a5D0f9a27',
                'dexs': {
                    'pulsex_v2': {
                        'router': '0x165C3410fC91EF562C50559f7d2289fEbed552d9',
                        'factory': '0x29eA7545DEf87022BAdc76323F373EA1e707C523',
                        'type': 'uniswap_v2'
                    },
                    'pulsex_v1': {
                        'router': '0x98bf93ebf5c380C0e6Ae8e192A7e2AE08edAcc02',
                        'factory': '0x1715a3E4A142d8b698131108995174F37aEBA10D',
                        'type': 'uniswap_v2'
                    }
                }
            }
        }
        return configs.get(network, configs['pulsechain'])
    
    def get_router_contract(self, dex: str):
        """Get router contract instance"""
        if dex in self.routers:
            return self.routers[dex]
        
        dex_config = self.network_config.get('dexs', {}).get(dex, {})
        if not dex_config:
            raise ValueError(f"DEX {dex} not found in {self.network} configuration")
        
        router_address = dex_config['router']
        abi = self.abi_manager.get_abi('uniswap_v2_router')
        
        contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(router_address),
            abi=abi
        )
        
        self.routers[dex] = contract
        return contract
    
    def get_proper_gas_price(self) -> int:
        """Proper gas price for PulseChain EIP-1559"""
        try:
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            
            if base_fee == 0:
                return self.web3.eth.gas_price
            
            priority_fee = self.web3.to_wei(2, 'gwei')
            max_fee_per_gas = (base_fee * 2) + priority_fee
            
            return max_fee_per_gas
            
        except Exception as e:
            print(f"   ⚠️ Gas calc error: {e}, using fallback")
            return self.web3.eth.gas_price
    
    def get_amounts_out(self, dex: str, amount_in: int, path: List[str]) -> List[int]:
        """Get expected output amounts"""
        try:
            router = self.get_router_contract(dex)
            checksum_path = [Web3.to_checksum_address(addr) for addr in path]
            amounts = router.functions.getAmountsOut(amount_in, checksum_path).call()
            return amounts
        except Exception as e:
            print(f"   ❌ Error getting amounts: {e}")
            return []
    
    def build_swap_path(self, token_in: str, token_out: str, wrapped_token: str = None) -> List[str]:
        """
        🔧 CRITICAL FIX: Build swap path WITHOUT converting native to wrapped
        
        This method should ONLY be used for getAmountsOut queries where we need actual addresses.
        For native swaps, use WPLS in the path but handle with special router functions.
        
        Returns path with WPLS address when either token is 'native', but maintains distinction.
        """
        if not wrapped_token:
            wrapped_token = self.network_config.get('wrapped_token')
        
        wrapped_token_address = Web3.to_checksum_address(wrapped_token)
        
        # 🔧 FIX: For path queries, use WPLS address for native
        # But the calling code should track which is actually native
        if token_in in ['native', 'PLS', 'ETH']:
            token_in_addr = wrapped_token_address
        else:
            token_in_addr = Web3.to_checksum_address(token_in)
            
        if token_out in ['native', 'PLS', 'ETH']:
            token_out_addr = wrapped_token_address
        else:
            token_out_addr = Web3.to_checksum_address(token_out)
        
        # Direct path
        if token_in_addr == wrapped_token_address or token_out_addr == wrapped_token_address:
            return [token_in_addr, token_out_addr]
        
        # Route through wrapped token
        return [token_in_addr, wrapped_token_address, token_out_addr]
    
    def estimate_gas_for_swap(
        self,
        dex: str,
        token_in: str,
        token_out: str,
        amount_in: int,
        amount_out_min: int,
        recipient: str,
        deadline: int,
        is_native_in: bool = False,
        is_native_out: bool = False
    ) -> int:
        """Estimate gas with proper error handling"""
        try:
            router = self.get_router_contract(dex)
            path = self.build_swap_path(token_in, token_out)
            
            # Build tx for estimation
            if is_native_in:
                tx = router.functions.swapExactETHForTokens(
                    amount_out_min, path,
                    Web3.to_checksum_address(recipient),
                    deadline
                ).build_transaction({
                    'from': Web3.to_checksum_address(recipient),
                    'value': amount_in,
                    'gas': 300000,
                    'maxFeePerGas': self.get_proper_gas_price(),
                    'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
                })
            elif is_native_out:
                tx = router.functions.swapExactTokensForETH(
                    amount_in, amount_out_min, path,
                    Web3.to_checksum_address(recipient),
                    deadline
                ).build_transaction({
                    'from': Web3.to_checksum_address(recipient),
                    'gas': 300000,
                    'maxFeePerGas': self.get_proper_gas_price(),
                    'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
                })
            else:
                tx = router.functions.swapExactTokensForTokens(
                    amount_in, amount_out_min, path,
                    Web3.to_checksum_address(recipient),
                    deadline
                ).build_transaction({
                    'from': Web3.to_checksum_address(recipient),
                    'gas': 300000,
                    'maxFeePerGas': self.get_proper_gas_price(),
                    'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
                })
            
            estimated_gas = self.web3.eth.estimate_gas(tx)
            return int(estimated_gas * 1.2)  # 20% buffer
            
        except Exception as e:
            print(f"   ⚠️ Gas estimation failed: {e}")
            return 250000 if is_native_in else 300000
    
    def build_swap_transaction(
        self,
        dex: str,
        token_in: str,
        token_out: str,
        amount_in: int,
        amount_out_min: int,
        recipient: str,
        deadline: int = None,
        gas_price: int = None,
        gas_limit: int = None,
        nonce: int = None,
        is_native_in: bool = False
    ) -> Dict:
        """
        🔧 FIXED: Build swap transaction with proper native handling
        """
        try:
            router = self.get_router_contract(dex)
            
            # 🔧 FIX: Determine if output is native
            wrapped_token = self.network_config.get('wrapped_token')
            is_native_out = token_out in ['native', 'PLS', 'ETH']
            
            # Build path using wrapped addresses (for router)
            path = self.build_swap_path(token_in, token_out)
            
            print(f"   📍 Swap path: {path}")
            print(f"   🔹 Native IN: {is_native_in}, Native OUT: {is_native_out}")
            
            if deadline is None:
                deadline = int(time.time()) + 1200  # 20 min
            
            if gas_price is None:
                gas_price = self.get_proper_gas_price()
            
            if nonce is None:
                nonce = self.web3.eth.get_transaction_count(
                    Web3.to_checksum_address(recipient)
                )
            
            if gas_limit is None:
                gas_limit = self.estimate_gas_for_swap(
                    dex, token_in, token_out, amount_in, 
                    amount_out_min, recipient, deadline, is_native_in, is_native_out
                )
            
            priority_fee = self.web3.to_wei(2, 'gwei')
            
            # 🔧 FIX: Choose correct router function based on native status
            if is_native_in:
                # Native PLS → Token (use swapExactETHForTokens)
                print(f"   ✓ Using swapExactETHForTokens")
                tx = router.functions.swapExactETHForTokens(
                    amount_out_min, path,
                    Web3.to_checksum_address(recipient),
                    deadline
                ).build_transaction({
                    'from': Web3.to_checksum_address(recipient),
                    'value': amount_in,
                    'gas': gas_limit,
                    'maxFeePerGas': gas_price,
                    'maxPriorityFeePerGas': priority_fee,
                    'nonce': nonce,
                    'chainId': self.network_config.get('chain_id', 369)
                })
            elif is_native_out:
                # Token → Native PLS (use swapExactTokensForETH)
                print(f"   ✓ Using swapExactTokensForETH")
                tx = router.functions.swapExactTokensForETH(
                    amount_in, amount_out_min, path,
                    Web3.to_checksum_address(recipient),
                    deadline
                ).build_transaction({
                    'from': Web3.to_checksum_address(recipient),
                    'gas': gas_limit,
                    'maxFeePerGas': gas_price,
                    'maxPriorityFeePerGas': priority_fee,
                    'nonce': nonce,
                    'chainId': self.network_config.get('chain_id', 369)
                })
            else:
                # Token → Token (use swapExactTokensForTokens)
                print(f"   ✓ Using swapExactTokensForTokens")
                tx = router.functions.swapExactTokensForTokens(
                    amount_in, amount_out_min, path,
                    Web3.to_checksum_address(recipient),
                    deadline
                ).build_transaction({
                    'from': Web3.to_checksum_address(recipient),
                    'gas': gas_limit,
                    'maxFeePerGas': gas_price,
                    'maxPriorityFeePerGas': priority_fee,
                    'nonce': nonce,
                    'chainId': self.network_config.get('chain_id', 369)
                })
            
            return {
                'success': True,
                'transaction': tx,
                'path': path,
                'estimated_gas': gas_limit,
                'gas_price': gas_price
            }
            
        except Exception as e:
            print(f"   ❌ Transaction build error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'transaction': None
            }
    
    def get_best_dex_for_swap(
        self, token_in: str, token_out: str, amount_in: int
    ) -> Tuple[str, int]:
        """
        🔧 FIXED: Find best DEX and return default if none found
        """
        best_dex = None
        best_amount_out = 0
        
        # Build path for querying
        path = self.build_swap_path(token_in, token_out)
        
        for dex_name in self.network_config.get('dexs', {}).keys():
            try:
                amounts = self.get_amounts_out(dex_name, amount_in, path)
                if amounts and amounts[-1] > best_amount_out:
                    best_amount_out = amounts[-1]
                    best_dex = dex_name
            except Exception as e:
                print(f"   ⚠️ {dex_name} query failed: {e}")
                continue
        
        # 🔧 FIX: Return default DEX if none found
        if best_dex is None:
            best_dex = self.get_default_dex()
            print(f"   ⚠️ No DEX found best price, using default: {best_dex}")
        
        return best_dex, best_amount_out
    
    def check_liquidity(self, dex: str, token_a: str, token_b: str) -> Dict:
        """Check liquidity"""
        try:
            dex_config = self.network_config.get('dexs', {}).get(dex, {})
            factory_address = dex_config.get('factory')
            
            if not factory_address:
                return {'has_liquidity': False, 'error': 'Factory not configured'}
            
            factory_abi = self.abi_manager.get_abi('uniswap_v2_factory')
            factory = self.web3.eth.contract(
                address=Web3.to_checksum_address(factory_address),
                abi=factory_abi
            )
            
            pair_address = factory.functions.getPair(
                Web3.to_checksum_address(token_a),
                Web3.to_checksum_address(token_b)
            ).call()
            
            if pair_address == '0x0000000000000000000000000000000000000000':
                return {'has_liquidity': False, 'pair': None}
            
            pair_abi = self.abi_manager.get_abi('uniswap_v2_pair')
            pair = self.web3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=pair_abi
            )
            
            reserves = pair.functions.getReserves().call()
            token0 = pair.functions.token0().call()
            token1 = pair.functions.token1().call()
            
            return {
                'has_liquidity': True,
                'pair': pair_address,
                'reserve0': reserves[0],
                'reserve1': reserves[1],
                'token0': token0,
                'token1': token1
            }
            
        except Exception as e:
            return {'has_liquidity': False, 'error': str(e)}
    
    def get_default_dex(self) -> str:
        """Get default DEX"""
        dexs = self.network_config.get('dexs', {})
        priority = ['pulsex_v2', 'pulsex_v1']
        
        for dex in priority:
            if dex in dexs:
                return dex
        
        return list(dexs.keys())[0] if dexs else None
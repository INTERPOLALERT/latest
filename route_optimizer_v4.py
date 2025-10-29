"""
Route Optimizer v4.0 - Multi-Hop Path Finding
Finds optimal swap routes across multiple DEXs and tokens
"""

import sys
from pathlib import Path

# CRITICAL FIX: Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from typing import Dict, List, Tuple
import itertools

try:
    from dex_router_v4 import DEXRouter
except:
    pass

class RouteOptimizer:
    """Optimize swap routes for best prices"""
    
    def __init__(self, web3_instance: Web3, network: str):
        self.web3 = web3_instance
        self.network = network
        
        try:
            self.dex_router = DEXRouter(web3_instance, network)
        except:
            self.dex_router = None
        
        # Common intermediary tokens for routing
        self.intermediary_tokens = {
            'pulsechain': [
                '0xA1077a294dDE1B09bB078844df40758a5D0f9a27',  # WPLS
                '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39',  # HEX
                '0x95B303987A60C71504D99Aa1b13B4DA07b0790ab'   # PLSX
            ],
            'ethereum': [
                '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
                '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT
                '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'   # USDC
            ],
            'bsc': [
                '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',  # WBNB
                '0x55d398326f99059fF775485246999027B3197955',  # USDT
                '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d'   # USDC
            ]
        }
    
    def find_best_route(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        max_hops: int = 3
    ) -> Dict:
        """Find the best route considering multiple paths"""
        try:
            best_route = None
            best_amount_out = 0
            best_dex = None
            
            # Get available DEXs
            dexs = list(self.dex_router.network_config.get('dexs', {}).keys())
            
            # Try each DEX
            for dex in dexs:
                # Try direct route
                direct_route = self._try_route(dex, [token_in, token_out], amount_in)
                
                if direct_route['success'] and direct_route['amount_out'] > best_amount_out:
                    best_amount_out = direct_route['amount_out']
                    best_route = [token_in, token_out]
                    best_dex = dex
                
                # Try routes through intermediary tokens if max_hops > 1
                if max_hops > 1:
                    intermediaries = self.intermediary_tokens.get(self.network, [])
                    
                    for intermediary in intermediaries:
                        # Skip if intermediary is same as input/output
                        if intermediary in [token_in, token_out]:
                            continue
                        
                        # Try 2-hop route
                        two_hop_route = self._try_route(
                            dex,
                            [token_in, intermediary, token_out],
                            amount_in
                        )
                        
                        if two_hop_route['success'] and two_hop_route['amount_out'] > best_amount_out:
                            best_amount_out = two_hop_route['amount_out']
                            best_route = [token_in, intermediary, token_out]
                            best_dex = dex
                        
                        # Try 3-hop routes if max_hops > 2
                        if max_hops > 2:
                            for intermediary2 in intermediaries:
                                if intermediary2 in [token_in, token_out, intermediary]:
                                    continue
                                
                                three_hop_route = self._try_route(
                                    dex,
                                    [token_in, intermediary, intermediary2, token_out],
                                    amount_in
                                )
                                
                                if three_hop_route['success'] and three_hop_route['amount_out'] > best_amount_out:
                                    best_amount_out = three_hop_route['amount_out']
                                    best_route = [token_in, intermediary, intermediary2, token_out]
                                    best_dex = dex
            
            if best_route:
                return {
                    'success': True,
                    'route': best_route,
                    'dex': best_dex,
                    'amount_out': best_amount_out,
                    'hops': len(best_route) - 1
                }
            else:
                return {
                    'success': False,
                    'error': 'No viable route found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _try_route(self, dex: str, path: List[str], amount_in: int) -> Dict:
        """Try a specific route and return expected output"""
        try:
            amounts = self.dex_router.get_amounts_out(dex, amount_in, path)
            
            if amounts and len(amounts) > 0:
                return {
                    'success': True,
                    'amount_out': amounts[-1],
                    'path': path
                }
            else:
                return {
                    'success': False,
                    'amount_out': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'amount_out': 0,
                'error': str(e)
            }
    
    def compare_dex_prices(
        self,
        token_in: str,
        token_out: str,
        amount_in: int
    ) -> List[Dict]:
        """Compare prices across all DEXs"""
        try:
            results = []
            dexs = list(self.dex_router.network_config.get('dexs', {}).keys())
            
            for dex in dexs:
                try:
                    path = self.dex_router.build_swap_path(token_in, token_out)
                    amounts = self.dex_router.get_amounts_out(dex, amount_in, path)
                    
                    if amounts and len(amounts) > 0:
                        results.append({
                            'dex': dex,
                            'amount_out': amounts[-1],
                            'path': path,
                            'price_per_token': amounts[-1] / amount_in if amount_in > 0 else 0
                        })
                except:
                    continue
            
            # Sort by amount_out descending
            results.sort(key=lambda x: x['amount_out'], reverse=True)
            
            return results
            
        except Exception as e:
            return []
    
    def calculate_arbitrage_opportunity(
        self,
        token_a: str,
        token_b: str,
        amount: int
    ) -> Dict:
        """Check for arbitrage opportunities across DEXs"""
        try:
            # Get prices on all DEXs
            dex_prices = self.compare_dex_prices(token_a, token_b, amount)
            
            if len(dex_prices) < 2:
                return {
                    'success': False,
                    'error': 'Need at least 2 DEXs for arbitrage'
                }
            
            # Best buy DEX (highest output = best sell price)
            best_sell = dex_prices[0]
            
            # Best sell DEX (lowest output = best buy price)
            best_buy = dex_prices[-1]
            
            # Calculate potential profit
            profit = best_sell['amount_out'] - best_buy['amount_out']
            profit_percent = (profit / best_buy['amount_out']) * 100 if best_buy['amount_out'] > 0 else 0
            
            return {
                'success': True,
                'profitable': profit > 0,
                'profit': profit,
                'profit_percent': profit_percent,
                'buy_dex': best_buy['dex'],
                'sell_dex': best_sell['dex'],
                'buy_price': best_buy['price_per_token'],
                'sell_price': best_sell['price_per_token']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

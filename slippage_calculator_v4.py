"""
Slippage Calculator v5.0 - PulseChain Optimized
Dynamic slippage & liquidity-aware protection for PulseX v1/v2
"""

import sys
import math
import time
from pathlib import Path
from typing import Dict
from web3 import Web3

# Add src to path (important for modular bots)
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from dex_router_v4 import DEXRouter
except ImportError:
    DEXRouter = None


class SlippageCalculator:
    """Dynamic slippage engine for PulseChain (PulseX v1/v2)"""

    def __init__(self, web3_instance: Web3, network: str):
        self.web3 = web3_instance
        self.network = network.lower()
        self.dex_router = None

        if DEXRouter:
            try:
                self.dex_router = DEXRouter(web3_instance, network)
            except Exception as e:
                print(f"[!] DEXRouter init failed: {e}")

    # -------------------------------
    # 🔹 Main slippage protection
    # -------------------------------
    def calculate_slippage(
        self,
        dex: str,
        token_in: str,
        token_out: str,
        amount_in: int,
        base_slippage: float = 0.5
    ) -> Dict:
        """Calculate dynamic min output based on price impact and liquidity"""

        try:
            # --- Step 1: Build path ---
            path = self.dex_router.build_swap_path(token_in, token_out)
            if not path:
                return {'success': False, 'error': 'Invalid swap path'}

            # --- Step 2: Fetch expected output ---
            amounts = self.dex_router.get_amounts_out(dex, amount_in, path)
            if not amounts or len(amounts) < 2:
                return {'success': False, 'error': 'Failed to get quote'}

            expected_output = amounts[-1]

            # --- Step 3: Estimate liquidity + impact ---
            liquidity = self.dex_router.check_liquidity(dex, token_in, token_out)
            if not liquidity.get("has_liquidity"):
                return {'success': False, 'error': 'No liquidity for pair'}

            reserve_in = liquidity['reserve0']
            reserve_out = liquidity['reserve1']

            if reserve_in == 0 or reserve_out == 0:
                return {'success': False, 'error': 'Zero liquidity pool'}

            # --- Step 4: Dynamic slippage calculation ---
            # Impact grows faster as ratio (amount_in/reserve_in) increases
            impact_ratio = (amount_in / reserve_in)
            price_impact = impact_ratio * 100  # percent

            # Dynamic slippage scaling
            dynamic_slippage = base_slippage + (price_impact * 1.5)

            # Limit slippage range (PulseChain-specific tuning)
            dynamic_slippage = max(0.3, min(dynamic_slippage, 8.0))

            # --- Step 5: Calculate minimum output ---
            slippage_multiplier = 1 - (dynamic_slippage / 100)
            min_amount_out = math.floor(expected_output * slippage_multiplier)

            return {
                'success': True,
                'expected_output': expected_output,
                'min_amount_out': min_amount_out,
                'applied_slippage': round(dynamic_slippage, 3),
                'price_impact_percent': round(price_impact, 4),
                'path': path
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # -------------------------------
    # 🔹 Liquidity + price impact tool
    # -------------------------------
    def estimate_price_impact(self, dex: str, token_a: str, token_b: str, amount_in: int) -> Dict:
        """Estimate how much your trade will move the market price"""

        try:
            liquidity = self.dex_router.check_liquidity(dex, token_a, token_b)

            if not liquidity.get('has_liquidity'):
                return {'success': False, 'error': 'No liquidity found'}

            reserve0 = liquidity['reserve0']
            reserve1 = liquidity['reserve1']

            if reserve0 == 0 or reserve1 == 0:
                return {'success': False, 'error': 'Empty liquidity pool'}

            # Price impact as percentage of reserves
            price_impact = (amount_in / reserve0) * 100

            return {
                'success': True,
                'price_impact_percent': round(price_impact, 5),
                'reserve_in': reserve0,
                'reserve_out': reserve1
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

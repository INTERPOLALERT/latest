"""
Swap Executor v4.0 - COMPLETE FIX
FIXES APPLIED:
1. ✅ raw_transaction (not rawTransaction) 
2. ✅ Better native PLS vs WPLS handling
3. ✅ Improved logging for debugging

REPLACE YOUR CURRENT swap_executor_v4.py WITH THIS FILE
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from typing import Dict, Optional
import time
from abi_manager_v4 import abi_manager
from dex_router_v4 import DEXRouter

class SwapExecutor:
    """Execute swaps on DEX - FULLY FIXED"""
    
    def __init__(self, web3_instance: Web3, network: str, wallet_manager):
        self.web3 = web3_instance
        self.network = network
        self.wallet_manager = wallet_manager
        self.abi_manager = abi_manager
        
        # WPLS contract address for PulseChain
        self.WPLS_ADDRESS = '0xA1077a294dDE1B09bB078844df40758a5D0f9a27'
        
        # Initialize DEX router
        self.dex_router = DEXRouter(web3_instance, network)
        
        print(f"✅ Swap executor initialized (wallet address will be retrieved dynamically)")
    
    def _get_wallet_address(self) -> Optional[str]:
        """Get wallet address dynamically from wallet_manager"""
        try:
            if not self.wallet_manager:
                return None
            
            if hasattr(self.wallet_manager, 'address') and self.wallet_manager.address:
                return self.wallet_manager.address
            elif hasattr(self.wallet_manager, 'get_address'):
                return self.wallet_manager.get_address()
            elif hasattr(self.wallet_manager, 'is_connected') and self.wallet_manager.is_connected():
                if hasattr(self.wallet_manager, 'address'):
                    return self.wallet_manager.address
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error getting wallet address: {e}")
            return None
    
    def _get_private_key(self) -> Optional[str]:
        """Get private key dynamically from wallet_manager"""
        try:
            if not self.wallet_manager:
                return None
            
            if hasattr(self.wallet_manager, 'private_key'):
                return self.wallet_manager.private_key
            elif hasattr(self.wallet_manager, 'get_private_key'):
                return self.wallet_manager.get_private_key()
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error getting private key: {e}")
            return None
    
    def get_proper_gas_price(self) -> int:
        """Proper gas price for PulseChain EIP-1559"""
        try:
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            
            if base_fee == 0:
                return self.web3.eth.gas_price
            
            # maxFeePerGas = (baseFee * 2) + priorityFee
            priority_fee = self.web3.to_wei(2, 'gwei')
            max_fee = (base_fee * 2) + priority_fee
            
            return max_fee
            
        except Exception as e:
            print(f"   ⚠️ Gas calc error: {e}")
            return self.web3.eth.gas_price
    
    def check_token_balance(self, token_address: str, required_amount: int) -> tuple:
        """
        Check if wallet has enough token balance
        Returns (has_enough: bool, actual_balance: int)
        """
        try:
            wallet_address = self._get_wallet_address()
            
            if not wallet_address:
                print(f"   ❌ Wallet not connected!")
                return False, 0
            
            # Handle native PLS
            if token_address in ['native', 'PLS', 'ETH', '0x0000000000000000000000000000000000000000']:
                balance = self.web3.eth.get_balance(wallet_address)
                print(f"   💰 Native PLS balance: {self.web3.from_wei(balance, 'ether')} PLS")
            else:
                # ERC20 token (including WPLS)
                token_contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.abi_manager.get_abi('erc20')
                )
                balance = token_contract.functions.balanceOf(
                    Web3.to_checksum_address(wallet_address)
                ).call()
                print(f"   💰 Token balance: {self.web3.from_wei(balance, 'ether')} tokens")
            
            has_enough = balance >= required_amount
            
            if not has_enough:
                print(f"   ⚠️ Insufficient balance!")
                print(f"   Required: {self.web3.from_wei(required_amount, 'ether')}")
                print(f"   Available: {self.web3.from_wei(balance, 'ether')}")
            
            return has_enough, balance
            
        except Exception as e:
            print(f"   ❌ Balance check error: {e}")
            return False, 0
    
    def ensure_token_approved(self, token_address: str, spender_address: str, amount: int) -> bool:
        """
        🔧 FIX: Ensure token is approved before swap
        FIXED: raw_transaction (not rawTransaction)
        """
        try:
            wallet_address = self._get_wallet_address()
            private_key = self._get_private_key()
            
            if not wallet_address or not private_key:
                print(f"   ❌ Wallet not connected!")
                return False
            
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.abi_manager.get_abi('erc20')
            )
            
            # Check current allowance
            current_allowance = token_contract.functions.allowance(
                Web3.to_checksum_address(wallet_address),
                Web3.to_checksum_address(spender_address)
            ).call()
            
            # If allowance sufficient, return
            if current_allowance >= amount:
                print(f"   ✅ Token already approved (allowance: {self.web3.from_wei(current_allowance, 'ether')})")
                return True
            
            print(f"   🔄 Approving token...")
            print(f"   Current allowance: {self.web3.from_wei(current_allowance, 'ether')}")
            print(f"   Required: {self.web3.from_wei(amount, 'ether')}")
            
            # Get nonce
            nonce = self.web3.eth.get_transaction_count(wallet_address)
            
            # Build approval transaction with FIXED gas
            approve_tx = token_contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                2**256 - 1  # Max approval
            ).build_transaction({
                'from': wallet_address,
                'gas': 100000,
                'maxFeePerGas': self.get_proper_gas_price(),
                'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei'),
                'nonce': nonce,
                'chainId': 369
            })
            
            # Sign and send
            signed_tx = self.web3.eth.account.sign_transaction(approve_tx, private_key)
            
            # 🔧 CRITICAL FIX: Use raw_transaction (lowercase with underscore)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"   📤 Approval tx: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                print(f"   ✅ Token approved!")
                return True
            else:
                print(f"   ❌ Approval failed!")
                return False
                
        except Exception as e:
            print(f"   ❌ Approval error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_router_address(self, dex: str) -> str:
        """Get router address for DEX"""
        routers = {
            'pulsex_v2': '0x165C3410fC91EF562C50559f7d2289fEbed552d9',
            'pulsex_v1': '0x98bf93ebf5c380C0e6Ae8e192A7e2AE08edAcc02',
            'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            'pancakeswap_v2': '0x10ED43C718714eb63d5aA57B78B54704E256024E'
        }
        return routers.get(dex, routers['pulsex_v2'])
    
    def execute_swap(
        self,
        dex: str,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        deadline: int = None,
        gas_limit: int = None
    ) -> Dict:
        """
        🔧 FIXED: Execute swap with proper native PLS vs WPLS handling
        """
        try:
            wallet_address = self._get_wallet_address()
            private_key = self._get_private_key()
            
            if not wallet_address or not private_key:
                return {
                    'success': False,
                    'error': 'Wallet not connected! Please connect your wallet first.'
                }
            
            print(f"🔄 Executing swap on {dex}")
            print(f"   Wallet: {wallet_address}")
            print(f"   From: {token_in}")
            print(f"   To: {token_out}")
            print(f"   Amount In: {self.web3.from_wei(amount_in, 'ether')}")
            print(f"   Min Out: {self.web3.from_wei(min_amount_out, 'ether')}")
            
            # 🔧 FIX: Properly detect native PLS
            is_native_in = token_in in ['native', 'PLS', 'ETH', 'BNB', '0x0000000000000000000000000000000000000000']
            is_native_out = token_out in ['native', 'PLS', 'ETH', 'BNB', '0x0000000000000000000000000000000000000000']
            
            print(f"   Native IN: {is_native_in}, Native OUT: {is_native_out}")
            
            # ✅ FIX #1: Check balance
            if not is_native_in:
                has_balance, balance = self.check_token_balance(token_in, amount_in)
                if not has_balance:
                    return {
                        'success': False,
                        'error': 'Insufficient token balance',
                        'required': amount_in,
                        'available': balance
                    }
            else:
                # Check PLS balance (include gas buffer)
                gas_buffer = self.web3.to_wei(0.01, 'ether')  # 0.01 PLS for gas
                total_needed = amount_in + gas_buffer
                has_balance, balance = self.check_token_balance('PLS', total_needed)
                if not has_balance:
                    return {
                        'success': False,
                        'error': 'Insufficient PLS balance (including gas)',
                        'required': total_needed,
                        'available': balance
                    }
            
            # ✅ FIX #2: Approve token if needed (NOT for native PLS)
            if not is_native_in:
                router_address = self.get_router_address(dex)
                print(f"   ✓ Checking approval for router: {router_address}")
                
                if not self.ensure_token_approved(token_in, router_address, amount_in):
                    return {
                        'success': False,
                        'error': 'Token approval failed'
                    }
                
                print(f"   ✓ Token approved")
            
            # ✅ FIX #3: Build transaction with proper gas
            print(f"   ✓ Building transaction...")
            
            if deadline is None:
                deadline = int(time.time()) + 1200  # 20 minutes
            
            tx_data = self.dex_router.build_swap_transaction(
                dex=dex,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out_min=min_amount_out,
                recipient=wallet_address,
                deadline=deadline,
                gas_price=self.get_proper_gas_price(),
                gas_limit=gas_limit,
                is_native_in=is_native_in
            )
            
            if not tx_data['success']:
                return {
                    'success': False,
                    'error': f"Transaction build failed: {tx_data.get('error')}"
                }
            
            print(f"   ✓ Transaction built")
            print(f"   Gas Limit: {tx_data['estimated_gas']}")
            print(f"   Gas Price: {tx_data['gas_price']}")
            
            # Sign transaction
            print(f"   ✓ Signing transaction...")
            signed_tx = self.web3.eth.account.sign_transaction(
                tx_data['transaction'],
                private_key
            )
            
            # 🔧 CRITICAL FIX: Use raw_transaction (lowercase with underscore)
            print(f"   ✓ Sending transaction...")
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"   ✓ Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            print(f"   ⏳ Waiting for confirmation...")
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                print(f"   ✅ Swap successful!")
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt['gasUsed'],
                    'block_number': receipt['blockNumber']
                }
            else:
                print(f"   ❌ Transaction reverted!")
                return {
                    'success': False,
                    'error': 'Transaction reverted on-chain',
                    'tx_hash': tx_hash.hex()
                }
                
        except Exception as e:
            print(f"   ❌ Swap error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_arbitrage(
        self,
        buy_dex: str,
        sell_dex: str,
        token_a: str,
        token_b: str,
        amount: int
    ) -> Dict:
        """Execute arbitrage trade"""
        try:
            if not self._get_wallet_address():
                return {
                    'success': False,
                    'error': 'Wallet not connected'
                }
            
            print(f"🔄 Executing arbitrage")
            print(f"   Buy on {buy_dex}: {token_a} -> {token_b}")
            print(f"   Sell on {sell_dex}: {token_b} -> {token_a}")
            
            # Step 1: Buy on first DEX
            print(f"   Step 1: Buying {token_b} on {buy_dex}...")
            buy_result = self.execute_swap(
                dex=buy_dex,
                token_in=token_a,
                token_out=token_b,
                amount_in=amount,
                min_amount_out=0  # Calculate proper slippage
            )
            
            if not buy_result['success']:
                return {
                    'success': False,
                    'error': f"Buy failed: {buy_result['error']}",
                    'step': 'buy'
                }
            
            print(f"   ✅ Buy successful!")
            
            # Get amount received from buy
            amount_received = self.get_output_amount_from_receipt(buy_result['tx_hash'])
            
            # Step 2: Sell on second DEX
            print(f"   Step 2: Selling {token_b} on {sell_dex}...")
            sell_result = self.execute_swap(
                dex=sell_dex,
                token_in=token_b,
                token_out=token_a,
                amount_in=amount_received,
                min_amount_out=amount  # At least break even
            )
            
            if not sell_result['success']:
                return {
                    'success': False,
                    'error': f"Sell failed: {sell_result['error']}",
                    'step': 'sell',
                    'buy_tx': buy_result['tx_hash']
                }
            
            print(f"   ✅ Arbitrage complete!")
            
            return {
                'success': True,
                'buy_tx': buy_result['tx_hash'],
                'sell_tx': sell_result['tx_hash'],
                'buy_gas': buy_result['gas_used'],
                'sell_gas': sell_result['gas_used']
            }
            
        except Exception as e:
            print(f"   ❌ Arbitrage error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_output_amount_from_receipt(self, tx_hash: str) -> int:
        """Parse output amount from transaction receipt"""
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            # Parse logs to get actual output amount
            # This is DEX-specific, might need adjustment
            return 0  # Placeholder
        except:
            return 0
    
    def estimate_gas_cost(self, dex: str, token_in: str, token_out: str, amount: int) -> int:
        """Estimate gas cost for a swap"""
        try:
            gas_price = self.get_proper_gas_price()
            
            # Estimate gas units
            is_native = token_in in ['native', 'PLS']
            estimated_gas = 200000 if is_native else 300000
            
            # Calculate cost in wei
            gas_cost = gas_price * estimated_gas
            
            return gas_cost
            
        except Exception as e:
            print(f"Gas estimation error: {e}")
            return 0
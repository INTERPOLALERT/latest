"""
Transaction Manager v4.0 - Nonce & Gas Management
Handles EIP-1559 transactions with proper nonce tracking
"""

import sys
from pathlib import Path

# CRITICAL FIX: Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from typing import Dict
import time

class TransactionManager:
    """Manage transaction nonces and gas pricing"""
    
    def __init__(self, web3_instance: Web3, network: str):
        self.web3 = web3_instance
        self.network = network
        
        # Nonce tracking
        self.pending_nonces = {}
        
    def get_nonce(self, address: str, pending: bool = True) -> int:
        """Get next nonce for an address"""
        try:
            address = Web3.to_checksum_address(address)
            
            if pending:
                # Get pending nonce (includes unconfirmed transactions)
                nonce = self.web3.eth.get_transaction_count(address, 'pending')
            else:
                # Get latest confirmed nonce
                nonce = self.web3.eth.get_transaction_count(address, 'latest')
            
            return nonce
            
        except Exception as e:
            print(f"Error getting nonce: {e}")
            return 0
    
    def get_gas_price(self, strategy: str = 'medium') -> Dict:
        """Get gas price based on strategy"""
        try:
            # Try EIP-1559 first
            try:
                latest_block = self.web3.eth.get_block('latest')
                base_fee = latest_block.get('baseFeePerGas', 0)
                
                if base_fee > 0:
                    # EIP-1559 supported
                    priority_fee_strategies = {
                        'low': Web3.to_wei(1, 'gwei'),
                        'medium': Web3.to_wei(2, 'gwei'),
                        'high': Web3.to_wei(5, 'gwei'),
                        'fast': Web3.to_wei(10, 'gwei')
                    }
                    
                    priority_fee = priority_fee_strategies.get(strategy, priority_fee_strategies['medium'])
                    max_fee = base_fee * 2 + priority_fee
                    
                    return {
                        'type': 'eip1559',
                        'maxFeePerGas': max_fee,
                        'maxPriorityFeePerGas': priority_fee,
                        'baseFee': base_fee
                    }
            except:
                pass
            
            # Fallback to legacy gas price
            gas_price = self.web3.eth.gas_price
            
            multipliers = {
                'low': 0.9,
                'medium': 1.0,
                'high': 1.2,
                'fast': 1.5
            }
            
            multiplier = multipliers.get(strategy, 1.0)
            adjusted_price = int(gas_price * multiplier)
            
            return {
                'type': 'legacy',
                'gasPrice': adjusted_price
            }
            
        except Exception as e:
            print(f"Error getting gas price: {e}")
            return {
                'type': 'legacy',
                'gasPrice': Web3.to_wei(50, 'gwei')  # Default fallback
            }
    
    def estimate_gas(self, transaction: Dict) -> int:
        """Estimate gas for a transaction"""
        try:
            estimated = self.web3.eth.estimate_gas(transaction)
            # Add 20% buffer
            return int(estimated * 1.2)
        except Exception as e:
            print(f"Gas estimation failed: {e}")
            return 300000  # Default
    
    def wait_for_confirmation(
        self,
        tx_hash: str,
        timeout: int = 180,
        confirmations: int = 1
    ) -> Dict:
        """Wait for transaction confirmation"""
        try:
            print(f"⏳ Waiting for {confirmations} confirmation(s)...")
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout
            )
            
            # Wait for additional confirmations if needed
            if confirmations > 1:
                target_block = receipt['blockNumber'] + confirmations - 1
                while self.web3.eth.block_number < target_block:
                    time.sleep(2)
                    print(f"   Block: {self.web3.eth.block_number}/{target_block}")
            
            return {
                'success': receipt['status'] == 1,
                'receipt': receipt,
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

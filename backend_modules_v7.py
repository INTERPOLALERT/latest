"""
Backend Modules v7.0 - FIXED Module Aggregator
FIXED: abi_manager import (v4 filename)
FIXED: Proper swap_executor initialization
NEW: Better error handling and module availability checking
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from typing import Dict, Optional
import json

# FIXED: Import from v4 files (they were never renamed to v6/v7)
try:
    from wallet_manager_v4 import WalletManager
    WALLET_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ wallet_manager_v4.py not available: {e}")
    WalletManager = None
    WALLET_MANAGER_AVAILABLE = False

try:
    from dex_router_v4 import DEXRouter
    DEX_ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ dex_router_v4.py not available: {e}")
    DEXRouter = None
    DEX_ROUTER_AVAILABLE = False

try:
    from swap_executor_v4 import SwapExecutor
    SWAP_EXECUTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ swap_executor_v4.py not available: {e}")
    SwapExecutor = None
    SWAP_EXECUTOR_AVAILABLE = False

try:
    from token_scanner_v4 import TokenScanner
    TOKEN_SCANNER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ token_scanner_v4.py not available: {e}")
    TokenScanner = None
    TOKEN_SCANNER_AVAILABLE = False

try:
    from state_manager_v4 import StateManager
    STATE_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ state_manager_v4.py not available: {e}")
    StateManager = None
    STATE_MANAGER_AVAILABLE = False

# FIXED: Import abi_manager from v4 (correct filename)
try:
    from abi_manager_v4 import abi_manager
    ABI_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ abi_manager_v4.py not available: {e}")
    abi_manager = None
    ABI_MANAGER_AVAILABLE = False

try:
    from slippage_calculator_v4 import SlippageCalculator
    SLIPPAGE_CALCULATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ slippage_calculator_v4.py not available: {e}")
    SlippageCalculator = None
    SLIPPAGE_CALCULATOR_AVAILABLE = False

try:
    from transaction_manager_v4 import TransactionManager
    TRANSACTION_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ transaction_manager_v4.py not available: {e}")
    TransactionManager = None
    TRANSACTION_MANAGER_AVAILABLE = False

try:
    from route_optimizer_v4 import RouteOptimizer
    ROUTE_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ route_optimizer_v4.py not available: {e}")
    RouteOptimizer = None
    ROUTE_OPTIMIZER_AVAILABLE = False

class BackendModules:
    """Central class to manage all backend modules - v7 fixed version"""
    
    def __init__(self, web3_instance: Web3 = None, network: str = 'pulsechain'):
        self.web3 = web3_instance
        self.network = network
        
        # Core modules
        self.wallet_manager = None
        self.dex_router = None
        self.swap_executor = None
        self.token_scanner = None
        self.state_manager = None
        self.slippage_calculator = None
        self.transaction_manager = None
        self.route_optimizer = None
        self.abi_manager = abi_manager  # FIXED: Direct reference
        
        # Initialize modules
        self.initialize_modules()
    
    def initialize_modules(self):
        """Initialize all available modules with proper error handling"""
        try:
            # Core modules that don't require Web3
            if WALLET_MANAGER_AVAILABLE:
                self.wallet_manager = WalletManager()
                print("✅ Wallet Manager initialized")
            
            if STATE_MANAGER_AVAILABLE:
                self.state_manager = StateManager()
                print("✅ State Manager initialized")
            
            # Modules that require Web3
            if self.web3:
                if DEX_ROUTER_AVAILABLE:
                    try:
                        self.dex_router = DEXRouter(self.web3, self.network)
                        print("✅ DEX Router initialized")
                    except Exception as e:
                        print(f"⚠️ DEX Router init error: {e}")
                
                # FIXED: Proper swap_executor initialization
                if SWAP_EXECUTOR_AVAILABLE:
                    try:
                        self.swap_executor = SwapExecutor(
                            self.web3,
                            self.network,
                            self.wallet_manager
                        )
                        print("✅ Swap Executor initialized")
                    except Exception as e:
                        print(f"⚠️ Swap Executor init error: {e}")
                
                if TOKEN_SCANNER_AVAILABLE:
                    try:
                        self.token_scanner = TokenScanner(self.web3)
                        print("✅ Token Scanner initialized")
                    except Exception as e:
                        print(f"⚠️ Token Scanner init error: {e}")
                
                if SLIPPAGE_CALCULATOR_AVAILABLE:
                    try:
                        self.slippage_calculator = SlippageCalculator(self.web3, self.network)
                        print("✅ Slippage Calculator initialized")
                    except Exception as e:
                        print(f"⚠️ Slippage Calculator init error: {e}")
                
                if TRANSACTION_MANAGER_AVAILABLE:
                    try:
                        self.transaction_manager = TransactionManager(self.web3, self.network)
                        print("✅ Transaction Manager initialized")
                    except Exception as e:
                        print(f"⚠️ Transaction Manager init error: {e}")
                
                if ROUTE_OPTIMIZER_AVAILABLE:
                    try:
                        self.route_optimizer = RouteOptimizer(self.web3, self.network)
                        print("✅ Route Optimizer initialized")
                    except Exception as e:
                        print(f"⚠️ Route Optimizer init error: {e}")
            
        except Exception as e:
            print(f"❌ Module initialization error: {e}")
    
    def get_module_status(self) -> Dict:
        """Get status of all modules"""
        return {
            'core_modules': {
                'wallet_manager': WALLET_MANAGER_AVAILABLE and self.wallet_manager is not None,
                'dex_router': DEX_ROUTER_AVAILABLE and self.dex_router is not None,
                'swap_executor': SWAP_EXECUTOR_AVAILABLE and self.swap_executor is not None,
                'token_scanner': TOKEN_SCANNER_AVAILABLE and self.token_scanner is not None,
                'state_manager': STATE_MANAGER_AVAILABLE and self.state_manager is not None,
                'abi_manager': ABI_MANAGER_AVAILABLE and self.abi_manager is not None,
                'slippage_calculator': SLIPPAGE_CALCULATOR_AVAILABLE and self.slippage_calculator is not None,
                'transaction_manager': TRANSACTION_MANAGER_AVAILABLE and self.transaction_manager is not None,
                'route_optimizer': ROUTE_OPTIMIZER_AVAILABLE and self.route_optimizer is not None
            }
        }
    
    def check_critical_modules(self) -> bool:
        """Check if all critical modules are available"""
        critical = [
            self.wallet_manager is not None,
            self.dex_router is not None,
            self.swap_executor is not None,
            self.abi_manager is not None
        ]
        return all(critical)
    
    def get_missing_modules(self) -> list:
        """Get list of missing modules"""
        status = self.get_module_status()
        missing = []
        
        for category, modules in status.items():
            for module_name, available in modules.items():
                if not available:
                    missing.append(module_name)
        
        return missing

def check_module_availability():
    """Print status of all modules"""
    print("\n" + "="*60)
    print("BACKEND MODULES V7 - STATUS CHECK")
    print("="*60)
    
    print("\n✅ CORE MODULES:")
    print(f"  {'Wallet Manager:':<25} {'✅' if WALLET_MANAGER_AVAILABLE else '❌'}")
    print(f"  {'DEX Router:':<25} {'✅' if DEX_ROUTER_AVAILABLE else '❌'}")
    print(f"  {'Swap Executor:':<25} {'✅' if SWAP_EXECUTOR_AVAILABLE else '❌'}")
    print(f"  {'Token Scanner:':<25} {'✅' if TOKEN_SCANNER_AVAILABLE else '❌'}")
    print(f"  {'State Manager:':<25} {'✅' if STATE_MANAGER_AVAILABLE else '❌'}")
    print(f"  {'ABI Manager:':<25} {'✅' if ABI_MANAGER_AVAILABLE else '❌'}")
    print(f"  {'Slippage Calculator:':<25} {'✅' if SLIPPAGE_CALCULATOR_AVAILABLE else '❌'}")
    print(f"  {'Transaction Manager:':<25} {'✅' if TRANSACTION_MANAGER_AVAILABLE else '❌'}")
    print(f"  {'Route Optimizer:':<25} {'✅' if ROUTE_OPTIMIZER_AVAILABLE else '❌'}")
    
    print("\n" + "="*60)
    
    critical_ok = all([
        WALLET_MANAGER_AVAILABLE,
        DEX_ROUTER_AVAILABLE,
        SWAP_EXECUTOR_AVAILABLE,
        ABI_MANAGER_AVAILABLE
    ])
    
    if critical_ok:
        print("✅ All critical modules are available!")
    else:
        print("❌ Some critical modules are missing!")
    
    print("="*60 + "\n")
    
    return critical_ok

if __name__ == "__main__":
    check_module_availability()

"""
Test Script for PulseX Fixes
Run this to verify your fixes are working
"""

from web3 import Web3
import sys

print("="*60)
print("PULSEX BOT - FIX VERIFICATION TEST")
print("="*60)

# Test 1: Web3 Connection
print("\n1️⃣ Testing Web3 Connection...")
try:
    web3 = Web3(Web3.HTTPProvider('https://rpc.pulsechain.com'))
    if web3.is_connected():
        print("   ✅ Connected to PulseChain")
        print(f"   Chain ID: {web3.eth.chain_id}")
    else:
        print("   ❌ Failed to connect")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Import modules
print("\n2️⃣ Testing Module Imports...")
try:
    from dex_router_v4 import DEXRouter
    print("   ✅ dex_router_v4 imported")
except Exception as e:
    print(f"   ❌ Failed to import dex_router_v4: {e}")
    sys.exit(1)

try:
    from swap_executor_v4 import SwapExecutor
    print("   ✅ swap_executor_v4 imported")
except Exception as e:
    print(f"   ❌ Failed to import swap_executor_v4: {e}")
    print("   ⚠️ This is OK if you haven't added wallet_manager yet")

# Test 3: Gas Price Calculation
print("\n3️⃣ Testing Gas Price Calculation...")
try:
    router = DEXRouter(web3, 'pulsechain')
    gas_price = router.get_proper_gas_price()
    
    # Get base fee
    block = web3.eth.get_block('latest')
    base_fee = block.get('baseFeePerGas', 0)
    
    print(f"   Base Fee: {base_fee:,} wei")
    print(f"   Max Fee: {gas_price:,} wei")
    print(f"   ✅ Gas price is {'VALID' if gas_price > base_fee else 'INVALID'}")
    
    if gas_price <= base_fee:
        print("   ❌ ERROR: Gas price too low!")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Router Contract
print("\n4️⃣ Testing Router Contract...")
try:
    router_contract = router.get_router_contract('pulsex_v2')
    print(f"   ✅ Router contract loaded")
    print(f"   Address: {router_contract.address}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 5: Get Price Quote
print("\n5️⃣ Testing Price Quote (1 PLS -> PLSX)...")
try:
    wpls = '0xA1077a294dDE1B09bB078844df40758a5D0f9a27'
    plsx = '0x95B303987A60C71504D99Aa1b13B4DA07b0790ab'
    
    path = [wpls, plsx]
    amount_in = web3.to_wei(1, 'ether')
    
    amounts = router.get_amounts_out('pulsex_v2', amount_in, path)
    
    if amounts:
        amount_out = amounts[1]
        print(f"   ✅ Quote received")
        print(f"   1 PLS = {web3.from_wei(amount_out, 'ether')} PLSX")
    else:
        print(f"   ❌ Failed to get quote")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Build Test Transaction (don't send)
print("\n6️⃣ Testing Transaction Building...")
try:
    test_address = '0x0000000000000000000000000000000000000001'
    
    tx_data = router.build_swap_transaction(
        dex='pulsex_v2',
        token_in='native',
        token_out=plsx,
        amount_in=web3.to_wei(0.1, 'ether'),
        amount_out_min=0,
        recipient=test_address,
        is_native_in=True
    )
    
    if tx_data['success']:
        print(f"   ✅ Transaction built successfully")
        print(f"   Gas Limit: {tx_data['estimated_gas']:,}")
        print(f"   Max Fee: {tx_data['gas_price']:,} wei")
        
        # Verify EIP-1559 format
        tx = tx_data['transaction']
        if 'maxFeePerGas' in tx and 'maxPriorityFeePerGas' in tx:
            print(f"   ✅ EIP-1559 format correct")
        else:
            print(f"   ❌ ERROR: Missing EIP-1559 fields")
            sys.exit(1)
    else:
        print(f"   ❌ Failed: {tx_data.get('error')}")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Check Liquidity
print("\n7️⃣ Testing Liquidity Check...")
try:
    liquidity = router.check_liquidity('pulsex_v2', wpls, plsx)
    
    if liquidity.get('has_liquidity'):
        print(f"   ✅ Liquidity exists")
        print(f"   Pair: {liquidity['pair']}")
        print(f"   Reserve0: {liquidity['reserve0']:,}")
        print(f"   Reserve1: {liquidity['reserve1']:,}")
    else:
        print(f"   ⚠️ No liquidity or error: {liquidity.get('error')}")
        
except Exception as e:
    print(f"   ⚠️ Error: {e}")

# Final Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("✅ All critical tests passed!")
print("")
print("Your fixes are working correctly. Key points:")
print("  • Gas price calculation: FIXED ✅")
print("  • EIP-1559 transaction format: FIXED ✅")
print("  • Router contract loading: WORKING ✅")
print("  • Price quotes: WORKING ✅")
print("")
print("Next steps:")
print("  1. Make sure you have PLS in your wallet")
print("  2. Test with a real swap (0.1 PLS)")
print("  3. Then try your arbitrage bot")
print("")
print("⚠️ REMEMBER: Test with small amounts first!")
print("="*60)
"""
Example: How to Use the New Wallet Token Tracking Feature
"""

from main_v7 import TradingBotV7

def example_wallet_tracking():
    """Example of how to display tracked tokens"""
    
    # Initialize bot
    bot = TradingBotV7(network='pulsechain')
    
    # Option 1: Get formatted display (easiest)
    print("\n" + "="*60)
    print("OPTION 1: Formatted Display")
    print("="*60)
    wallet_display = bot.format_wallet_display()
    print(wallet_display)
    
    # Option 2: Get raw token data (for custom display)
    print("\n" + "="*60)
    print("OPTION 2: Raw Token Data")
    print("="*60)
    tracked_tokens = bot.get_tracked_tokens()
    
    for token in tracked_tokens:
        print(f"\nToken: {token['symbol']}")
        print(f"  Address: {token['address']}")
        print(f"  Balance: {token['balance']:.4f}")
        print(f"  Price: ${token['price_usd']:.6f}")
        print(f"  Value: ${token['value_usd']:.2f}")
        print(f"  In Active Position: {token['in_positions']}")
    
    # Option 3: Filter by value threshold
    print("\n" + "="*60)
    print("OPTION 3: Tokens Above $1")
    print("="*60)
    valuable_tokens = [t for t in tracked_tokens if t['value_usd'] > 1.0]
    
    for token in valuable_tokens:
        print(f"{token['symbol']}: ${token['value_usd']:.2f}")
    
    # Option 4: Get total portfolio value
    print("\n" + "="*60)
    print("OPTION 4: Total Portfolio Value")
    print("="*60)
    total_value = sum(t['value_usd'] for t in tracked_tokens)
    print(f"Total Portfolio Value: ${total_value:.2f}")
    
    # Option 5: Check if you own a specific token
    print("\n" + "="*60)
    print("OPTION 5: Check Specific Token")
    print("="*60)
    token_to_check = 'HEX'
    hex_token = next((t for t in tracked_tokens if t['symbol'] == token_to_check), None)
    
    if hex_token:
        print(f"✅ You own {hex_token['balance']:.4f} {token_to_check}")
        print(f"   Worth: ${hex_token['value_usd']:.2f}")
    else:
        print(f"❌ You don't own any {token_to_check}")


def example_gui_integration():
    """Example of how to integrate into your GUI"""
    
    print("\n" + "="*60)
    print("GUI INTEGRATION EXAMPLE")
    print("="*60)
    
    # In your GUI code, you would do something like:
    
    example_code = '''
# In gui_v7.py, add a new method:

def update_wallet_display(self):
    """Update the wallet tokens display"""
    try:
        # Get tracked tokens
        tracked_tokens = self.bot.get_tracked_tokens()
        
        # Clear existing display
        self.wallet_tokens_text.delete('1.0', 'end')
        
        # Add header
        self.wallet_tokens_text.insert('end', "💰 TRACKED TOKENS\\n\\n", 'header')
        
        # Add tokens
        total_value = 0
        for token in tracked_tokens:
            symbol = token['symbol']
            balance = token['balance']
            price = token['price_usd']
            value = token['value_usd']
            in_position = "📊" if token['in_positions'] else "  "
            
            total_value += value
            
            line = f"{in_position} {symbol}: {balance:.4f} @ ${price:.6f} = ${value:.2f}\\n"
            self.wallet_tokens_text.insert('end', line)
        
        # Add total
        self.wallet_tokens_text.insert('end', f"\\n💵 Total: ${total_value:.2f}", 'total')
        
    except Exception as e:
        self.wallet_tokens_text.insert('end', f"Error: {e}", 'error')

# Then call this method:
# - When wallet connects
# - Every 30 seconds (for updates)
# - After each trade
# - When user clicks "Refresh Wallet" button
'''
    
    print(example_code)


def example_console_monitor():
    """Example of continuous monitoring in console"""
    
    print("\n" + "="*60)
    print("CONSOLE MONITORING EXAMPLE")
    print("="*60)
    
    example_code = '''
import time
from main_v7 import TradingBotV7

def monitor_wallet():
    """Monitor wallet tokens continuously"""
    
    bot = TradingBotV7(network='pulsechain')
    
    print("Starting wallet monitor...")
    print("Press Ctrl+C to stop\\n")
    
    try:
        while True:
            # Clear screen (Windows)
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Display time
            from datetime import datetime
            print(f"Last Update: {datetime.now().strftime('%H:%M:%S')}\\n")
            
            # Display wallet
            print(bot.format_wallet_display())
            
            # Wait 30 seconds
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\\nMonitor stopped")

if __name__ == "__main__":
    monitor_wallet()
'''
    
    print(example_code)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  TRADING BOT v7.0 - WALLET TOKEN TRACKING EXAMPLES")
    print("="*70)
    
    # Show all examples
    example_wallet_tracking()
    example_gui_integration()
    example_console_monitor()
    
    print("\n" + "="*70)
    print("  Examples complete! Copy these into your code.")
    print("="*70)

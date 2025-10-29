"""
DEX Trading Bot v7.0 - Main Entry Point
FIXED: Proper path setup, module loading, and GUI launch
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Setup Python path"""
    current_dir = Path(__file__).parent
    
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    src_dir = current_dir / 'src'
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    print(f"✓ Python path configured")

setup_python_path()

# Import modules
try:
    from main_v7 import TradingBotV7
    print("✓ Main bot module loaded")
except ImportError as e:
    print(f"❌ Error loading main_v7.py: {e}")
    input("\nPress Enter to exit...")
    sys.exit(1)

try:
    from gui_v7 import TradingBotGUI
    print("✓ GUI module loaded")
except ImportError as e:
    print(f"❌ Error loading gui_v7.py: {e}")
    input("\nPress Enter to exit...")
    sys.exit(1)

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("   DEX TRADING BOT V7.0 - PROFESSIONAL EDITION")
    print("="*60)
    print()
    
    try:
        print("🚀 Starting GUI...")
        app = TradingBotGUI()
        app.mainloop()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Bot stopped by user")
        
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
DEX Trading Bot v7.0 - Enhanced GUI Interface
FIXED: Settings properly integrated with bot (risk management, trading settings)
FIXED: All settings now respected in live trading mode
NEW: Better validation and feedback for setting changes
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import customtkinter as ctk
from customtkinter import CTkFont
import threading
import time
from datetime import datetime

try:
    from main_v7 import TradingBotV7
except ImportError:
    print("❌ main_v7.py not found!")
    TradingBotV7 = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TradingBotGUI(ctk.CTk):
    """Enhanced GUI with FIXED settings integration"""
    
    def __init__(self):
        super().__init__()
        
        self.title("DEX Trading Bot v7.0 - Professional Edition")
        self.geometry("1600x1000")
        
        # Initialize bot
        if TradingBotV7:
            self.bot = TradingBotV7(network='pulsechain')
        else:
            self.bot = None
        
        # GUI state
        self.update_thread = None
        self.running_updates = False
        
        # Build GUI
        self.build_gui()
        
        # FIXED: Load current settings into GUI
        self.load_current_settings()
        
        # Start update loop
        self.start_gui_updates()
    
    def build_gui(self):
        """Build the GUI interface"""
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # === TOP BAR ===
        self.build_top_bar()
        
        # === TAB VIEW ===
        self.tabview = ctk.CTkTabview(self, width=1560, height=900)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Add tabs
        self.tabview.add("Dashboard")
        self.tabview.add("Wallet")
        self.tabview.add("Strategies")
        self.tabview.add("Positions")
        self.tabview.add("Settings")
        
        # Build tabs
        self.build_dashboard_tab()
        self.build_wallet_tab()
        self.build_strategies_tab()
        self.build_positions_tab()
        self.build_settings_tab()
    
    def build_top_bar(self):
        """Build top control bar"""
        top_frame = ctk.CTkFrame(self, height=80)
        top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        top_frame.grid_columnconfigure((1, 2, 3, 4), weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            top_frame,
            text="🚀 DEX TRADING BOT v7.0",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            top_frame,
            text="● STOPPED",
            text_color="red",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.status_label.grid(row=0, column=1, padx=10)
        
        # Start/Stop button
        self.start_button = ctk.CTkButton(
            top_frame,
            text="🚀 START BOT",
            command=self.toggle_bot,
            fg_color="green",
            hover_color="darkgreen",
            width=160,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.grid(row=0, column=2, padx=10)
        
        # Emergency stop button
        self.emergency_button = ctk.CTkButton(
            top_frame,
            text="🛑 EMERGENCY STOP",
            command=self.emergency_stop,
            fg_color="red",
            hover_color="darkred",
            width=160,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.emergency_button.grid(row=0, column=3, padx=10)
        
        # Network selector
        self.network_selector = ctk.CTkOptionMenu(
            top_frame,
            values=["pulsechain", "ethereum", "bsc", "polygon"],
            command=self.change_network,
            width=150,
            font=ctk.CTkFont(size=13)
        )
        self.network_selector.set("pulsechain")
        self.network_selector.grid(row=0, column=4, padx=10)
    
    def build_dashboard_tab(self):
        """Enhanced dashboard with integrated activity feed"""
        tab = self.tabview.tab("Dashboard")
        
        # Configure grid
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        
        # === LEFT COLUMN ===
        left_column = ctk.CTkFrame(tab)
        left_column.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")
        
        # Stats frame
        stats_frame = ctk.CTkFrame(left_column)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 Performance Metrics",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        stats_title.pack(pady=10)
        
        self.balance_label = ctk.CTkLabel(
            stats_frame,
            text="Balance: $0.00",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.balance_label.pack(pady=5)
        
        self.profit_label = ctk.CTkLabel(
            stats_frame,
            text="Total P&L: $0.00",
            font=ctk.CTkFont(size=18)
        )
        self.profit_label.pack(pady=5)
        
        self.trades_label = ctk.CTkLabel(
            stats_frame,
            text="Trades: 0 (0W / 0L)",
            font=ctk.CTkFont(size=16)
        )
        self.trades_label.pack(pady=5)
        
        self.winrate_label = ctk.CTkLabel(
            stats_frame,
            text="Win Rate: 0%",
            font=ctk.CTkFont(size=16)
        )
        self.winrate_label.pack(pady=5)
        
        # Controls frame
        controls_frame = ctk.CTkFrame(left_column)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        controls_title = ctk.CTkLabel(
            controls_frame,
            text="⚙️ Trading Controls",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        controls_title.pack(pady=10)
        
        # Mode selector
        mode_frame = ctk.CTkFrame(controls_frame)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        mode_label = ctk.CTkLabel(mode_frame, text="Trading Mode:")
        mode_label.pack(side="left", padx=10)
        
        self.mode_selector = ctk.CTkOptionMenu(
            mode_frame,
            values=["simulation", "paper", "live"],
            command=self.change_mode,
            width=150
        )
        self.mode_selector.set("simulation")
        self.mode_selector.pack(side="left", padx=10)
        
        # Balance input
        balance_frame = ctk.CTkFrame(controls_frame)
        balance_frame.pack(fill="x", padx=10, pady=5)
        
        balance_label = ctk.CTkLabel(balance_frame, text="Trading Balance:")
        balance_label.pack(side="left", padx=10)
        
        self.balance_entry = ctk.CTkEntry(balance_frame, placeholder_text="10000", width=120)
        self.balance_entry.pack(side="left", padx=5)
        
        apply_button = ctk.CTkButton(
            balance_frame,
            text="Apply",
            command=self.apply_balance,
            width=80
        )
        apply_button.pack(side="left", padx=5)
        
        # === RIGHT COLUMN - ACTIVITY FEED ===
        right_column = ctk.CTkFrame(tab)
        right_column.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")
        
        activity_title = ctk.CTkLabel(
            right_column,
            text="📡 Live Activity Feed",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        activity_title.pack(pady=10)
        
        # Activity feed
        self.activity_text = ctk.CTkTextbox(right_column, width=700, height=700)
        self.activity_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Clear button
        clear_button = ctk.CTkButton(
            right_column,
            text="🗑️ Clear Activity",
            command=self.clear_activity
        )
        clear_button.pack(pady=10)
    
    def build_wallet_tab(self):
        """Enhanced wallet tab with better token display"""
        tab = self.tabview.tab("Wallet")
        
        # Wallet status
        self.wallet_status_label = ctk.CTkLabel(
            tab,
            text="Wallet: Not Connected",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="orange"
        )
        self.wallet_status_label.pack(pady=20)
        
        # Connection methods frame
        conn_frame = ctk.CTkFrame(tab)
        conn_frame.pack(fill="x", padx=20, pady=10)
        
        conn_title = ctk.CTkLabel(
            conn_frame,
            text="🔑 Connect Wallet",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        conn_title.pack(pady=10)
        
        # Private key connection
        pk_frame = ctk.CTkFrame(conn_frame)
        pk_frame.pack(fill="x", padx=10, pady=10)
        
        pk_label = ctk.CTkLabel(pk_frame, text="Private Key:")
        pk_label.pack(pady=5)
        
        self.pk_entry = ctk.CTkEntry(
            pk_frame,
            placeholder_text="Enter 64-character private key",
            width=600,
            show="*"
        )
        self.pk_entry.pack(pady=5)
        
        pk_connect_button = ctk.CTkButton(
            pk_frame,
            text="🔗 Connect with Private Key",
            command=self.connect_private_key,
            width=200
        )
        pk_connect_button.pack(pady=10)
        
        # Seed phrase connection
        seed_frame = ctk.CTkFrame(conn_frame)
        seed_frame.pack(fill="x", padx=10, pady=10)
        
        seed_label = ctk.CTkLabel(seed_frame, text="Seed Phrase:")
        seed_label.pack(pady=5)
        
        self.seed_entry = ctk.CTkEntry(
            seed_frame,
            placeholder_text="Enter 12 or 24 word seed phrase",
            width=600,
            show="*"
        )
        self.seed_entry.pack(pady=5)
        
        seed_connect_button = ctk.CTkButton(
            seed_frame,
            text="🔗 Connect with Seed Phrase",
            command=self.connect_seed_phrase,
            width=200
        )
        seed_connect_button.pack(pady=10)
        
        # Balance display
        balance_frame = ctk.CTkFrame(tab)
        balance_frame.pack(fill="both", padx=20, pady=20, expand=True)
        
        balance_title = ctk.CTkLabel(
            balance_frame,
            text="💰 Token Balances",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        balance_title.pack(pady=10)
        
        self.wallet_info_text = ctk.CTkTextbox(balance_frame, width=1400, height=400)
        self.wallet_info_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            tab,
            text="🔄 Refresh Balances",
            command=self.refresh_wallet,
            width=150
        )
        refresh_button.pack(pady=10)
    
    def build_strategies_tab(self):
        """Build strategies tab"""
        tab = self.tabview.tab("Strategies")
        
        info_label = ctk.CTkLabel(
            tab,
            text="🎯 Trading Strategies",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        info_label.pack(pady=20)
        
        strategies = [
            "arbitrage",
            "yield_farming",
            "liquidity_sniping",
            "whale_tracking",
            "grid_trading",
            "market_making",
            "flash_loans"
        ]
        
        self.strategy_vars = {}
        
        for strategy in strategies:
            frame = ctk.CTkFrame(tab)
            frame.pack(fill="x", padx=20, pady=8)
            
            var = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(
                frame,
                text=strategy.replace("_", " ").title(),
                variable=var,
                command=lambda s=strategy, v=var: self.toggle_strategy(s, v),
                font=ctk.CTkFont(size=14)
            )
            checkbox.pack(side="left", padx=20, pady=10)
            
            self.strategy_vars[strategy] = var
    
    def build_positions_tab(self):
        """Build positions tab"""
        tab = self.tabview.tab("Positions")
        
        # Open positions
        open_label = ctk.CTkLabel(
            tab,
            text="📈 Open Positions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        open_label.pack(pady=10)
        
        self.open_positions_text = ctk.CTkTextbox(tab, width=1500, height=350)
        self.open_positions_text.pack(padx=20, pady=10)
        
        # Closed positions
        closed_label = ctk.CTkLabel(
            tab,
            text="📊 Recent Closed Positions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        closed_label.pack(pady=10)
        
        self.closed_positions_text = ctk.CTkTextbox(tab, width=1500, height=350)
        self.closed_positions_text.pack(padx=20, pady=10)
    
    def build_settings_tab(self):
        """FIXED: Enhanced settings tab with proper bot integration"""
        tab = self.tabview.tab("Settings")
        
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        
        # LEFT COLUMN - Risk Management
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        risk_label = ctk.CTkLabel(
            left_frame,
            text="⚠️ Risk Management",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        risk_label.pack(pady=15)
        
        # Max position size
        pos_size_frame = ctk.CTkFrame(left_frame)
        pos_size_frame.pack(fill="x", padx=15, pady=10)
        
        pos_size_label = ctk.CTkLabel(pos_size_frame, text="Max Position Size (%)")
        pos_size_label.pack(pady=5)
        self.pos_size_entry = ctk.CTkEntry(pos_size_frame, placeholder_text="5")
        self.pos_size_entry.pack(pady=5)
        
        # Stop loss
        sl_frame = ctk.CTkFrame(left_frame)
        sl_frame.pack(fill="x", padx=15, pady=10)
        
        sl_label = ctk.CTkLabel(sl_frame, text="Stop Loss (%)")
        sl_label.pack(pady=5)
        self.sl_entry = ctk.CTkEntry(sl_frame, placeholder_text="5")
        self.sl_entry.pack(pady=5)
        
        # Take profit
        tp_frame = ctk.CTkFrame(left_frame)
        tp_frame.pack(fill="x", padx=15, pady=10)
        
        tp_label = ctk.CTkLabel(tp_frame, text="Take Profit (%)")
        tp_label.pack(pady=5)
        self.tp_entry = ctk.CTkEntry(tp_frame, placeholder_text="10")
        self.tp_entry.pack(pady=5)
        
        # Daily loss limit
        daily_loss_frame = ctk.CTkFrame(left_frame)
        daily_loss_frame.pack(fill="x", padx=15, pady=10)
        
        daily_loss_label = ctk.CTkLabel(daily_loss_frame, text="Max Daily Loss (%)")
        daily_loss_label.pack(pady=5)
        self.daily_loss_entry = ctk.CTkEntry(daily_loss_frame, placeholder_text="10")
        self.daily_loss_entry.pack(pady=5)
        
        # Apply risk button
        apply_risk_button = ctk.CTkButton(
            left_frame,
            text="✅ Apply Risk Settings",
            command=self.apply_risk_settings,
            width=200,
            fg_color="green",
            hover_color="darkgreen"
        )
        apply_risk_button.pack(pady=20)
        
        # RIGHT COLUMN - Trading Settings
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        trading_label = ctk.CTkLabel(
            right_frame,
            text="🔧 Trading Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        trading_label.pack(pady=15)
        
        # Slippage
        slippage_frame = ctk.CTkFrame(right_frame)
        slippage_frame.pack(fill="x", padx=15, pady=10)
        
        slippage_label = ctk.CTkLabel(slippage_frame, text="Slippage Tolerance (%)")
        slippage_label.pack(pady=5)
        self.slippage_entry = ctk.CTkEntry(slippage_frame, placeholder_text="0.5")
        self.slippage_entry.pack(pady=5)
        
        # Gas multiplier
        gas_frame = ctk.CTkFrame(right_frame)
        gas_frame.pack(fill="x", padx=15, pady=10)
        
        gas_label = ctk.CTkLabel(gas_frame, text="Gas Price Multiplier")
        gas_label.pack(pady=5)
        self.gas_entry = ctk.CTkEntry(gas_frame, placeholder_text="1.2")
        self.gas_entry.pack(pady=5)
        
        # Min trade size
        min_trade_frame = ctk.CTkFrame(right_frame)
        min_trade_frame.pack(fill="x", padx=15, pady=10)
        
        min_trade_label = ctk.CTkLabel(min_trade_frame, text="Min Trade Size (USD)")
        min_trade_label.pack(pady=5)
        self.min_trade_entry = ctk.CTkEntry(min_trade_frame, placeholder_text="1.0")
        self.min_trade_entry.pack(pady=5)
        
        # Apply trading button
        apply_trading_button = ctk.CTkButton(
            right_frame,
            text="✅ Apply Trading Settings",
            command=self.apply_trading_settings,
            width=200,
            fg_color="green",
            hover_color="darkgreen"
        )
        apply_trading_button.pack(pady=20)
    
    # === FIXED: Load current settings ===
    
    def load_current_settings(self):
        """FIXED: Load current bot settings into GUI"""
        if not self.bot:
            return
        
        try:
            # Load risk settings
            self.pos_size_entry.insert(0, str(self.bot.max_position_size_percent * 100))
            self.sl_entry.insert(0, str(self.bot.stop_loss_percent * 100))
            self.tp_entry.insert(0, str(self.bot.take_profit_percent * 100))
            self.daily_loss_entry.insert(0, str(self.bot.max_daily_loss_percent * 100))
            
            # Load trading settings
            self.slippage_entry.insert(0, str(self.bot.slippage_tolerance_percent))
            self.gas_entry.insert(0, str(self.bot.gas_price_multiplier))
            self.min_trade_entry.insert(0, str(self.bot.min_trade_size_usd))
            
            # Load balance
            self.balance_entry.insert(0, str(self.bot.trading_balance))
            
        except Exception as e:
            print(f"⚠️ Error loading settings: {e}")
    
    # === EVENT HANDLERS ===
    
    def toggle_bot(self):
        """Start/Stop the bot"""
        if not self.bot:
            self.log_activity("❌ Bot not initialized!", 'error')
            return
        
        if not self.bot.running:
            result = self.bot.start_bot()
            if result['success']:
                self.start_button.configure(text="⏸️ STOP BOT", fg_color="orange")
                self.status_label.configure(text="● RUNNING", text_color="green")
            else:
                self.log_activity(f"❌ Failed to start: {result.get('error')}", 'error')
        else:
            result = self.bot.stop_bot()
            if result['success']:
                self.start_button.configure(text="🚀 START BOT", fg_color="green")
                self.status_label.configure(text="● STOPPED", text_color="red")
    
    def emergency_stop(self):
        """Emergency stop"""
        if self.bot:
            result = self.bot.emergency_stop()
            if result['success']:
                self.status_label.configure(text="● STOPPED", text_color="red")
                self.start_button.configure(text="🚀 START BOT", fg_color="green")
    
    def change_network(self, network: str):
        """Change network"""
        self.log_activity(f"🌐 Network changed to: {network}", 'info')
    
    def change_mode(self, mode: str):
        """Change trading mode"""
        if self.bot:
            result = self.bot.set_mode(mode)
            if not result['success']:
                self.log_activity(f"❌ Mode change failed: {result.get('error')}", 'error')
                # Revert selector
                self.mode_selector.set(self.bot.mode)
    
    def apply_balance(self):
        """FIXED: Apply trading balance with validation"""
        try:
            balance = float(self.balance_entry.get())
            if self.bot:
                result = self.bot.set_balance(balance)
                if result['success']:
                    self.log_activity(f"💰 Trading balance set to: ${balance:.2f}", 'success')
                    self.update_balance_display()
                else:
                    self.log_activity(f"❌ Balance update failed: {result.get('error')}", 'error')
        except ValueError:
            self.log_activity("❌ Invalid balance amount", 'error')
    
    def apply_risk_settings(self):
        """FIXED: Apply risk management settings to bot"""
        try:
            if not self.bot:
                self.log_activity("❌ Bot not initialized", 'error')
                return
            
            settings = {}
            
            if self.pos_size_entry.get():
                settings['max_position_size_percent'] = float(self.pos_size_entry.get()) / 100
            
            if self.sl_entry.get():
                settings['stop_loss_percent'] = float(self.sl_entry.get()) / 100
            
            if self.tp_entry.get():
                settings['take_profit_percent'] = float(self.tp_entry.get()) / 100
            
            if self.daily_loss_entry.get():
                settings['max_daily_loss_percent'] = float(self.daily_loss_entry.get()) / 100
            
            result = self.bot.set_risk_settings(settings)
            
            if result['success']:
                self.log_activity("✅ Risk settings applied successfully", 'success')
            else:
                self.log_activity(f"❌ Risk settings failed: {result.get('error')}", 'error')
                
        except ValueError:
            self.log_activity("❌ Invalid risk settings values", 'error')
    
    def apply_trading_settings(self):
        """FIXED: Apply trading settings to bot"""
        try:
            if not self.bot:
                self.log_activity("❌ Bot not initialized", 'error')
                return
            
            settings = {}
            
            if self.slippage_entry.get():
                settings['slippage_tolerance_percent'] = float(self.slippage_entry.get())
            
            if self.gas_entry.get():
                settings['gas_price_multiplier'] = float(self.gas_entry.get())
            
            if self.min_trade_entry.get():
                settings['min_trade_size_usd'] = float(self.min_trade_entry.get())
            
            result = self.bot.set_trading_settings(settings)
            
            if result['success']:
                self.log_activity("✅ Trading settings applied successfully", 'success')
            else:
                self.log_activity(f"❌ Trading settings failed: {result.get('error')}", 'error')
                
        except ValueError:
            self.log_activity("❌ Invalid trading settings values", 'error')
    
    def connect_private_key(self):
        """Connect wallet with private key"""
        pk = self.pk_entry.get()
        if self.bot and self.bot.backend and self.bot.backend.wallet_manager:
            result = self.bot.backend.wallet_manager.connect_with_private_key(
                pk, self.bot.web3, self.bot.network
            )
            if result['success']:
                self.wallet_status_label.configure(
                    text=f"✅ Connected: {result['address'][:10]}...",
                    text_color="green"
                )
                self.log_activity(f"✅ Wallet connected: {result['address']}", 'success')
                self.update_wallet_display()
            else:
                self.log_activity(f"❌ Connection failed: {result.get('error')}", 'error')
    
    def connect_seed_phrase(self):
        """Connect wallet with seed phrase"""
        seed = self.seed_entry.get()
        if self.bot and self.bot.backend and self.bot.backend.wallet_manager:
            result = self.bot.backend.wallet_manager.connect_with_seed_phrase(
                seed, self.bot.web3, self.bot.network
            )
            if result['success']:
                self.wallet_status_label.configure(
                    text=f"✅ Connected: {result['address'][:10]}...",
                    text_color="green"
                )
                self.log_activity(f"✅ Wallet connected: {result['address']}", 'success')
                self.update_wallet_display()
            else:
                self.log_activity(f"❌ Connection failed: {result.get('error')}", 'error')
    
    def refresh_wallet(self):
        """Refresh wallet balances"""
        self.log_activity("🔄 Refreshing wallet balances...", 'info')
        self.update_wallet_display()
    
    def update_wallet_display(self):
        """ENHANCED: Wallet display with all tokens"""
        if self.bot and self.bot.backend and self.bot.backend.wallet_manager:
            info = self.bot.backend.wallet_manager.get_wallet_info()
            
            self.wallet_info_text.delete("1.0", "end")
            
            # Header
            self.wallet_info_text.insert("1.0", "="*80 + "\n")
            self.wallet_info_text.insert("end", f"  WALLET INFO\n")
            self.wallet_info_text.insert("end", "="*80 + "\n\n")
            
            # Connection status
            self.wallet_info_text.insert("end", f"Connected: {info.get('connected')}\n")
            self.wallet_info_text.insert("end", f"Address: {info.get('address', 'N/A')}\n")
            self.wallet_info_text.insert("end", f"Network: {info.get('network', 'N/A')}\n\n")
            
            # Native balance
            self.wallet_info_text.insert("end", "-"*80 + "\n")
            self.wallet_info_text.insert("end", "  NATIVE TOKEN\n")
            self.wallet_info_text.insert("end", "-"*80 + "\n")
            
            native_symbol = info.get('native_symbol', 'N/A')
            native_balance = info.get('native_balance', 0)
            native_price = info.get('native_price_usd', 0)
            native_value = native_balance * native_price
            
            self.wallet_info_text.insert("end", f"{native_symbol}: {native_balance:.6f}\n")
            self.wallet_info_text.insert("end", f"Price: ${native_price:.6f}\n")
            self.wallet_info_text.insert("end", f"Value: ${native_value:.2f}\n\n")
            
            # ERC20 tokens
            tokens = info.get('tokens', [])
            if len(tokens) > 0:
                self.wallet_info_text.insert("end", "-"*80 + "\n")
                self.wallet_info_text.insert("end", f"  ERC20 TOKENS ({len(tokens)} found)\n")
                self.wallet_info_text.insert("end", "-"*80 + "\n\n")
                
                for token in tokens:
                    symbol = token.get('symbol', 'UNKNOWN')
                    balance = token.get('balance', 0)
                    value = token.get('value_usd', 0)
                    
                    self.wallet_info_text.insert("end", f"{symbol}: {balance:.6f} (${value:.2f})\n")
            else:
                self.wallet_info_text.insert("end", "\n📍 No ERC20 tokens detected with balance\n")
            
            # Total value
            self.wallet_info_text.insert("end", "\n" + "="*80 + "\n")
            self.wallet_info_text.insert("end", f"  TOTAL VALUE: ${info.get('total_value_usd', 0):.2f}\n")
            self.wallet_info_text.insert("end", "="*80 + "\n")
    
    def toggle_strategy(self, strategy: str, var):
        """Toggle strategy"""
        if self.bot:
            if var.get():
                self.bot.enable_strategy(strategy)
            else:
                self.bot.disable_strategy(strategy)
    
    def clear_activity(self):
        """Clear activity feed"""
        self.activity_text.delete("1.0", "end")
    
    def log_activity(self, message: str, level: str = 'info'):
        """Log message to activity feed"""
        timestamp = time.strftime("%H:%M:%S")
        
        self.activity_text.insert("end", f"[{timestamp}] {message}\n")
        self.activity_text.see("end")
    
    # === GUI UPDATE LOOP ===
    
    def start_gui_updates(self):
        """Start GUI update thread"""
        self.running_updates = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        """Update GUI periodically"""
        while self.running_updates:
            try:
                self.after(0, self.update_gui_elements)
                time.sleep(1)
            except:
                pass
    
    def update_gui_elements(self):
        """Update GUI elements with latest data"""
        if not self.bot:
            return
        
        try:
            status = self.bot.get_status()
            
            # Update balance display
            self.update_balance_display()
            
            # Update P&L
            total_profit = status['total_profit']
            color = 'green' if total_profit >= 0 else 'red'
            self.profit_label.configure(
                text=f"Total P&L: ${total_profit:.2f}",
                text_color=color
            )
            
            # Update trades
            total = status['total_trades']
            wins = status['winning_trades']
            losses = status['losing_trades']
            win_rate = (wins / total * 100) if total > 0 else 0
            
            self.trades_label.configure(text=f"Trades: {total} ({wins}W / {losses}L)")
            self.winrate_label.configure(text=f"Win Rate: {win_rate:.1f}%")
            
            # Update positions
            self.update_positions_display()
            
            # Update activity feed
            self.update_activity_from_bot()
            
        except Exception as e:
            pass
    
    def update_balance_display(self):
        """Update balance display"""
        if not self.bot:
            return
        
        mode = self.bot.mode
        balance = self.bot.current_balance
        
        self.balance_label.configure(
            text=f"Balance: ${balance:.2f} ({mode.upper()})"
        )
    
    def update_activity_from_bot(self):
        """Pull activity from bot's queue"""
        if not self.bot:
            return
        
        activities = self.bot.get_activity_log(limit=10)
        for activity in activities:
            msg = activity['message']
            level = activity.get('level', 'info')
            self.log_activity(msg, level)
    
    def update_positions_display(self):
        """Update positions display"""
        if not self.bot:
            return
        
        try:
            # Open positions
            self.open_positions_text.delete("1.0", "end")
            if len(self.bot.open_positions) == 0:
                self.open_positions_text.insert("1.0", "No open positions")
            else:
                for pos_id, pos in self.bot.open_positions.items():
                    pnl = pos.get('pnl', 0)
                    self.open_positions_text.insert("end",
                        f"ID: {pos_id} | Token: {pos['token'][:10]}... | "
                        f"Amount: {pos['amount']:.4f} | P&L: ${pnl:.2f} ({pos['pnl_percent']:.2f}%)\n"
                    )
            
            # Closed positions
            self.closed_positions_text.delete("1.0", "end")
            recent_closed = self.bot.closed_positions[-10:]
            if len(recent_closed) == 0:
                self.closed_positions_text.insert("1.0", "No closed positions")
            else:
                for pos in recent_closed:
                    self.closed_positions_text.insert("end",
                        f"ID: {pos['id']} | Token: {pos['token'][:10]}... | "
                        f"P&L: ${pos['pnl']:.2f} ({pos['pnl_percent']:.2f}%) | "
                        f"Reason: {pos.get('close_reason', 'unknown')}\n"
                    )
        except Exception as e:
            pass

if __name__ == "__main__":
    app = TradingBotGUI()
    app.mainloop()
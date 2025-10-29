"""
State Manager v4.0 - Complete Save/Load System
Auto-saves everything: positions, trades, settings, balances
"""

import sys
from pathlib import Path

# CRITICAL FIX: Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import json
import sqlite3
from typing import Dict, List
from datetime import datetime
import shutil

class StateManager:
    """Manage bot state with JSON and SQLite backup"""
    
    def __init__(self, state_file: str = "data/state_v4.json", db_file: str = "data/trading_v4.db"):
        self.state_file = Path(state_file)
        self.db_file = Path(db_file)
        
        # Ensure data directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.state = self.load_state()
        
        # Initialize database
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    token TEXT,
                    amount REAL,
                    entry_price REAL,
                    current_price REAL,
                    pnl REAL,
                    pnl_percent REAL,
                    status TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    network TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    token_in TEXT,
                    token_out TEXT,
                    amount_in REAL,
                    amount_out REAL,
                    price REAL,
                    gas_cost REAL,
                    profit REAL,
                    timestamp TEXT,
                    tx_hash TEXT,
                    network TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS balances (
                    token TEXT,
                    amount REAL,
                    value_usd REAL,
                    network TEXT,
                    updated_at TEXT,
                    PRIMARY KEY (token, network)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def load_state(self) -> Dict:
        """Load state from JSON file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading state: {e}")
        
        # Default state
        return {
            'version': '4.0',
            'last_saved': None,
            'open_positions': [],
            'closed_positions': [],
            'recent_trades': [],
            'wallet_balances': {},
            'settings': {
                'max_position_size': 0.05,
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'max_daily_loss': 0.10,
                'slippage': 0.5
            },
            'performance': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_profit': 0,
                'total_loss': 0,
                'best_trade': 0,
                'worst_trade': 0
            },
            'metadata': {
                'bot_started': None,
                'last_trade': None,
                'total_runtime': 0
            }
        }
    
    def save_state(self) -> bool:
        """Save current state to JSON"""
        try:
            # Update timestamp
            self.state['last_saved'] = datetime.now().isoformat()
            
            # Create backup of existing state
            if self.state_file.exists():
                backup_file = self.state_file.with_suffix('.json.backup')
                shutil.copy2(self.state_file, backup_file)
            
            # Save to file
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def add_position(self, position: Dict):
        """Add or update a position"""
        try:
            # Add to state
            existing = [p for p in self.state['open_positions'] if p['id'] == position['id']]
            
            if existing:
                # Update existing
                idx = self.state['open_positions'].index(existing[0])
                self.state['open_positions'][idx] = position
            else:
                # Add new
                self.state['open_positions'].append(position)
            
            # Save to database
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO positions
                (id, token, amount, entry_price, current_price, pnl, pnl_percent, status, opened_at, closed_at, network)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.get('id'),
                position.get('token'),
                position.get('amount', 0),
                position.get('entry_price', 0),
                position.get('current_price', 0),
                position.get('pnl', 0),
                position.get('pnl_percent', 0),
                position.get('status', 'open'),
                position.get('opened_at'),
                position.get('closed_at'),
                position.get('network')
            ))
            
            conn.commit()
            conn.close()
            
            # Auto-save
            self.save_state()
            
        except Exception as e:
            print(f"Error adding position: {e}")
    
    def close_position(self, position_id: str):
        """Close a position"""
        try:
            # Find and move to closed
            position = next((p for p in self.state['open_positions'] if p['id'] == position_id), None)
            
            if position:
                position['status'] = 'closed'
                position['closed_at'] = datetime.now().isoformat()
                
                self.state['open_positions'].remove(position)
                self.state['closed_positions'].append(position)
                
                # Keep only last 100 closed positions
                self.state['closed_positions'] = self.state['closed_positions'][-100:]
                
                # Update database
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE positions
                    SET status = 'closed', closed_at = ?
                    WHERE id = ?
                ''', (position['closed_at'], position_id))
                
                conn.commit()
                conn.close()
                
                # Auto-save
                self.save_state()
                
        except Exception as e:
            print(f"Error closing position: {e}")
    
    def add_trade(self, trade: Dict):
        """Record a trade"""
        try:
            # Add to state
            self.state['recent_trades'].append(trade)
            
            # Keep only last 1000 trades
            self.state['recent_trades'] = self.state['recent_trades'][-1000:]
            
            # Update performance metrics
            self.state['performance']['total_trades'] += 1
            
            profit = trade.get('profit', 0)
            if profit > 0:
                self.state['performance']['winning_trades'] += 1
                self.state['performance']['total_profit'] += profit
                
                if profit > self.state['performance']['best_trade']:
                    self.state['performance']['best_trade'] = profit
            else:
                self.state['performance']['losing_trades'] += 1
                self.state['performance']['total_loss'] += abs(profit)
                
                if profit < self.state['performance']['worst_trade']:
                    self.state['performance']['worst_trade'] = profit
            
            # Update metadata
            self.state['metadata']['last_trade'] = datetime.now().isoformat()
            
            # Save to database
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO trades
                (id, type, token_in, token_out, amount_in, amount_out, price, gas_cost, profit, timestamp, tx_hash, network)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.get('id'),
                trade.get('type'),
                trade.get('token_in'),
                trade.get('token_out'),
                trade.get('amount_in', 0),
                trade.get('amount_out', 0),
                trade.get('price', 0),
                trade.get('gas_cost', 0),
                profit,
                trade.get('timestamp'),
                trade.get('tx_hash'),
                trade.get('network')
            ))
            
            conn.commit()
            conn.close()
            
            # Auto-save
            self.save_state()
            
        except Exception as e:
            print(f"Error adding trade: {e}")
    
    def update_balances(self, balances: Dict):
        """Update wallet balances"""
        try:
            self.state['wallet_balances'] = balances
            
            # Save to database
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            for network, tokens in balances.items():
                for token, data in tokens.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO balances
                        (token, amount, value_usd, network, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        token,
                        data.get('amount', 0),
                        data.get('value_usd', 0),
                        network,
                        datetime.now().isoformat()
                    ))
            
            conn.commit()
            conn.close()
            
            # Auto-save
            self.save_state()
            
        except Exception as e:
            print(f"Error updating balances: {e}")
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        return self.state['open_positions']
    
    def get_closed_positions(self, limit: int = 100) -> List[Dict]:
        """Get recent closed positions"""
        return self.state['closed_positions'][-limit:]
    
    def get_recent_trades(self, limit: int = 100) -> List[Dict]:
        """Get recent trades"""
        return self.state['recent_trades'][-limit:]
    
    def get_performance(self) -> Dict:
        """Get performance metrics"""
        return self.state['performance']
    
    def get_settings(self) -> Dict:
        """Get current settings"""
        return self.state['settings']
    
    def update_settings(self, settings: Dict):
        """Update settings"""
        self.state['settings'].update(settings)
        self.save_state()
    
    def export_to_csv(self, export_type: str = 'trades', output_file: str = None):
        """Export data to CSV"""
        try:
            import csv
            
            if not output_file:
                output_file = f"data/{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if export_type == 'trades':
                data = self.get_recent_trades(limit=10000)
            elif export_type == 'positions':
                data = self.get_closed_positions(limit=10000)
            else:
                return {'success': False, 'error': 'Invalid export type'}
            
            if not data:
                return {'success': False, 'error': 'No data to export'}
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            return {'success': True, 'file': str(output_path)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

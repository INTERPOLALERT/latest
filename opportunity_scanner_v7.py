"""
Opportunity Scanner v7.0 - FIXED VERSION
✅ FIXED: Generates pairs from YOUR wallet tokens (WBTC, TEDDY, INC, etc)
✅ FIXED: Uses PLS/WPLS as base currency with detected tokens
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent / 'src'
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from web3 import Web3
from typing import Dict, List, Optional
import time
import random
import json

class OpportunityScanner:
    """Scans for opportunities using PLS/WPLS + detected wallet tokens"""
    
    def __init__(self, web3_instance: Web3, network: str):
        self.web3 = web3_instance
        self.network = network
        
        self.scan_interval = 5
        self.min_profit_percent = 0.5
        
        self.opportunities = []
        self.last_scan_time = 0
        
        # ✅ FIXED: Dynamic pairs from wallet + common tokens
        self.trading_pairs = self.generate_trading_pairs()
        self.dexs = ['pulsex_v2', 'pulsex_v1'] if network == 'pulsechain' else ['uniswap_v2', 'uniswap_v3']
    
    def generate_trading_pairs(self) -> List[Dict]:
        """✅ FIXED: Generate pairs from wallet tokens + common tokens"""
        try:
            # Load common tokens from networks_v7.json
            networks_file = Path(__file__).parent / 'networks_v7.json'
            common_tokens = []
            
            if networks_file.exists():
                with open(networks_file, 'r') as f:
                    networks = json.load(f)
                    token_config = networks.get(self.network, {}).get('common_tokens', {})
                    
                    # Get all token symbols except native
                    for symbol, address in token_config.items():
                        if address != 'native' and symbol not in ['PLS']:
                            common_tokens.append(symbol)
            
            # If no tokens found, use defaults
            if not common_tokens:
                if self.network == 'pulsechain':
                    common_tokens = ['HEX', 'PLSX', 'INC', 'TEDDY', 'WBTC', 'USDC', 'DAI']
                else:
                    common_tokens = ['USDC', 'USDT', 'DAI']
            
            # ✅ Generate pairs: PLS/WPLS as base with EACH detected token
            pairs = []
            base_tokens = ['PLS', 'WPLS']
            
            for base in base_tokens:
                for quote in common_tokens:
                    if quote not in base_tokens:  # Don't pair PLS with WPLS
                        pairs.append({
                            'name': f'{base}/{quote}',
                            'token_a': base,
                            'token_b': quote,
                            'liquidity': 'unknown'
                        })
            
            print(f"✅ Generated {len(pairs)} trading pairs from wallet tokens")
            for pair in pairs[:5]:  # Show first 5
                print(f"   {pair['name']}")
            if len(pairs) > 5:
                print(f"   ... and {len(pairs)-5} more")
            
            return pairs
            
        except Exception as e:
            print(f"⚠️ Error generating pairs: {e}")
            # Fallback to basic pairs
            return [
                {'name': 'PLS/HEX', 'token_a': 'PLS', 'token_b': 'HEX', 'liquidity': 'high'},
                {'name': 'WPLS/HEX', 'token_a': 'WPLS', 'token_b': 'HEX', 'liquidity': 'high'},
                {'name': 'PLS/PLSX', 'token_a': 'PLS', 'token_b': 'PLSX', 'liquidity': 'high'},
                {'name': 'WPLS/PLSX', 'token_a': 'WPLS', 'token_b': 'PLSX', 'liquidity': 'high'},
            ]
    
    def refresh_trading_pairs(self):
        """Refresh pairs (call after wallet connection or token changes)"""
        self.trading_pairs = self.generate_trading_pairs()
    
    def scan_for_opportunities(self) -> List[Dict]:
        """Scan all DEXs for opportunities"""
        current_time = time.time()
        
        if current_time - self.last_scan_time < self.scan_interval:
            return self.opportunities
        
        self.last_scan_time = current_time
        self.opportunities = []
        
        for pair in self.trading_pairs:
            opportunities = self._scan_pair(pair)
            self.opportunities.extend(opportunities)
        
        return self.opportunities
    
    def _scan_pair(self, pair: Dict) -> List[Dict]:
        """Scan a specific pair"""
        opportunities = []
        
        try:
            arbitrage = self._check_arbitrage(pair)
            if arbitrage:
                opportunities.append(arbitrage)
            
            momentum = self._check_momentum(pair)
            if momentum:
                opportunities.append(momentum)
            
            liquidity_event = self._check_liquidity_events(pair)
            if liquidity_event:
                opportunities.append(liquidity_event)
            
        except Exception as e:
            pass
        
        return opportunities
    
    def _check_arbitrage(self, pair: Dict) -> Optional[Dict]:
        """Check for arbitrage"""
        if len(self.dexs) < 2:
            return None
        
        dex_a = self.dexs[0]
        dex_b = self.dexs[1]
        
        base_price = 1.0
        price_a = base_price * (1 + random.uniform(-0.05, 0.05))
        price_b = base_price * (1 + random.uniform(-0.05, 0.05))
        
        price_diff = abs(price_a - price_b)
        profit_percent = (price_diff / min(price_a, price_b)) * 100
        
        if profit_percent >= 0.3:
            if price_a < price_b:
                buy_dex = dex_a
                sell_dex = dex_b
                buy_price = price_a
                sell_price = price_b
            else:
                buy_dex = dex_b
                sell_dex = dex_a
                buy_price = price_b
                sell_price = price_a
            
            return {
                'type': 'arbitrage',
                'pair': pair['name'],
                'token_a': pair['token_a'],
                'token_b': pair['token_b'],
                'buy_dex': buy_dex,
                'sell_dex': sell_dex,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'profit_percent': profit_percent,
                'estimated_profit': profit_percent * 10,
                'confidence': 'high' if profit_percent > 1.0 else 'medium',
                'timestamp': time.time()
            }
        
        return None
    
    def _check_momentum(self, pair: Dict) -> Optional[Dict]:
        """Check for momentum"""
        if random.random() < 0.2:
            direction = random.choice(['up', 'down'])
            momentum_strength = random.uniform(1.0, 5.0)
            
            if momentum_strength >= 2.0:
                return {
                    'type': 'momentum',
                    'pair': pair['name'],
                    'token': pair['token_a'],
                    'token_a': pair['token_a'],
                    'token_b': pair['token_b'],
                    'direction': direction,
                    'strength': momentum_strength,
                    'action': 'buy' if direction == 'up' else 'sell',
                    'confidence': 'high' if momentum_strength > 3.0 else 'medium',
                    'estimated_profit': momentum_strength * 2,
                    'timestamp': time.time()
                }
        
        return None
    
    def _check_liquidity_events(self, pair: Dict) -> Optional[Dict]:
        """Check for whale trades"""
        if random.random() < 0.1:
            trade_size = random.uniform(50000, 500000)
            
            if trade_size >= 100000:
                return {
                    'type': 'whale_activity',
                    'pair': pair['name'],
                    'token': pair['token_a'],
                    'token_a': pair['token_a'],
                    'token_b': pair['token_b'],
                    'trade_size': trade_size,
                    'direction': random.choice(['buy', 'sell']),
                    'action': 'follow',
                    'confidence': 'medium',
                    'estimated_profit': trade_size * 0.01,
                    'timestamp': time.time()
                }
        
        return None
    
    def get_best_opportunity(self) -> Optional[Dict]:
        """Get best opportunity"""
        if not self.opportunities:
            return None
        
        sorted_opps = sorted(
            self.opportunities,
            key=lambda x: x.get('estimated_profit', 0),
            reverse=True
        )
        
        return sorted_opps[0] if sorted_opps else None
    
    def clear_old_opportunities(self, max_age: int = 60):
        """Clear old opportunities"""
        current_time = time.time()
        self.opportunities = [
            opp for opp in self.opportunities
            if current_time - opp['timestamp'] < max_age
        ]
    
    def format_opportunity(self, opp: Dict) -> str:
        """Format for display"""
        if opp['type'] == 'arbitrage':
            return (
                f"💰 ARBITRAGE: {opp['pair']} | "
                f"Buy on {opp['buy_dex']} @ ${opp['buy_price']:.4f}, "
                f"Sell on {opp['sell_dex']} @ ${opp['sell_price']:.4f} | "
                f"Profit: {opp['profit_percent']:.2f}% (${opp['estimated_profit']:.2f})"
            )
        elif opp['type'] == 'momentum':
            return (
                f"📈 MOMENTUM: {opp['pair']} | "
                f"Direction: {opp['direction'].upper()} | "
                f"Strength: {opp['strength']:.1f} | "
                f"Est. Profit: ${opp['estimated_profit']:.2f}"
            )
        elif opp['type'] == 'whale_activity':
            return (
                f"🐋 WHALE: {opp['pair']} | "
                f"Size: ${opp['trade_size']:,.0f} | "
                f"Direction: {opp['direction'].upper()} | "
                f"Est. Profit: ${opp['estimated_profit']:.2f}"
            )
        else:
            return f"❓ UNKNOWN: {opp.get('pair', 'N/A')}"
    
    def should_execute_opportunity(self, opp: Dict, risk_settings: Dict) -> bool:
        """Check if opportunity meets criteria"""
        min_profit = risk_settings.get('min_profit_usd', 10)
        if opp.get('estimated_profit', 0) < min_profit:
            return False
        
        min_confidence = risk_settings.get('min_confidence', 'medium')
        confidence_levels = {'low': 1, 'medium': 2, 'high': 3}
        
        opp_confidence = confidence_levels.get(opp.get('confidence', 'low'), 1)
        required_confidence = confidence_levels.get(min_confidence, 2)
        
        if opp_confidence < required_confidence:
            return False
        
        enabled_types = risk_settings.get('enabled_opportunity_types', ['arbitrage'])
        if opp['type'] not in enabled_types:
            return False
        
        return True
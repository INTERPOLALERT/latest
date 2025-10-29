"""
Price Oracle v4.0 - Multi-source PulseChain Token Pricing
Priority: Bullscope > GoPulse > DexScreener > Moralis > GeckoTerminal > Fallback
"""

import requests
from typing import Optional, Dict
import time

class PriceOracle:
    """Fetch real-time token prices from multiple sources"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 30  # 30 seconds
        
        # Token address mapping for PulseChain
        self.token_map = {
            'PLS': '0xA1077a294dDE1B09bB078844df40758a5D0f9a27',  # Use WPLS for price
            'WPLS': '0xA1077a294dDE1B09bB078844df40758a5D0f9a27',
            'HEX': '0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39',
            'PLSX': '0x95B303987A60C71504D99Aa1b13B4DA07b0790ab',
            'INC': '0x2fa878Ab3F87CC1C9737Fc071108F904c0B0C95d',
            'TEDDY': '0x4fE5851C9af07df9E5AD8217afAE1ea72737EbdA',
            'USDC': '0x15D38573d2feeb82e7ad5187aB8c1D52810B1f07',
            'DAI': '0xefD766cCb38EaF1dfd701853BFCe31359239F305',
            'WBTC': '0xb17D901469B9208B17d916112988A3FeD19b5cA1',
            'WETH': '0x02DcdD04e3F455D838cd1249292C58f3B79e3C3C',
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_address(self, token_symbol: str) -> str:
        """Get token address from symbol"""
        return self.token_map.get(token_symbol.upper(), '')
    
    def get_price(self, token_symbol: str) -> float:
        """Get token price with caching and fallback sources"""
        token_upper = token_symbol.upper()
        
        # Check cache
        if token_upper in self.cache:
            cached_time, cached_price = self.cache[token_upper]
            if time.time() - cached_time < self.cache_duration:
                return cached_price
        
        # Get address
        address = self.get_address(token_upper)
        if not address:
            return self._get_fallback_price(token_upper)
        
        # Try sources in priority order
        price = None
        
        # 1. Bullscope
        price = self._fetch_bullscope(address, token_upper)
        if price and price > 0:
            self.cache[token_upper] = (time.time(), price)
            return price
        
        # 2. GoPulse
        price = self._fetch_gopulse(address, token_upper)
        if price and price > 0:
            self.cache[token_upper] = (time.time(), price)
            return price
        
        # 3. DexScreener
        price = self._fetch_dexscreener(address)
        if price and price > 0:
            self.cache[token_upper] = (time.time(), price)
            return price
        
        # 4. GeckoTerminal
        price = self._fetch_geckoterminal(address)
        if price and price > 0:
            self.cache[token_upper] = (time.time(), price)
            return price
        
        # 5. Moralis (requires API key)
        price = self._fetch_moralis(address)
        if price and price > 0:
            self.cache[token_upper] = (time.time(), price)
            return price
        
        # 6. Fallback
        fallback = self._get_fallback_price(token_upper)
        self.cache[token_upper] = (time.time(), fallback)
        return fallback
    
    def _fetch_bullscope(self, address: str, symbol: str) -> Optional[float]:
        """Fetch from Bullscope"""
        try:
            # Bullscope endpoint - using token address
            url = f"https://api.bullscope.com/pulsechain/tokens/{address}"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'priceUSD' in data:
                    return float(data['priceUSD'])
                elif 'price' in data:
                    return float(data['price'])
        except:
            pass
        return None
    
    def _fetch_gopulse(self, address: str, symbol: str) -> Optional[float]:
        """Fetch from GoPulse"""
        try:
            url = f"https://api.gopulse.com/api/v1/tokens/{address}/price"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'usd' in data:
                    return float(data['usd'])
                elif 'price' in data:
                    return float(data['price'])
        except:
            pass
        return None
    
    def _fetch_dexscreener(self, address: str) -> Optional[float]:
        """Fetch from DexScreener"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and len(data['pairs']) > 0:
                    # Find PulseChain pair with best liquidity
                    pulsechain_pairs = [p for p in data['pairs'] if p.get('chainId') == 'pulsechain']
                    if pulsechain_pairs:
                        # Sort by liquidity
                        pulsechain_pairs.sort(key=lambda x: x.get('liquidity', {}).get('usd', 0), reverse=True)
                        best_pair = pulsechain_pairs[0]
                        if 'priceUsd' in best_pair:
                            return float(best_pair['priceUsd'])
        except:
            pass
        return None
    
    def _fetch_geckoterminal(self, address: str) -> Optional[float]:
        """Fetch from GeckoTerminal"""
        try:
            url = f"https://api.geckoterminal.com/api/v2/networks/pulsechain/tokens/{address}"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'attributes' in data['data']:
                    attrs = data['data']['attributes']
                    if 'price_usd' in attrs:
                        return float(attrs['price_usd'])
        except:
            pass
        return None
    
    def _fetch_moralis(self, address: str) -> Optional[float]:
        """Fetch from Moralis (requires API key)"""
        # Placeholder - implement if you have Moralis API key
        return None
    
    def _get_fallback_price(self, symbol: str) -> float:
        """Fallback approximate prices"""
        fallbacks = {
            'PLS': 0.00001,
            'WPLS': 0.00001,
            'HEX': 0.005,
            'PLSX': 0.000001,
            'INC': 0.00001,
            'TEDDY': 0.00000001,
            'USDC': 1.0,
            'DAI': 1.0,
            'WBTC': 95000.0,
            'WETH': 3500.0,
        }
        return fallbacks.get(symbol, 0.0)
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, float]:
        """Get prices for multiple tokens"""
        return {symbol: self.get_price(symbol) for symbol in symbols}
    
    def calculate_token_amount_for_usd(self, token_symbol: str, usd_value: float) -> int:
        """
        Calculate token amount needed for USD value (returns wei)
        Example: $1 USD / $0.00001 per WPLS = 100,000 WPLS = 100000000000000000000000 wei
        """
        price = self.get_price(token_symbol)
        if price == 0:
            print(f"WARNING: Price for {token_symbol} is 0!")
            return 0
        
        # Calculate tokens needed
        token_amount = usd_value / price
        
        # Convert to wei (18 decimals)
        amount_wei = int(token_amount * 10**18)
        
        print(f"💵 USD→Token: ${usd_value} / ${price} = {token_amount:.2f} {token_symbol} = {amount_wei} wei")
        
        return amount_wei
    
    def calculate_usd_value(self, token_symbol: str, amount_wei: int) -> float:
        """
        Calculate USD value from token amount (in wei)
        Example: 100,000 WPLS * $0.00001 = $1 USD
        """
        price = self.get_price(token_symbol)
        
        # Convert from wei
        token_amount = amount_wei / 10**18
        
        # Calculate USD
        usd_value = token_amount * price
        
        return usd_value
    
    def get_price_by_address(self, address: str) -> float:
        """Get price directly by address"""
        # Check known addresses
        for symbol, token_addr in self.token_map.items():
            if token_addr.lower() == address.lower():
                return self.get_price(symbol)
        
        # Try DexScreener directly
        price = self._fetch_dexscreener(address)
        if price and price > 0:
            return price
        
        return 0.0

# Global instance
price_oracle = PriceOracle()
'''Data Fetcher - Yahoo Finance + popular stock lists'''
import yfinance as yf
import pandas as pd
import time, hashlib

_fetch_cache = {}
_info_cache = {}

def get_popular_stocks():
    return [
        {"symbol": "AAPL", "name": "Apple", "market": "US"},
        {"symbol": "MSFT", "name": "Microsoft", "market": "US"},
        {"symbol": "AMZN", "name": "Amazon", "market": "US"},
        {"symbol": "NVDA", "name": "NVIDIA", "market": "US"},
        {"symbol": "META", "name": "Meta", "market": "US"},
        {"symbol": "TSLA", "name": "Tesla", "market": "US"},
        {"symbol": "JPM", "name": "JPMorgan", "market": "US"},
        {"symbol": "V", "name": "Visa", "market": "US"},
        {"symbol": "WMT", "name": "Walmart", "market": "US"},
        {"symbol": "0700.HK", "name": "Tencent", "market": "HK"},
        {"symbol": "9988.HK", "name": "Alibaba HK", "market": "HK"},
        {"symbol": "0941.HK", "name": "China Mobile", "market": "HK"},
        {"symbol": "3690.HK", "name": "Meituan", "market": "HK"},
        {"symbol": "2318.HK", "name": "Ping An", "market": "HK"},
        {"symbol": "0005.HK", "name": "HSBC", "market": "HK"},
        {"symbol": "0388.HK", "name": "HKEX", "market": "HK"},
        {"symbol": "1810.HK", "name": "Xiaomi", "market": "HK"},
        {"symbol": "2269.HK", "name": "WuXi Bio", "market": "HK"},
    ]

def fetch_stock_data(symbol: str, period: str = "6mo", interval: str = "1d"):
    """Fetch stock OHLCV data from Yahoo Finance with in-memory cache"""
    ck = hashlib.md5((symbol + period + interval).encode()).hexdigest()
    if ck in _fetch_cache:
        cached_data, cached_time = _fetch_cache[ck]
        if time.time() - cached_time < 3600:
            return cached_data.copy()
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        if df is not None and not df.empty:
            df = df[["Open","High","Low","Close","Volume"]]
            _fetch_cache[ck] = (df.copy(), time.time())
            return df
    except Exception:
        pass
    return pd.DataFrame()

def get_stock_info(symbol: str):
    """Get stock fundamental info with in-memory cache"""
    ck = hashlib.md5(symbol.encode()).hexdigest()
    if ck in _info_cache:
        cached_data, cached_time = _info_cache[ck]
        if time.time() - cached_time < 3600:
            return cached_data.copy()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        result = {
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector", "无"),
            "industry": info.get("industry", "无"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "currency": info.get("currency", "USD"),
        }
        _info_cache[ck] = (result.copy(), time.time())
        return result
    except Exception:
        return {"name": symbol, "sector": "无", "pe_ratio": None,
                "current_price": None, "market_cap": None,
                "52w_high": None, "52w_low": None, "currency": "USD"}
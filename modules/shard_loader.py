"""Shard Loader - Split long-period data loading into monthly chunks with timeout."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time, threading, hashlib

_shard_cache = {}
TIMEOUT_SEC = 10  # Per-shard timeout

def _parse_period_to_months(period_str):
    """Convert period string to number of months."""
    p = period_str.lower().strip()
    if p.endswith("mo"):
        return int(p.replace("mo",""))
    elif p.endswith("y"):
        return int(p.replace("y","")) * 12
    elif p.endswith("d"):
        return max(1, int(p.replace("d","")) // 30)
    return 6  # default

def _monthly_date_ranges(months_back, end_date=None):
    """Generate (start, end, label) tuples for monthly shards."""
    if end_date is None:
        end_date = datetime.now()
    ranges = []
    for i in range(months_back):
        shard_end = end_date - timedelta(days=30 * i)
        shard_start = shard_end - timedelta(days=35)  # slight overlap for safety
        label = shard_start.strftime("%Y-%m")
        ranges.append((shard_start.strftime("%Y-%m-%d"), shard_end.strftime("%Y-%m-%d"), label))
    return list(reversed(ranges))  # oldest first

def _download_shard_with_timeout(symbol, start_date, end_date, timeout=TIMEOUT_SEC):
    """Download one shard with timeout. Returns (DataFrame, error_msg)."""
    result = {"df": pd.DataFrame(), "error": None}

    def _download():
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d", auto_adjust=True)
            if df is not None and not df.empty:
                df = df[["Open","High","Low","Close","Volume"]]
            result["df"] = df if df is not None else pd.DataFrame()
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=_download, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        return pd.DataFrame(), f"超时({timeout}秒)"
    return result["df"], result["error"]


def load_sharded(symbol, period="1y", on_progress=None, on_cancel=None):
    """Load stock data in monthly shards with progress and cancellation.

    Args:
        symbol: Stock symbol
        period: yfinance-style period string (e.g. "1y", "6mo", "2y")
        on_progress: callback(completed, total, label, status)
        on_cancel: callback() -> bool, return True to cancel

    Returns:
        dict with keys: df (concatenated), missing_shards (list of labels),
                        total_shards, completed_shards, cancelled
    """
    cache_key = hashlib.md5(f"{symbol}_{period}_sharded".encode()).hexdigest()
    if cache_key in _shard_cache:
        cached, ts = _shard_cache[cache_key]
        if time.time() - ts < 300:  # 5 min cache
            return cached

    months = _parse_period_to_months(period)
    shards = _monthly_date_ranges(months)

    all_dfs = []
    missing = []
    cancelled = False

    for i, (start_d, end_d, label) in enumerate(shards):
        # Check cancellation
        if on_cancel and on_cancel():
            cancelled = True
            if on_progress:
                on_progress(i, len(shards), label, "已取消")
            break

        if on_progress:
            on_progress(i, len(shards), label, "加载中...")

        df_shard, err = _download_shard_with_timeout(symbol, start_d, end_d)

        if err:
            missing.append(label)
            if on_progress:
                on_progress(i + 1, len(shards), label, f"跳过: {err}")
        elif df_shard is not None and not df_shard.empty:
            all_dfs.append(df_shard)
            if on_progress:
                on_progress(i + 1, len(shards), label, f"OK ({len(df_shard)}行)")
        else:
            missing.append(label)
            if on_progress:
                on_progress(i + 1, len(shards), label, "无数据")

    # Merge
    if all_dfs:
        merged = pd.concat(all_dfs)
        merged = merged[~merged.index.duplicated(keep="first")].sort_index()
    else:
        merged = pd.DataFrame()

    result = {
        "df": merged,
        "missing_shards": missing,
        "total_shards": len(shards),
        "completed_shards": len(shards) - len(missing),
        "cancelled": cancelled,
    }

    _shard_cache[cache_key] = (result, time.time())
    return result


def quick_load(symbol, period="1mo"):
    """Fast single-shot load for short periods. Falls back to sharded for long."""
    months = _parse_period_to_months(period)
    if months <= 1:
        # Single download
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval="1d", auto_adjust=True)
            if df is not None and not df.empty:
                return df[["Open","High","Low","Close","Volume"]]
        except Exception:
            pass
        return pd.DataFrame()
    else:
        # Use sharded for longer periods
        result = load_sharded(symbol, period)
        return result["df"]


def clear_shard_cache():
    """Clear the shard cache."""
    _shard_cache.clear()
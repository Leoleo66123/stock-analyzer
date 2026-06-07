'''Backtest - Original Golden Cross Strategy (v5 additions commented)'''
import pandas as pd, numpy as np

# ===== V5 ADDITIONS (commented - future iteration) =====
# def _detect_regime_quarterly(df):
#     """Split data into bull/bear/sideways/high-vol regimes."""
#     ...
#
# def _black_swan_test(equity_curve, trade_pnls):
#     """Simulate -20%/-30%/-50% market crashes."""
#     ...
#
# def walk_forward_backtest_v5(df, train_window=252, test_window=21, step=21,
#                               max_position=0.20, freeze_after_losses=2,
#                               cost_pct=0.001, slippage=0.0005):
#     """Multi-asset walk-forward backtest with regime tracking and risk controls."""
#     ...
#
# def generate_backtest_summary_v5(trades, initial_capital=100000):
#     """Comprehensive backtest with regime breakdown + stress test."""
#     ...

def walk_forward_backtest(df, train_window=252, test_window=21, step=21,
                           cost_pct=0.001, slippage=0.0005):
    """Original walk-forward backtest with golden cross strategy."""
    n = len(df)
    if n < train_window + test_window:
        train_window = max(60, n // 3)
        test_window = max(5, n // 10)
        step = test_window
    trades = []
    for start in range(train_window, n - test_window, step):
        train = df.iloc[start - train_window:start]
        test = df.iloc[start:start + test_window]
        if len(train) < 50 or len(test) < 3:
            continue
        for i in range(1, len(test)):
            if "MA5" not in test.columns or "MA20" not in test.columns:
                continue
            ma5, ma20 = test["MA5"].iloc[i], test["MA20"].iloc[i]
            ma5_prev = test["MA5"].iloc[i - 1]
            ma20_prev = test["MA20"].iloc[i - 1]
            close = test["Close"].iloc[i]
            idx = test.index[i]
            if ma5 > ma20 and ma5_prev <= ma20_prev:
                cost = close * (cost_pct + slippage)
                trades.append({"date": str(idx), "action": "BUY", "price": close, "cost": cost})
            elif ma5 < ma20 and ma5_prev >= ma20_prev:
                cost = close * (cost_pct + slippage)
                trades.append({"date": str(idx), "action": "SELL", "price": close, "cost": cost})
    return trades

def generate_backtest_summary(trades, initial_capital=100000):
    """Original backtest summary: sharpe, sortino, calmar, win rate, max drawdown."""
    if not trades:
        return {"error": "无交易记录", "star_rating": 0}
    capital = initial_capital; position = 0; entry_price = 0
    trade_pnls = []; equity_curve = [initial_capital]
    for t in trades:
        if t["action"] == "BUY" and position == 0:
            max_shares = int(capital / t["price"])
            entry_price = t["price"]
            position = max_shares
            capital -= max_shares * t["price"] + t["cost"]
        elif t["action"] == "SELL" and position > 0:
            capital += position * t["price"] - t["cost"]
            pnl = (t["price"] - entry_price) * position - t["cost"] * 2
            trade_pnls.append(pnl)
            position = 0
        equity_curve.append(capital + position * t["price"])
    if position > 0 and trades:
        capital += position * trades[-1]["price"]
        equity_curve[-1] = capital
    total_return = (capital - initial_capital) / initial_capital * 100
    if trade_pnls:
        wins = sum(1 for p in trade_pnls if p > 0)
        win_rate = wins / len(trade_pnls) * 100
        avg_win = np.mean([p for p in trade_pnls if p > 0]) if wins > 0 else 0
        avg_loss = abs(np.mean([p for p in trade_pnls if p < 0])) if len(trade_pnls) - wins > 0 else 0
        profit_factor = (avg_win * wins) / (avg_loss * (len(trade_pnls) - wins) + 1e-10)
        mean_pnl = np.mean(trade_pnls); std_pnl = np.std(trade_pnls) or 1
        sharpe = mean_pnl / std_pnl * np.sqrt(len(trade_pnls)) if std_pnl > 0 else 0
        neg_vals = [p for p in trade_pnls if p < 0]
        neg_std = np.std(neg_vals) if neg_vals else 1
        sortino = mean_pnl / neg_std * np.sqrt(len(trade_pnls)) if neg_std > 0 else 0
    else:
        win_rate = avg_win = avg_loss = profit_factor = sharpe = sortino = 0
    equity_arr = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_arr) if len(equity_arr) > 0 else np.array([initial_capital])
    dd = (equity_arr - peak) / peak
    max_dd = abs(dd.min()) * 100 if len(dd) > 0 else 0
    calmar = total_return / max_dd if max_dd > 0 else 0
    max_cw = max_cl = cur_w = cur_l = 0
    for p in trade_pnls:
        if p > 0: cur_w += 1; cur_l = 0; max_cw = max(max_cw, cur_w)
        else: cur_l += 1; cur_w = 0; max_cl = max(max_cl, cur_l)
    stars = 0
    if total_return > 0: stars += 1
    if sharpe > 0.5: stars += 1
    if win_rate > 45: stars += 1
    if max_dd < 20: stars += 1
    if profit_factor > 1.2: stars += 1
    # ===== V5 ADDITIONS (commented) =====
    # regime_breakdown = {}
    # stress_test = {}
    return {
        "total_return": round(total_return, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "calmar_ratio": round(calmar, 2),
        "max_drawdown": round(max_dd, 2),
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "trade_count": len(trade_pnls),
        "total_signals": len(trades),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "max_consecutive_wins": max_cw,
        "max_consecutive_losses": max_cl,
        "equity_curve": equity_curve,
        "trade_pnls": trade_pnls,
        "star_rating": stars,
        # V5 fields (commented):
        # "regime_breakdown": {},
        # "stress_test": {},
    }
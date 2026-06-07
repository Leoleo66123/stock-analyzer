'''Risk Manager - Original (v5 position limits + freeze commented)'''
import numpy as np

# Original neutral values (effectively disabled)
MAX_POSITION_PCT = 1.0
FREEZE_AFTER_LOSSES = 999
MAX_DRAWDOWN_LIMIT = 1.0
DAILY_LOSS_LIMIT = 1.0

# ===== V5 VALUES (commented) =====
# MAX_POSITION_PCT = 0.20
# FREEZE_AFTER_LOSSES = 2
# MAX_DRAWDOWN_LIMIT = 0.25
# DAILY_LOSS_LIMIT = 0.05

def calc_position_size(signal_strength, capital, price, atr=0):
    """Original: full position (v5 cap commented)."""
    max_shares = int(capital / price) if price > 0 else 0
    return max_shares, 1.0

def calc_stop_loss(entry_price, atr, multiplier=2.0, side='long'):
    if side == 'long': return entry_price - atr * multiplier
    return entry_price + atr * multiplier

def calc_take_profit(entry_price, atr, multiplier=3.0, side='long'):
    if side == 'long': return entry_price + atr * multiplier
    return entry_price - atr * multiplier

def check_circuit_breaker(equity_curve, max_dd_pct=1.0, consecutive_losses=999):
    """Original: effectively disabled (v5 limits commented)."""
    return False, ""

# ===== V5 FUNCTIONS (commented) =====
# def black_swan_stress(equity, crash_pcts=[-0.20, -0.30, -0.50]):
#     ...
#
# def check_consecutive_losses(trade_pnls, freeze_threshold=2):
#     ...
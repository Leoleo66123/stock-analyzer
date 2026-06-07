'''Portfolio Manager with Alerts - SQLite-based'''
import sqlite3, pandas as pd, os
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "portfolio.db")

def _conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS holdings (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, name TEXT, buy_price REAL, quantity REAL, buy_date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT UNIQUE, name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, condition TEXT, value REAL, active INTEGER DEFAULT 1)")
    c.commit()
    return c

def add_holding(symbol, name, buy_price, quantity, buy_date):
    c = _conn(); c.execute("INSERT INTO holdings (symbol,name,buy_price,quantity,buy_date) VALUES (?,?,?,?,?)", (symbol.upper(),name,buy_price,quantity,buy_date)); c.commit(); c.close()
def get_holdings():
    c = _conn(); df = pd.read_sql("SELECT * FROM holdings", c); c.close(); return df
def delete_holding(holding_id):
    c = _conn(); c.execute("DELETE FROM holdings WHERE id=?", (holding_id,)); c.commit(); c.close()
def calculate_pnl(holdings, prices):
    h = holdings.copy(); h["current_price"] = h["symbol"].map(prices).fillna(0); h["cost"] = h["buy_price"]*h["quantity"]; h["market_value"] = h["current_price"]*h["quantity"]; h["pnl"] = h["market_value"]-h["cost"]; h["pnl_pct"] = (h["pnl"]/h["cost"]*100).fillna(0); return h
def add_watchlist(symbol, name=""):
    c = _conn()
    try: c.execute("INSERT OR REPLACE INTO watchlist (symbol,name) VALUES (?,?)", (symbol.upper(),name)); c.commit()
    except: pass
    c.close()
def get_watchlist():
    c = _conn(); df = pd.read_sql("SELECT * FROM watchlist ORDER BY id DESC", c); c.close(); return df if not df.empty else pd.DataFrame(columns=["id","symbol","name"])
def remove_watchlist(symbol):
    c = _conn(); c.execute("DELETE FROM watchlist WHERE symbol=?", (symbol.upper(),)); c.commit(); c.close()

def add_alert(symbol, condition, value):
    c = _conn(); c.execute("INSERT INTO alerts (symbol,condition,value) VALUES (?,?,?)", (symbol.upper(),condition,value)); c.commit(); c.close()
def get_alerts():
    c = _conn(); df = pd.read_sql("SELECT * FROM alerts WHERE active=1", c); c.close(); return df
def delete_alert(alert_id):
    c = _conn(); c.execute("DELETE FROM alerts WHERE id=?", (alert_id,)); c.commit(); c.close()
def check_alerts(symbol, price):
    alerts = get_alerts()
    if alerts.empty: return []
    triggered = []
    for _, row in alerts.iterrows():
        if row["symbol"].upper() != symbol.upper(): continue
        if row["condition"] == "above" and price > row["value"]:
            triggered.append(f"[Alert] {symbol} above {row['value']:.2f} (now: {price:.2f})")
        elif row["condition"] == "below" and price < row["value"]:
            triggered.append(f"[Alert] {symbol} below {row['value']:.2f} (now: {price:.2f})")
    return triggered

def generate_pdf_report(*args, **kwargs):
    pass

def get_sector_performance():
    try:
        import yfinance as yf
        etfs = {"XLK":"Technology","XLF":"Financials","XLE":"Energy","XLV":"Healthcare","XLI":"Industrials","XLP":"Consumer Staples","XLY":"Consumer Discretionary","XLB":"Materials","XLU":"Utilities","XLRE":"Real Estate","XLC":"Communication"}
        data = []
        for sym, name in etfs.items():
            t = yf.Ticker(sym); hist = t.history(period="5d")
            if len(hist) >= 2:
                chg = (hist["Close"].iloc[-1]/hist["Close"].iloc[-2]-1)*100
                data.append({"sector": name, "symbol": sym, "change_pct": round(chg, 2)})
        return pd.DataFrame(data)
    except: return pd.DataFrame()

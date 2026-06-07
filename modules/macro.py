'''Macroeconomic indicators via FRED'''
import pandas as pd
import streamlit as st
from datetime import datetime

FRED_SERIES = {
    "Fed Funds Rate": "FEDFUNDS",
    "CPI YoY": "CPIAUCSL",
    "Unemployment": "UNRATE",
    "GDP": "GDP",
    "10Y Treasury": "DGS10",
    "VIX": "VIXCLS",
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_macro_data():
    try:
        from fredapi import Fred
        fred = Fred(api_key=st.secrets.get("FRED_API_KEY", ""))
        if not fred.api_key:
            return {"error": "FRED API key not configured. Set FRED_API_KEY in .streamlit/secrets.toml"}
        data = {}
        for name, series_id in FRED_SERIES.items():
            try:
                s = fred.get_series(series_id)
                s = s.dropna()
                if len(s) > 0:
                    data[name] = {"latest": round(float(s.iloc[-1]), 2), "date": str(s.index[-1])}
            except Exception:
                data[name] = {"latest": None, "date": None}
        return data
    except ImportError:
        return {"error": "fredapi not installed"}
    except Exception as e:
        return {"error": str(e)}

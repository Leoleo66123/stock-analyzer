'''Chart Visualizer - Plotly candlestick, MACD, prediction, equity curve'''
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_candlestick_chart(df, signals_df, show_sma=True, show_bb=True):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                 name="Price", increasing_line_color="#26a69a", decreasing_line_color="#e15241"), row=1, col=1)
    if show_sma:
        for ma, color in [("MA5","#ffa726"),("MA20","#4e8cff"),("MA60","#ab47bc")]:
            if ma in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df[ma], mode="lines", name=ma, line=dict(color=color,width=1)), row=1, col=1)
        for ema, color in [("EMA12","#ffee58"),("EMA26","#ef5350")]:
            if ema in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df[ema], mode="lines", name=ema, line=dict(color=color,width=1,dash="dot")), row=1, col=1)
    if show_bb and "BB_Up" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Up"], mode="lines", name="BB Up", line=dict(color="gray",width=0.5,dash="dash"), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Low"], mode="lines", name="BB Low", line=dict(color="gray",width=0.5,dash="dash"), fill="tonexty", fillcolor="rgba(128,128,128,0.1)", showlegend=False), row=1, col=1)
    buys = signals_df[signals_df["signal"]=="BUY"]
    sells = signals_df[signals_df["signal"]=="SELL"]
    if len(buys)>0:
        fig.add_trace(go.Scatter(x=buys.index, y=buys["Low"]*0.99, mode="markers", marker=dict(symbol="triangle-up",size=10,color="#26a69a"), name="BUY"), row=1, col=1)
    if len(sells)>0:
        fig.add_trace(go.Scatter(x=sells.index, y=sells["High"]*1.01, mode="markers", marker=dict(symbol="triangle-down",size=10,color="#e15241"), name="SELL"), row=1, col=1)
    colors = ["#e15241" if df["Close"].iloc[i] < df["Open"].iloc[i] else "#26a69a" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors, showlegend=False), row=2, col=1)
    fig.update_layout(height=500, margin=dict(l=0,r=0,t=10,b=0), template="plotly_dark", paper_bgcolor="#13161a", plot_bgcolor="#13161a", hovermode="x unified", xaxis_rangeslider_visible=False, legend=dict(orientation="h",yanchor="top",y=1.15,xanchor="left",x=0,font=dict(size=10)))
    fig.update_xaxes(showgrid=True, gridcolor="#2a2e35")
    fig.update_yaxes(showgrid=True, gridcolor="#2a2e35")
    return fig

def create_macd_chart(df):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Hist", marker_color=["#26a69a" if v>=0 else "#e15241" for v in df["MACD_Hist"]]), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD", line=dict(color="#4e8cff",width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], mode="lines", name="Signal", line=dict(color="#ffa726",width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI", line=dict(color="#ab47bc",width=1)), row=1, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#e15241", row=1, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", row=1, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="#3a3e45", row=2, col=1)
    fig.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0), template="plotly_dark", paper_bgcolor="#13161a", plot_bgcolor="#13161a", hovermode="x unified", showlegend=False)
    fig.update_xaxes(showgrid=True, gridcolor="#2a2e35")
    fig.update_yaxes(showgrid=True, gridcolor="#2a2e35")
    return fig

def create_prediction_chart(prediction):
    fig = go.Figure()
    forecast = prediction.get("forecast", [])
    lower = prediction.get("forecast_lower", [])
    upper = prediction.get("forecast_upper", [])
    if forecast and len(forecast) > 0:
        days = list(range(1, len(forecast)+1))
        if lower and upper:
            fig.add_trace(go.Scatter(x=days+days[::-1], y=upper+lower[::-1], fill="toself", fillcolor="rgba(78,140,255,0.2)", line=dict(color="rgba(78,140,255,0)"), name="95% CI"))
        fig.add_trace(go.Scatter(x=days, y=forecast, mode="lines+markers", name="Forecast", line=dict(color="#4e8cff",width=2), marker=dict(size=8)))
    fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), template="plotly_dark", paper_bgcolor="#13161a", plot_bgcolor="#13161a", xaxis_title="Days Ahead", yaxis_title="Price")
    return fig

def create_feature_importance_chart(fi_df):
    fig = go.Figure(go.Bar(x=fi_df["importance"].values, y=fi_df["feature"].values, orientation="h", marker_color="#4e8cff"))
    fig.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0), template="plotly_dark", paper_bgcolor="#13161a", plot_bgcolor="#13161a")
    return fig

def create_equity_curve_chart(equity_curve):
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=equity_curve, mode="lines", name="Equity", line=dict(color="#4e8cff",width=2), fill="tozeroy", fillcolor="rgba(78,140,255,0.1)"))
    fig.add_hline(y=equity_curve[0] if equity_curve else 100000, line_dash="dash", line_color="#3a3e45")
    fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), template="plotly_dark", paper_bgcolor="#13161a", plot_bgcolor="#13161a", title="Equity Curve")
    return fig

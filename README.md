# 📈 Stock Analyzer — AI Quantitative Analysis System

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.57-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**English** | [中文](#chinese)

A full-featured AI-powered stock analysis desktop app covering **US / HK / China A-share** markets. Built with Streamlit + LightGBM + CatBoost + XGBoost ensemble learning.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📊 **Technical Analysis** | Candlestick charts, MACD, RSI, Bollinger Bands, ATR, multi-factor buy/sell signals |
| 🤖 **ML Prediction** | 3-model Stacking ensemble (LightGBM + CatBoost + XGBoost) with Ridge meta-learner, confidence intervals and A~F quality rating |
| 📋 **Walk-Forward Backtest** | Rolling window + Sharpe / Sortino / Calmar ratios, win rate, profit factor, max drawdown |
| 📰 **Sentiment Analysis** | Yahoo Finance news scraping + VADER sentiment scoring |
| 🛡️ **Risk Management** | Anomaly detection, position sizing, dynamic stop-loss/take-profit, circuit breaker |
| 📈 **Multi-Stock Compare** | Normalized trend overlay, cross-market (US/HK/CN) comparison |
| 🔥 **Sector Heatmap** | US 11 sectors TreeMap with real-time performance coloring |
| 💰 **Portfolio Tracker** | SQLite-backed position management with real-time P&L |
| 🔔 **Price Alerts** + ⭐ **Watchlist** | Break above/below target price notifications + persistent watchlist |
| 🏛️ **Macro Indicators** | FRED API: Fed Funds Rate, CPI, VIX, 10Y Yield (optional) |
| 🔄 **Auto Refresh** + 🎨 **Dark/Light Theme** | Configurable intervals + one-click theme toggle |
| 📡 **Shard Loader** | Monthly data sharding with timeout skip for long periods |
| 📦 **Windows EXE** | One-click PyInstaller packaging (~8 MB launcher) |

---

## 🚀 Quick Start

`ash
git clone https://github.com/Leoleo66123/stock-analyzer.git
cd stock-analyzer
pip install -r requirements.txt
streamlit run app.py --server.port 8501
`

Open **http://localhost:8501** in your browser.

---

## 📦 Build Windows EXE

`ash
pip install pyinstaller
pyinstaller launcher.spec --clean --noconfirm
Copy-Item app.py,modules,portfolio.db -Destination dist\ -Recurse -Force
`

Output: dist\StockAnalyzer.exe

---

## 🏗️ Project Structure

`
stock-analyzer/
├── app.py                  # Streamlit main app
├── modules/
│   ├── predictor.py        # ML ensemble: LGBM + CatBoost + XGBoost
│   ├── backtest.py         # Walk-forward backtest engine
│   ├── indicators.py       # Technical indicators (MACD, RSI, BB, ATR)
│   ├── data_fetcher.py     # Yahoo Finance + AkShare data fetching
│   ├── sentiment.py        # VADER news sentiment analysis
│   ├── risk_manager.py     # Position sizing + stop-loss + circuit breaker
│   ├── anomaly_detector.py # Z-score anomaly + volume spike detection
│   ├── market_regime.py    # Bull/bear/sideways regime
│   ├── shard_loader.py     # Monthly shard loading with timeout
│   ├── portfolio.py        # SQLite portfolio CRUD
│   ├── visualizer.py       # Plotly chart builders
│   ├── a_share.py          # China A-share (AkShare) integration
│   └── macro.py            # FRED macroeconomic data
├── run.py                  # PyInstaller launcher entry
├── worker.py               # Streamlit subprocess worker
├── launcher.spec           # PyInstaller spec
├── build.bat               # One-click build script
├── requirements.txt        # Python dependencies
└── portfolio.db            # SQLite portfolio database
`

---

## 🔧 Dependencies

- **Python** 3.10+
- **Streamlit** 1.57+ — Web UI
- **LightGBM / CatBoost / XGBoost** — Gradient boosting ensemble
- **scikit-learn** — Ridge meta-learner, preprocessing
- **yfinance** — US/HK stock data
- **akshare** — China A-share data
- **plotly** — Interactive charts
- **pandas / numpy / scipy** — Data processing

---

## 📄 License

MIT © [Leoleo66123](https://github.com/Leoleo66123)

---

<a name="chinese"></a>
# 中文

## 📈 股票智能分析系统

基于 **Streamlit + LightGBM + CatBoost + XGBoost** 集成学习的全功能 AI 量化分析桌面软件，覆盖**美股 / 港股 / A股**三大市场。

### 功能一览

- 📊 **技术分析**：K线图 + MACD/RSI/布林带 + 多因子买卖信号
- 🤖 **机器学习预测**：三模型 Stacking 集成，含置信区间和 A~F 模型评级
- 📋 **样本外回测**：滚动窗口 + 夏普/Sortino/Calmar/胜率/盈亏比/最大回撤
- 📰 **新闻情感分析**：VADER 情感评分 + 市场情绪判定
- 🛡️ **风控系统**：异常检测 + 仓位管理 + 动态止盈止损 + 熔断
- 📈 **多股对比**：归一化走势叠加，跨市场混合对比
- 🔥 **板块热力图**：美股 11 大板块 TreeMap
- 💰 **持仓管理**：SQLite 持久化 + 实时盈亏
- 🔔 **价格预警** + ⭐ **自选股**
- 🔄 **自动刷新** + 🎨 **暗色/亮色主题**
- 📦 **一键打包 EXE**：pyinstaller launcher.spec
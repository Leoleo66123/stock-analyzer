# 股票智能分析系统 v6 - 全功能中文版
import streamlit as st, pandas as pd, numpy as np, plotly.graph_objects as go
from datetime import datetime
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
from data_fetcher import *; from indicators import *; from predictor import *
from sentiment import *; from backtest import *; from visualizer import *
from portfolio import *; from anomaly_detector import *; from risk_manager import *
from market_regime import *; from a_share import *; from macro import *
from shard_loader import *
# Clear stale caches
st.set_page_config(page_title="股票智能分析系统", page_icon="📈", layout="wide")

D = {"sym":"AAPL","period":"1mo","show_ml":True,"show_bt":True,"auto_refresh":False,"refresh_sec":60,"theme":"dark"}
for k,v in D.items():
    if k not in st.session_state: st.session_state[k] = v

def parse_symbol(s):
    s = s.strip().upper()
    if not s: return ""
    if s.endswith(".HK"): return f"{(s[:-3].lstrip('0') or '0').zfill(4)}.HK"
    if s.isdigit() and len(s) <= 5: return f"{(s.lstrip('0') or '0').zfill(4)}.HK"
    return s

def load_data(sym, per, use_shard=True):
    """Load data with shard support for long periods."""
    if sym.endswith(('.SH','.SZ','.BJ')): return fetch_a_share_data(sym, per)
    months = {'1mo':1,'3mo':3,'6mo':6,'1y':12,'2y':24,'5y':60}.get(per, 6)
    if months > 1 and use_shard:
        from shard_loader import load_sharded
        result = load_sharded(sym, per)
        return result['df']
    return fetch_stock_data(sym, period=per)

theme = st.session_state.theme
bg = "#13161a" if theme == "dark" else "#ffffff"
card = "#1a1e24" if theme == "dark" else "#f5f5f5"
tx = "#e8eaed" if theme == "dark" else "#1a1a1a"
sub = "#8b8f96" if theme == "dark" else "#666666"
tpl = "plotly_dark" if theme == "dark" else "plotly_white"
c1 = "#e15241"; c2 = "#26a69a"; c3 = "#4e8cff"; c4 = "#ffa726"; c5 = "#ab47bc"

CSS = "<style>*{font-family:-apple-system,Segoe_UI,Microsoft_YaHei,sans-serif;}.stApp{background:"+bg+";}.top-bar{display:flex;align-items:center;justify-content:space-between;padding:8px_16px;background:"+card+";border-bottom:1px_solid_#2a2e35;margin:-4rem_-4rem_1rem_-4rem;}.top-bar_.t{font-size:18px;font-weight:700;color:"+tx+";}.top-bar_.s{font-size:12px;color:"+sub+";}[data-testid=stSidebar]{background:"+card+";border-right:1px_solid_#2a2e35;}[data-testid=stSidebar]_*{color:#b0b4bb!important;}.stButton>button{background:#252a33;color:#b0b4bb;border:1px_solid_#3a3e45;border-radius:4px;font-size:13px;padding:4px_12px;}.stButton>button:hover{background:#30363d;}.stTextInput_input{background:"+card+"!important;color:"+tx+"!important;border:1px_solid_#3a3e45!important;}#MainMenu,footer,header{visibility:hidden;}[data-testid=stToolbar]{display:none;}</style>".replace("_"," ")
st.markdown(CSS, unsafe_allow_html=True)

now = datetime.now().strftime("%Y-%m-%d %H:%M")
H = "<div class=top-bar><div><span class=t>股票智能分析系统 v6</span><span class=s> | 全功能中文版</span></div><div class=s>"+now+"</div></div>"
st.markdown(H, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔍 搜索股票")
    raw = st.text_input("股票代码", key="si_input", placeholder="AAPL / 0700.HK / 600519.SH")
    if raw:
        raw = raw.strip().upper()
        ps = parse_symbol(raw)
        if ps and ps != st.session_state.get("sym", ""):
            st.session_state.sym = ps
            st.rerun()
    sym = st.session_state.get("sym", "AAPL")
    st.caption(f"当前: {sym}")

    with st.expander("📋 快速选择"):
        popular = get_popular_stocks()
        all_s = popular + A_SHARE_POPULAR
        opts = {f'{s["name"]} ({s["symbol"]})': s["symbol"] for s in all_s}
        sel = st.selectbox("选择股票", list(opts.keys()), key="qp_select_v2")
        if sel in opts and opts[sel] != sym:
            st.session_state.sym = opts[sel]
            st.rerun()
    st.divider()
    tabs = ["个股分析","多股对比","持仓管理","板块热力","宏观经济","系统设置"]
    tab = st.radio("导航", tabs, index=0, label_visibility="collapsed", key="nav_tabs_v2")
    if tab == "系统设置":
        pmap = {"1月":"1mo","3月":"3mo","6月":"6mo","1年":"1y","2年":"2y","5年":"5y"}
        st.session_state.period = pmap[st.selectbox("数据周期", list(pmap.keys()), index=0)]
        st.session_state.show_ml = st.checkbox("机器学习预测", True)
        st.session_state.show_bt = st.checkbox("历史回测", True)
        st.divider()
        auto = st.checkbox("自动刷新", False)
        if auto:
            ri = st.selectbox("刷新间隔", ["10秒","30秒","1分钟","2分钟"], index=2)
            st.session_state.auto_refresh = True
            st.session_state.refresh_sec = {"10秒":10,"30秒":30,"1分钟":60,"2分钟":120}[ri]
        else: st.session_state.auto_refresh = False
        st.divider()
        if st.button("切换亮色/暗色"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    else:
        if "period" not in st.session_state: st.session_state.period = "1mo"
    period = st.session_state.get("period", "6mo")
    show_ml = st.session_state.get("show_ml", True)
    show_bt = st.session_state.get("show_bt", True)
    sym = st.session_state.sym
    st.divider(); st.markdown("**自选股**")
    if st.button("+ 添加自选", key="wa"): add_watchlist(sym, ""); st.rerun()
    wl = get_watchlist()
    if wl is not None and not wl.empty:
        for _, r in wl.head(10).iterrows():
            c1b, c2b = st.columns([5, 1])
            if c1b.button(r["symbol"], key=f"w_{r['symbol']}"):
                st.session_state.sym = r["symbol"]; st.rerun()
            if c2b.button("X", key=f"d_{r['symbol']}"):
                remove_watchlist(r["symbol"]); st.rerun()

if tab == "个股分析":
    # Phase 1: Fast - load data + indicators
    # Phase 1: Sharded loading with progress + cancel
    months = {"1mo":1,"3mo":3,"6mo":6,"1y":12,"2y":24,"5y":60}.get(period, 1)
    use_shard = months > 1
    if "load_cancelled" not in st.session_state:
        st.session_state.load_cancelled = False
    if use_shard:
        st.markdown(f"📡 分片加载中({months}个月度分片)...  ")
        prog_bar = st.progress(0)
        status_text = st.empty()
        cancel_col, _ = st.columns([1, 3])
        if cancel_col.button("⏹ 取消加载", key="cancel_load"):
            st.session_state.load_cancelled = True
        
        def prog_callback(completed, total, label, status):
            pct = completed / total if total > 0 else 0
            prog_bar.progress(pct)
            status_text.caption(f"分片 {completed}/{total}: {label} — {status}")
        def cancel_check():
            return st.session_state.get("load_cancelled", False)
        
        from shard_loader import load_sharded
        result = load_sharded(sym, period, on_progress=prog_callback, on_cancel=cancel_check)
        df = result["df"]
        if result["cancelled"]:
            st.warning(f"⏹ 加载已取消。已获取 {len(df)} 行数据，缺失 {len(result['missing_shards'])} 个月度分片")
            st.session_state.load_cancelled = False
        elif result["missing_shards"]:
            st.info(f"⚠️ 部分数据缺失: {result['missing_shards']}，已获取 {len(df)} 行")
        else:
            st.success(f"✅ 加载完成: {len(df)} 行，{result['completed_shards']}/{result['total_shards']} 分片")
        status_text.empty()
    else:
        with st.spinner("正在加载数据..."):
            df = load_data(sym, period, use_shard=False)
    if df is None or df.empty:
        st.error(f"无法获取 {sym} 数据"); st.stop()
    df = calculate_all_indicators(df)

    # Phase 2: Basic info - instant
    info = get_stock_info(sym) if not sym.endswith((".SH",".SZ",".BJ")) else {"name":sym,"sector":"A股","pe_ratio":None,"current_price":df["Close"].iloc[-1],"market_cap":None,"currency":"CNY"}
    signals_df = generate_signals(df)
    trend = analyze_trend(df)
    for ta in check_alerts(sym, df["Close"].iloc[-1]): st.warning(ta)
    price = info.get("current_price") or df["Close"].iloc[-1]
    prev = df["Close"].iloc[-2] if len(df) > 1 else price
    chg = price - prev; chg_pct = (chg/prev)*100
    cur = "HK$" if sym.endswith(".HK") else ("¥" if sym.endswith((".SH",".SZ",".BJ")) else "$")
    is_up = chg >= 0; CC = c1 if is_up else c2
    name = info.get("name", sym)
    sector = info.get("sector", "无")
    st.markdown(f"<div style=display:flex;gap:16px;padding:12px_0_16px_0;><div style=flex:2><div style=font-size:22px;font-weight:700;color:{tx};>{name}</div><div style=font-size:13px;color:#6b6f76;>{sym} / {sector}</div></div><div style=flex:1;text-align:right;><div style=font-size:28px;font-weight:700;color:{CC};>{cur}{price:.2f}</div><div style=font-size:14px;color:{CC};>{chg:+.2f} ({chg_pct:+.2f}%)</div></div></div>".replace("_"," "), unsafe_allow_html=True)
    c = st.columns(6)
    c[0].metric("开盘", f"{df['Open'].iloc[-1]:.2f}")
    c[1].metric("最高", f"{df['High'].iloc[-1]:.2f}")
    c[2].metric("最低", f"{df['Low'].iloc[-1]:.2f}")
    c[3].metric("成交量", f"{df['Volume'].iloc[-1]/1e6:.1f}M")
    mc = info.get("market_cap",0)
    c[4].metric("市值", f"{mc/1e9:.1f}B" if mc else "无")
    c[5].metric("市盈率", f"{info.get('pe_ratio'):.1f}" if info.get("pe_ratio") else "无")
    sig = signals_df["signal"].iloc[-1]
    label = "买入" if sig=="BUY" else ("卖出" if sig=="SELL" else "持有")
    rsi_val = df["RSI"].iloc[-1]
    SC = c1 if sig=="SELL" else (c2 if sig=="BUY" else c4)
    sig_score = signals_df["score"].iloc[-1] if "score" in signals_df.columns else 0
    trend_label = trend.get("trend","未知")
    st.markdown(f"<div style=display:flex;gap:20px;padding:8px_0;align-items:center;><span style=font-size:18px;font-weight:600;color:{SC};>{label}</span><span style=font-size:14px;color:{sub};>评分:{sig_score} 趋势:{trend_label} RSI:{rsi_val:.1f} ATR:{df['ATR'].iloc[-1]:.2f}</span></div>".replace("_"," "), unsafe_allow_html=True)

    # Phase 3: Charts - fast
    st.markdown("---")
    st.markdown("### 📊 技术分析图表")
    col_l, col_r = st.columns([3, 2])
    with col_l:
        fig_k = create_candlestick_chart(df, signals_df)
        st.plotly_chart(fig_k, use_container_width=True, key="kline")
    with col_r:
        fig_m = create_macd_chart(df)
        st.plotly_chart(fig_m, use_container_width=True, key="macd")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI(14)", line=dict(color=c3,width=1.5)))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color=c1, annotation_text="超买 70")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color=c2, annotation_text="超卖 30")
    fig_rsi.update_layout(height=200, margin=dict(l=0,r=0,t=20,b=0), template=tpl, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_rsi, use_container_width=True, key="rsi")

    # Phase 4: ML Prediction - independent spinner
    if show_ml:
        st.markdown("---")
        st.markdown("### 🤖 机器学习预测")
        with st.spinner("模型训练中(约5-10秒)..."):
            try:
                pred = predict_future(df, sym)
            except Exception as e:
                pred = {"error": str(e)}
        if "error" not in pred:
            pcol1, pcol2 = st.columns([1, 1])
            with pcol1:
                fig_pred = create_prediction_chart(pred)
                st.plotly_chart(fig_pred, use_container_width=True, key="pred_chart")
            with pcol2:
                rating = pred.get("grade","C")
                rmap = {"A":"🟢优秀","B":"🟢良好","C":"🟡一般","D":"🟠较差","E":"🔴差","F":"🔴极差"}
                rlabel = rmap.get(rating, rating)
                prob_up = pred.get("prob_up", 50)
                prob_down = pred.get("prob_down", 50)
                fc = pred.get("forecast", [price]*5)
                fc_lo = pred.get("forecast_lower", [price]*5)
                fc_hi = pred.get("forecast_upper", [price]*5)
                pred_price = fc[-1]
                ci_low = fc_lo[-1]
                ci_high = fc_hi[-1]
                exp_return = (pred_price/price - 1)*100
                fc_summary = pred.get("forecast_summary","")
                st.metric("模型评级", rlabel)
                st.metric("预测方向", fc_summary)
                st.metric("预测价格", f"{cur}{pred_price:.2f}", delta=f"{exp_return:+.2f}%")
                st.metric("上涨概率", f"{prob_up:.1f}%")
                st.metric("下跌概率", f"{prob_down:.1f}%")
                st.metric("95%置信区间", f"{cur}{ci_low:.2f} ~ {cur}{ci_high:.2f}")
                st.caption(f"R²={pred.get('ensemble_r2',0):.3f} | 方向准确率={pred.get('ensemble_dir_acc',0):.1f}%")
            try:
                fi = get_feature_importance(df)
                if fi is not None and not fi.empty:
                    st.markdown("**特征重要性 Top 15**")
                    fig_fi = create_feature_importance_chart(fi.head(15))
                    st.plotly_chart(fig_fi, use_container_width=True, key="fi_chart")
            except: pass
        else:
            st.info(f"预测: {pred.get('error','数据不足')}")

    # Phase 5: Backtest - independent spinner
    if show_bt:
        st.markdown("---")
        st.markdown("### 📋 样本外回测")
        with st.spinner("回测计算中..."):
            try:
                trades = walk_forward_backtest(df)
                summary = generate_backtest_summary(trades)
            except Exception as e:
                summary = {"error": str(e)}
        if "error" not in summary:
            btcol1, btcol2, btcol3, btcol4, btcol5 = st.columns(5)
            btcol1.metric("夏普比率", f"{summary.get('sharpe_ratio',0):.2f}")
            btcol2.metric("Sortino", f"{summary.get('sortino_ratio',0):.2f}")
            btcol3.metric("Calmar", f"{summary.get('calmar_ratio',0):.2f}")
            btcol4.metric("胜率", f"{summary.get('win_rate',0):.1f}%")
            btcol5.metric("最大回撤", f"{summary.get('max_drawdown',0):.1f}%")
            btcol6, btcol7, btcol8, btcol9, btcol10 = st.columns(5)
            btcol6.metric("盈亏比", f"{summary.get('profit_factor',0):.2f}")
            btcol7.metric("总收益", f"{summary.get('total_return',0):.1f}%")
            btcol8.metric("交易次数", str(summary.get("trade_count",0)))
            btcol9.metric("最大连赢", str(summary.get("max_consecutive_wins",0)))
            btcol10.metric("最大连亏", str(summary.get("max_consecutive_losses",0)))
            star = summary.get("star_rating",0)
            stars = "⭐" * int(star)
            st.caption(f"回测评级: {stars} ({star}/5)")
# V5: rb = summary.get("regime_breakdown", {})
# V5: if rb:
# V5: with st.expander("📊 分场景回测详情"):
# V5: regime_labels = {"bull":"牛市","bear":"熊市","sideways":"震荡","high_vol":"高波动"}
# V5: for r, s in rb.items():
# V5: label = regime_labels.get(r, r)
# V5: st.caption(f"{label}: {s.get("trades",0)}笔 | 胜率{s.get("win_rate",0)}% | 盈亏{s.get("total_pnl",0):+.0f}")
# V5: st_test = summary.get("stress_test", {})
# V5: if st_test:
# V5: with st.expander("⚠️ 黑天鹅压力测试"):
# V5: st.caption(f"20%暴跌: ${st_test.get("crash_20pct",0):,.0f} | 回本需{st_test.get("recovery_trades_20","?")}笔")
# V5: st.caption(f"30%暴跌: ${st_test.get("crash_30pct",0):,.0f}")
# V5: st.caption(f"50%暴跌: ${st_test.get("crash_50pct",0):,.0f}")
            ec = summary.get("equity_curve")
            if ec is not None:
                fig_eq = create_equity_curve_chart(ec)
                st.plotly_chart(fig_eq, use_container_width=True, key="eq_chart")
        else:
            st.info(f"回测: {summary.get('error','无交易')}")

    # Phase 6: Sentiment - independent spinner
    st.markdown("---")
    st.markdown("### 📰 新闻情感分析")
    with st.spinner("抓取新闻中..."):
        try:
            sentiment = fetch_news_sentiment(sym)
        except Exception as e:
            sentiment = {"error": str(e)}
    if "error" not in sentiment:
        mood = sentiment.get("mood","中性")
        avg_s = sentiment.get("avg_sentiment",0)
        pos_pct = sentiment.get("positive_pct",0)
        neg_pct = sentiment.get("negative_pct",0)
        neu_pct = sentiment.get("neutral_pct",0)
        mood_color = c2 if mood == "积极" else (c1 if mood == "消极" else c4)
        st.markdown(f"<div style=display:flex;gap:16px;padding:8px_0;><span style=font-size:16px;font-weight:600;color:{mood_color};>市场情绪: {mood}</span><span style=color:{sub};>平均情感分: {avg_s:.3f} | 积极 {pos_pct}% | 消极 {neg_pct}% | 中性 {neu_pct}%</span></div>".replace("_"," "), unsafe_allow_html=True)
        articles = sentiment.get("articles",[])
        if articles:
            with st.expander(f"新闻列表 ({len(articles)}条)"):
                for a in articles[:20]:
                    emoji = "😊" if a.get("sentiment","中性") == "积极" else ("😟" if a.get("sentiment","中性") == "消极" else "😐")
                    st.markdown(f"{emoji} **{a.get('title','')}** — {a.get('source','')} ({a.get('date','')})")
    else:
        st.info(f"情感分析: {sentiment.get('error','无新闻')}")

    # Phase 7: Risk & Regime - fast
    st.markdown("---")
    st.markdown("### 🛡️ 风控与市场环境")
    adcol1, adcol2 = st.columns(2)
    with adcol1:
        try:
            anomaly = detect_anomalies(df)
            st.markdown(f"**异常检测**: {anomaly.get('status_text','正常')}")
            alerts = anomaly.get("alerts",[])
            if alerts:
                for a in alerts: st.warning(a)
            st.caption(f"信号权重: {anomaly.get('signal_weight',1.0)}")
        except Exception as e:
            st.info("异常检测暂不可用")
    with adcol2:
        try:
            regime = detect_market_regime(df)
            st.markdown(f"**市场环境**: {regime.get('label','未知')}")
            st.markdown(f"**策略建议**: {regime.get('strategy','持有')}")
        except Exception as e:
            st.info("市场环境检测暂不可用")

elif tab == "多股对比":
    st.markdown("### 📈 多股对比")
    compare_symbols = st.text_input("输入股票代码（逗号分隔）", placeholder="AAPL, MSFT, 0700.HK, 600519.SH", key="comp_input")
    if compare_symbols:
        symbols = [s.strip() for s in compare_symbols.split(",") if s.strip()]
        if symbols:
            with st.spinner("加载对比数据..."):
                comp_data = {}
                for s in symbols:
                    ps = parse_symbol(s)
                    d = load_data(ps, "3mo")
                    if d is not None and not d.empty:
                        comp_data[ps] = d["Close"] / d["Close"].iloc[0] * 100
            if comp_data:
                fig_comp = go.Figure()
                for s, series in comp_data.items():
                    fig_comp.add_trace(go.Scatter(x=series.index, y=series.values, name=s, mode="lines"))
                fig_comp.update_layout(height=400, template=tpl, title="归一化走势对比 (基期=100)",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_comp, use_container_width=True, key="comp_chart")
                perf = []
                for s in symbols:
                    ps = parse_symbol(s)
                    if ps in comp_data:
                        chg_val = ((comp_data[ps].iloc[-1]/100)-1)*100
                        perf.append({"股票": ps, "期间收益%": round(chg_val,2)})
                if perf:
                    st.dataframe(pd.DataFrame(perf), use_container_width=True)
            else:
                st.warning("无法加载对比数据")

elif tab == "持仓管理":
    st.markdown("### 💰 持仓管理")
    with st.form("add_position"):
        c1f, c2f, c3f, c4f = st.columns(4)
        psym = c1f.text_input("代码", value=sym)
        pqty = c2f.number_input("数量", min_value=1, value=100)
        pprice = c3f.number_input("买入价", min_value=0.01, value=100.0, format="%.2f")
        pdate = c4f.date_input("日期", value=datetime.now())
        if st.form_submit_button("添加持仓"):
            add_holding(sym, sym, psym, pqty, pprice, str(pdate)); st.rerun()
    positions = get_holdings()
    if positions is not None and not positions.empty:
        total_cost = (positions["buy_price"]*positions["quantity"]).sum()
        st.markdown(f"**总成本**: ${total_cost:,.2f}")
        st.dataframe(positions, use_container_width=True)

elif tab == "板块热力":
    st.markdown("### 🔥 板块热力图")
    with st.spinner("加载板块数据..."):
        heatmap = get_sector_performance()
    if heatmap is not None and not heatmap.empty:
        import plotly.express as px
        fig_hm = px.treemap(heatmap, path=["sector"], values=[1]*len(heatmap), color="change_pct",
            color_continuous_scale=["#e15241","#333333","#26a69a"], range_color=[-5,5])
        fig_hm.update_layout(height=450, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig_hm, use_container_width=True, key="heatmap")
    else:
        st.info("板块数据暂不可用")

elif tab == "宏观经济":
    st.markdown("### 🏛️ 宏观经济指标")
    with st.spinner("获取宏观数据..."):
        macro_data = fetch_macro_data()
    if "error" not in macro_data:
        mcols = st.columns(len(macro_data))
        for i, (name, info) in enumerate(macro_data.items()):
            mcols[i].metric(name, str(info.get("latest","无")))
    else:
        st.info("宏观数据不可用（需要 FRED API Key）")

# 自动刷新
if st.session_state.get("auto_refresh"):
    time.sleep(st.session_state.get("refresh_sec", 60))
    st.rerun()

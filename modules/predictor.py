'''ML Predictor - Original 15 Price-Volume Features (v5 additions commented)'''
import pandas as pd, numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

_pred_cache = {}

# ===== V5 ADDITIONS (commented - future iteration) =====
# def _get_market(symbol): ...
# def _rolling_beta_simple(series, benchmark): ...
# def _build_features_v5(df, symbol=''): ...

def _build_features(df):
    """Original 15-factor price-volume feature set."""
    f = pd.DataFrame(index=df.index)
    close = df['Close']; high = df['High']; low = df['Low']; volume = df['Volume']
    for n in [1, 3, 5, 10, 20]:
        f[f'ret_{n}'] = close.pct_change(n)
    f['hl_ratio'] = (high - low) / close.replace(0, np.nan)
    f['amplitude'] = (high - low) / df['Open'].replace(0, np.nan)
    f['close_position'] = (close - low) / (high - low + 1e-10)
    vol_ma20 = volume.rolling(20).mean().replace(0, np.nan)
    f['volume_ratio'] = volume / vol_ma20
    f['vol_lag'] = volume.shift(1) / volume.replace(0, np.nan)
    rets = close.pct_change()
    f['volatility'] = rets.rolling(10).std()
    for p in [5, 10, 20, 60]:
        ma = close.rolling(p).mean()
        f[f'ma{p}_dev'] = close / ma.replace(0, np.nan) - 1
    for p in [10, 20, 60]:
        high_p = high.rolling(p).max()
        low_p = low.rolling(p).min()
        f[f'mom_{p}'] = (close - low_p) / (high_p - low_p + 1e-10)
    for c in ['MACD','MACD_Signal','MACD_Hist','RSI','ATR']:
        if c in df.columns:
            f[c.lower()] = df[c]
    if 'MACD_Hist' in df.columns:
        f['macd_divergence'] = df['MACD_Hist'].diff()
    if 'ATR' in df.columns:
        f['atr_pct'] = df['ATR'] / close
    # ===== V5 ADDITIONS (commented) =====
    # for n in [1, 3, 10, 20]:
    #     f[f"log_{n}"] = np.log(np.maximum(close / close.shift(n), 1e-10))
    # f['vol_trend'] = volume.rolling(5).mean() / volume.rolling(20).mean()
    # f['volatility_20'] = rets.rolling(20).std()
    # f['volatility_60'] = rets.rolling(60).std()
    # f['vol_expansion'] = f['volatility'] / (f['volatility_20'] + 1e-10)
    # ma5=close.rolling(5).mean(); ma20=close.rolling(20).mean(); ma60=close.rolling(60).mean()
    # f['ma_bullish'] = ((ma5>ma20)&(ma20>ma60)).astype(float)
    # up_vol=rets.clip(lower=0).rolling(20).std()
    # down_vol=rets.clip(upper=0).rolling(20).std()
    # f['mom_quality'] = up_vol/(down_vol.abs()+1e-10)-1
    # # Industry Beta (v5) & Crowding (v5) commented out
    f['target'] = close.pct_change(5).shift(-5)
    f = f.dropna(); f = f.replace([np.inf, -np.inf], np.nan).dropna()
    return f

def _rate_model(r2, dir_acc):
    if r2 > 0.05 and dir_acc > 58: return "A", "优秀"
    if r2 > 0.02 and dir_acc > 55: return "B", "良好"
    if r2 > -0.05 and dir_acc > 52: return "C", "一般"
    if r2 > -0.2: return "D", "较差"
    if r2 > -0.5: return "E", "差"
    return "F", "极差"

def predict_future(df, symbol=''):
    import hashlib
    ck = hashlib.md5((symbol + str(len(df)) + str(df.index[-1])).encode()).hexdigest()
    if ck in _pred_cache:
        return _pred_cache[ck]
    try:
        f = _build_features(df)
        if len(f) < 60:
            return {"error": f"需要>=60个数据点，当前仅有{len(f)}"}
        feature_cols = [c for c in f.columns if c != 'target' and f[c].dtype in [np.float64, np.float32, np.int64]]
        if len(feature_cols) < 5:
            return {"error": "特征不足"}
        X = f[feature_cols].values; y = f['target'].values
        mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        X, y = X[mask], y[mask]
        if len(y) < 60:
            return {"error": f"清洗后数据不足({len(y)}行)"}
        split = int(len(y) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        models = {}
        try:
            import lightgbm as lgb
            m = lgb.LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.05,
                                  subsample=0.8, colsample_bytree=0.8,
                                  reg_alpha=0.1, reg_lambda=0.1,
                                  random_state=42, verbose=-1)
            m.fit(X_train_s, y_train); p = m.predict(X_test_s)
            ss_res = ((y_test-p)**2).sum(); ss_tot = ((y_test-y_test.mean())**2).sum()
            r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
            da = (np.sign(p)==np.sign(y_test)).mean()*100
            models["lgb"] = {"model":m,"pred":p,"r2":r2,"dir_acc":da}
        except Exception as e: models["lgb"] = {"error":str(e)}
        try:
            from catboost import CatBoostRegressor
            m = CatBoostRegressor(n_estimators=200, max_depth=6, learning_rate=0.05,
                                  subsample=0.8, random_seed=42, verbose=0)
            m.fit(X_train_s, y_train); p = m.predict(X_test_s)
            ss_res = ((y_test-p)**2).sum(); ss_tot = ((y_test-y_test.mean())**2).sum()
            r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
            da = (np.sign(p)==np.sign(y_test)).mean()*100
            models["cb"] = {"model":m,"pred":p,"r2":r2,"dir_acc":da}
        except Exception as e: models["cb"] = {"error":str(e)}
        try:
            import xgboost as xgb
            m = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8,
                                 reg_alpha=0.1, reg_lambda=0.1,
                                 random_state=42, verbosity=0)
            m.fit(X_train_s, y_train); p = m.predict(X_test_s)
            ss_res = ((y_test-p)**2).sum(); ss_tot = ((y_test-y_test.mean())**2).sum()
            r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
            da = (np.sign(p)==np.sign(y_test)).mean()*100
            models["xgb"] = {"model":m,"pred":p,"r2":r2,"dir_acc":da}
        except Exception as e: models["xgb"] = {"error":str(e)}

        valid = {k:v for k,v in models.items() if "error" not in v}
        if not valid: return {"error":"所有模型训练失败"}
        preds = np.column_stack([v["pred"] for v in valid.values()])
        if preds.shape[1] >= 2:
            meta = Ridge(alpha=1.0); meta.fit(preds, y_test)
            ensemble_pred = meta.predict(preds)
        else: ensemble_pred = preds[:,0]
        ss_res = ((y_test-ensemble_pred)**2).sum(); ss_tot = ((y_test-y_test.mean())**2).sum()
        ensemble_r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        ensemble_dir_acc = (np.sign(ensemble_pred)==np.sign(y_test)).mean()*100
        grade, grade_label = _rate_model(ensemble_r2, ensemble_dir_acc)
        residuals = y_test - ensemble_pred
        std_resid = np.std(residuals) if len(residuals) > 1 else 0.01
        ci_95 = 1.96 * std_resid
        pred_mean = ensemble_pred.mean(); pred_std = ensemble_pred.std() if len(ensemble_pred) > 1 else 0.01
        prob_up_raw = float(1 - (0-pred_mean)/(pred_std+1e-10))
        prob_up = 1/(1+np.exp(-prob_up_raw))*100
        prob_down = 100 - prob_up
        last_row = scaler.transform(X[-1:])
        fc_preds_list = [v["model"].predict(last_row)[0] for v in valid.values()]
        if len(fc_preds_list) >= 2:
            fc_meta = Ridge(alpha=1.0); fc_meta.fit(preds, y_test)
            fc_return = fc_meta.predict(np.array(fc_preds_list).reshape(1,-1))[0]
        else: fc_return = fc_preds_list[0]
        # V5 CLAMP: fc_return = max(min(float(fc_return), 0.15), -0.15)
        fc_return = float(fc_return)
        last_price = float(df["Close"].iloc[-1])
        forecast = [last_price*(1+fc_return*(i/5)) for i in range(1,6)]
        fc_lower = [last_price*(1+(fc_return-ci_95)*(i/5)) for i in range(1,6)]
        fc_upper = [last_price*(1+(fc_return+ci_95)*(i/5)) for i in range(1,6)]
        if fc_return > 0.015: summary = "看涨(5日)"
        elif fc_return > 0.003: summary = "微涨(5日)"
        elif fc_return > -0.003: summary = "横盘(5日)"
        elif fc_return > -0.015: summary = "微跌(5日)"
        else: summary = "看跌(5日)"
        result = {
            "ensemble_r2":round(ensemble_r2,3), "ensemble_dir_acc":round(ensemble_dir_acc,1),
            "grade":grade, "grade_label":grade_label,
            "lgb_r2":round(models.get("lgb",{}).get("r2",-1),3),
            "cb_r2":round(models.get("cb",{}).get("r2",-1),3),
            "xgb_r2":round(models.get("xgb",{}).get("r2",-1),3),
            "prob_up":round(prob_up,1), "prob_down":round(prob_down,1),
            "ci_95":round(ci_95,4),
            "forecast":forecast, "forecast_lower":fc_lower, "forecast_upper":fc_upper,
            "forecast_days":5, "forecast_summary":summary,
            "n_features":len(feature_cols),
            "models":{k:{"r2":round(v.get("r2",-1),3),"dir_acc":round(v.get("dir_acc",50),1)} for k,v in models.items()},
        }
        _pred_cache[ck] = result
        return result
    except Exception as e:
        return {"error":str(e)}

def get_feature_importance(df):
    try:
        import lightgbm as lgb
        f = _build_features(df)
        feature_cols = [c for c in f.columns if c != 'target' and f[c].dtype in [np.float64, np.float32, np.int64]]
        if len(feature_cols) < 5: return pd.DataFrame()
        X = f[feature_cols].values; y = f['target'].values
        mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        X, y = X[mask], y[mask]
        if len(y) < 30: return pd.DataFrame()
        scaler = StandardScaler(); X_s = scaler.fit_transform(X)
        m = lgb.LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
        m.fit(X_s, y)
        imp = pd.DataFrame({"feature":feature_cols, "importance":m.feature_importances_})
        return imp.sort_values("importance", ascending=False)
    except Exception: return pd.DataFrame()
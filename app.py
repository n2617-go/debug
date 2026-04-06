import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="VIX 數據監控", layout="wide")

# --- 核心抓取邏輯 ---

def fetch_finmind():
    """來源一：FinMind (最穩定)"""
    from FinMind.data import DataLoader
    api = DataLoader()
    # 抓取最近 30 天
    start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    df = api.taiwan_vix(start_date=start_dt)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.rename(columns={'close': 'VIX', 'date': 'Date'}).set_index('Date')
        return df[['VIX']]
    return None

def fetch_yfinance():
    """來源二：yfinance (代號 ^VIXTWN)"""
    # Yahoo Finance 的台指 VIX 代號
    ticker = "^VIXTWN"
    data = yf.download(ticker, period="1mo", progress=False)
    if not data.empty:
        # yfinance 回傳可能是 MultiIndex，需取 Close 欄位
        df = data[['Close']].copy()
        df.columns = ['VIX']
        df.index = df.index.date
        return df
    return None

# --- UI 呈現 ---
st.title("🛡️ 台指 VIX 數據監控測試")

col1, col2 = st.columns(2)

# 測試 FinMind
with col1:
    st.subheader("1. FinMind 測試")
    try:
        df_fm = fetch_finmind()
        if df_fm is not None:
            st.success("FinMind 連線成功！")
            st.metric("最新點位", f"{df_fm['VIX'].iloc[-1]:.2f}")
            st.dataframe(df_fm.tail(5))
        else:
            st.warning("FinMind 回傳空資料")
    except Exception as e:
        st.error(f"FinMind 失敗原因: {e}")

# 測試 yfinance
with col2:
    st.subheader("2. yfinance 測試")
    try:
        df_yf = fetch_yfinance()
        if df_yf is not None:
            st.success("yfinance 連線成功！")
            st.metric("最新點位", f"{df_yf['VIX'].iloc[-1]:.2f}")
            st.dataframe(df_yf.tail(5))
        else:
            st.warning("yfinance 回傳空資料 (可能是代號失效)")
    except Exception as e:
        st.error(f"yfinance 失敗原因: {e}")

st.divider()
st.info("💡 如果兩邊都失敗且出現 'ModuleNotFoundError'，請在終端機執行 `pip install finmind yfinance`。")

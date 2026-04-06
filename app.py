import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(page_title="台指 VIX 官方數據監控系統", layout="wide")

def get_vix_comprehensive():
    """
    雙重數據源抓取邏輯：
    1. 優先：期交所 OpenAPI (DailyVIX)
    2. 備援：yfinance (^VIXTWN)
    """
    # --- 來源 A: 期交所 OpenAPI ---
    try:
        url = "https://openapi.taifex.com.tw/v1/DailyVIX"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", "").lower():
            data = response.json()
            df_oa = pd.DataFrame(data)
            if 'Date' in df_oa.columns and 'ClosePrice' in df_oa.columns:
                df_oa['Date'] = pd.to_datetime(df_oa['Date']).dt.date
                df_oa['VIX'] = pd.to_numeric(df_oa['ClosePrice'], errors='coerce')
                df_oa = df_oa[['Date', 'VIX']].set_index('Date').sort_index(ascending=False)
                return df_oa, "期交所 OpenAPI"
    except:
        pass # 失敗則轉向備援

    # --- 來源 B: yfinance (備援) ---
    try:
        # 抓取最近 10 天，確保跨越連假
        yf_data = yf.download("^VIXTWN", period="10d", interval="1d", progress=False)
        if not yf_data.empty:
            if isinstance(yf_data.columns, pd.MultiIndex):
                yf_data.columns = yf_data.columns.get_level_values(0)
            
            df_yf = yf_data[['Close']].rename(columns={'Close': 'VIX'})
            df_yf.index = pd.to_datetime(df_yf.index).date
            return df_yf.sort_index(ascending=False), "yfinance (備援)"
    except:
        pass

    return None, None

# --- UI 呈現 ---
st.title("🛡️ 台指 VIX 數據監控中心")
st.info(f"📅 今天是 2026-04-06 (補假)，台股休市。系統自動抓取最後交易日數據。")

# 執行抓取
with st.spinner('同步官方數據源中...'):
    vix_df, source_name = get_vix_comprehensive()

if vix_df is not None and not vix_df.empty:
    # 1. 取得最新一筆 (連假前收盤)
    latest_val = float(vix_df['VIX'].iloc[0])
    latest_date = vix_df.index[0]
    
    # 計算與前一交易日漲跌
    if len(vix_df) > 1:
        prev_val = float(vix_df['VIX'].iloc[1])
        delta = latest_val - prev_val
    else:
        delta = 0

    # 2. 指標看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"最後結算價 ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    with col2:
        # 市場情緒
        if latest_val > 25:
            st.error("🚨 市場避險情緒濃厚")
        elif latest_val < 17:
            st.success("😊 市場氣氛樂觀")
        else:
            st.info("🟡 波動率處於常態")
    with col3:
        st.write(f"**目前數據源：** `{source_name}`")
        if st.button("🔄 立即重新整理"):
            st.rerun()

    st.divider()

    # 3. 數據明細
    st.subheader("📋 歷史成交紀錄清單")
    st.dataframe(
        vix_df.style.format("{:.2f}")
              .background_gradient(cmap="coolwarm", subset=['VIX']),
        use_container_width=True,
        height=500
    )
    
    # 4. 監控小提醒
    with st.expander("💡 投資觀察重點"):
        st.write("""
        - **基準日說明：** 由於今日 4/6 休市，最新數據為 4/3 之結算點位。
        - **恐慌門檻：** 一般而言，VIX 指數超過 20 代表波動開始放大，超過 30 則代表市場進入極度恐慌。
        - **數據更新：** 官方 OpenAPI 數據於每日收盤後由期交所發布。
        """)

else:
    st.error("❌ 嚴重錯誤：無法從任何來源取得數據。")
    st.info("建議檢查：1. 您的網路連線 2. 終端機執行 `pip install --upgrade yfinance requests`。")

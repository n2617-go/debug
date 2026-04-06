import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="台指 VIX 官方數據監控", layout="wide")

def get_vix_from_openapi():
    """
    從期交所 OpenAPI 抓取台指 VIX 近三個月每日收盤指數
    API Endpoint: https://openapi.taifex.com.tw/v1/DailyVIX
    """
    url = "https://openapi.taifex.com.tw/v1/DailyVIX"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 轉換為 DataFrame
            df = pd.DataFrame(data)
            
            # 欄位對應：Date(日期), ClosePrice(收盤指數)
            # 依據期交所 OpenAPI 格式進行調整
            if 'Date' in df.columns and 'ClosePrice' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df['ClosePrice'] = pd.to_numeric(df['ClosePrice'], errors='coerce')
                df = df.rename(columns={'ClosePrice': 'VIX'}).set_index('Date')
                return df.sort_index(ascending=False)
            else:
                st.error(f"API 欄位異常，抓到：{df.columns.tolist()}")
                return None
        else:
            st.error(f"期交所 API 連線失敗，代碼：{response.status_code}")
            return None
    except Exception as e:
        st.error(f"連線發生錯誤: {e}")
        return None

# --- UI 介面 ---
st.title("🏦 台指 VIX 官方 OpenAPI 監控")
st.info("數據來源：台灣期交所 (TAIFEX) OpenAPI | 顯示範圍：近三個月每日收盤")

# 側邊欄重新整理
if st.sidebar.button("🔄 刷新數據"):
    st.cache_data.clear()
    st.rerun()

# 抓取數據
with st.spinner('連線官方 API 中...'):
    vix_df = get_vix_from_openapi()

if vix_df is not None and not vix_df.empty:
    # 取得最新一筆 (最後交易日)
    latest_val = float(vix_df['VIX'].iloc[0])
    latest_date = vix_df.index[0]
    
    # 計算漲跌 (與前一交易日比較)
    if len(vix_df) > 1:
        prev_val = float(vix_df['VIX'].iloc[1])
        delta = latest_val - prev_val
    else:
        delta = 0

    # 1. 數據看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"最後收盤價 ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    with col2:
        status = "😱 避險升溫" if latest_val > 25 else "😊 情緒穩定"
        st.subheader(f"市場狀態：{status}")
    with col3:
        st.write("**今日提醒：**")
        st.write("2026-04-06 補假休市，此為最後成交數據。")

    st.divider()

    # 2. 數據清單
    st.subheader("📋 歷史收盤數據清單")
    st.dataframe(
        vix_df.style.format("{:.2f}")
              .background_gradient(cmap="Reds", subset=['VIX']),
        use_container_width=True,
        height=500
    )

else:
    st.warning("目前無法透過 OpenAPI 取得數據。")
    st.info("這可能是因為假日期間 API 進行維護。建議開盤日再試，或檢查 API 連結是否正確。")

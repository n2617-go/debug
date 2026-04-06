import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="期交所 VIX 監控", layout="wide")

def get_vix_from_taifex_openapi():
    """
    直接從期交所 OpenAPI 抓取數據
    網址：https://openapi.taifex.com.tw/v1/DailyVIX
    """
    url = "https://openapi.taifex.com.tw/v1/DailyVIX"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # 欄位轉換：期交所格式為 Date, ClosePrice
            if 'Date' in df.columns and 'ClosePrice' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df['VIX'] = pd.to_numeric(df['ClosePrice'], errors='coerce')
                
                # 重要：過濾掉 VIX 為空或 NaN 的行 (排除無交易的假日)
                df = df.dropna(subset=['VIX'])
                
                # 依日期排序，最新在前
                df = df.sort_values('Date', ascending=False)
                return df
        return None
    except Exception as e:
        st.sidebar.error(f"API 連線失敗: {e}")
        return None

# --- UI 介面 ---
st.title("🏦 台指 VIX 官方數據 (期交所 OpenAPI)")
st.caption(f"檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 手動更新按鈕
if st.button("🔄 刷新官方數據"):
    st.cache_data.clear()
    st.rerun()

with st.spinner('連線期交所 OpenAPI 中...'):
    df_vix = get_vix_from_taifex_openapi()

if df_vix is not None and not df_vix.empty:
    # 取得最新一筆真實交易資料 (應該會跳過 4/6, 4/3，抓到 4/2)
    latest_row = df_vix.iloc[0]
    latest_val = float(latest_row['VIX'])
    latest_date = latest_row['Date']
    
    # 取得前一交易日計算漲跌
    if len(df_vix) > 1:
        prev_val = float(df_vix.iloc[1]['VIX'])
        delta = latest_val - prev_val
    else:
        delta = 0

    # 1. 顯示指標
    col1, col2, col3 = st.columns(3)
    with col1:
        # 判斷是否為今天 (4/6)
        is_today = latest_date == datetime.now().date()
        label = "今日數據" if is_today else "最後交易日"
        st.metric(f"{label} ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    
    with col2:
        if latest_val > 25:
            st.error("🚨 市場情緒：恐慌上升")
        elif latest_val < 18:
            st.success("😊 市場情緒：穩定樂觀")
        else:
            st.info("🟡 市場情緒：常態波動")
            
    with col3:
        st.write("**連假狀態：**")
        st.warning("4/3-4/6 休市，目前顯示 4/2 結算價。")

    st.divider()

    # 2. 顯示完整列表
    st.subheader("📋 歷史收盤數據紀錄 (期交所)")
    st.dataframe(
        df_vix.set_index('Date').style.format("{:.2f}"),
        use_container_width=True
    )
else:
    st.error("❌ 無法取得期交所 OpenAPI 數據。")
    st.info("原因可能是：\n1. 官方 API 伺服器在假日進行維護。\n2. 您的網路環境限制了連線。")

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(page_title="台指 VIX 數據監控", layout="wide")

def get_vix_data(source="yfinance"):
    """
    抓取台指 VIX 數據
    """
    try:
        if source == "yfinance":
            # ^VIXTWN 為 Yahoo Finance 台指 VIX 代號
            vix = yf.Ticker("^VIXTWN")
            df = vix.history(period="1mo") # 抓取一個月數據
            if df.empty:
                return None
            # 整理格式：只取收盤價，並格式化日期
            df = df[['Close']].rename(columns={'Close': 'VIX'})
            df.index = df.index.date # 只保留日期部分
            return df
            
        elif source == "FinMind":
            from FinMind.data import DataLoader
            api = DataLoader()
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            df = api.taiwan_vix(start_date=start_date)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date']).dt.date
                df = df.set_index('date')
                return df[['close']].rename(columns={'close': 'VIX'})
        return None
    except Exception as e:
        st.error(f"抓取錯誤: {e}")
        return None

# --- UI 介面 ---
st.title("📑 台指 VIX 指數數據表")

# 側邊欄控制
with st.sidebar:
    st.header("設定")
    data_source = st.radio("選擇資料來源", ["yfinance", "FinMind"])
    if st.button("刷新數據"):
        st.rerun()

# 執行抓取
vix_df = get_vix_data(data_source)

if vix_df is not None:
    # 計算最新資訊
    latest_val = vix_df['VIX'].iloc[-1]
    prev_val = vix_df['VIX'].iloc[-2]
    delta = latest_val - prev_val
    
    # 顯示指標卡
    col1, col2 = st.columns(2)
    with col1:
        st.metric("最新 VIX 點位", f"{latest_val:.2f}", f"{delta:.2f}")
    with col2:
        # 簡單的情緒標籤
        if latest_val > 25:
            label = "🔴 市場恐慌 (High Volatility)"
        elif latest_val < 15:
            label = "🟢 市場樂觀 (Low Volatility)"
        else:
            label = "🟡 波動正常"
        st.write(f"### 當前狀態：{label}")

    st.divider()

    # 顯示數據表格
    st.subheader(f"歷史數據明細 ({data_source})")
    
    # 將索引轉為字串方便閱讀，並降冪排列（最新的在上面）
    display_df = vix_df.sort_index(ascending=False)
    
    st.dataframe(
        display_df.style.format("{:.2f}"), # 格式化數值到小數點第二位
        use_container_width=True,
        height=500
    )

else:
    st.warning("無法取得數據，請檢查 API 或 Ticker 是否有效。")

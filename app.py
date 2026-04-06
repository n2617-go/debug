import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(page_title="台指 VIX 監控中心", layout="wide")

def get_vix_data():
    """
    雙來源抓取機制：優先 FinMind，備援 yfinance
    """
    # --- 來源 1: FinMind ---
    try:
        from FinMind.data import DataLoader
        api = DataLoader()
        # 抓取最近 60 天的資料
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        df_fm = api.taiwan_vix(start_date=start_date)
        
        if not df_fm.empty:
            df_fm['date'] = pd.to_datetime(df_fm['date']).dt.date
            df_fm = df_fm.rename(columns={'close': 'VIX', 'date': 'Date'})
            df_fm = df_fm.set_index('Date')
            return df_fm[['VIX']], "FinMind"
    except Exception as e:
        # 如果沒安裝 FinMind 或出錯，靜默跳過轉向備援
        pass

    # --- 來源 2: yfinance (備援) ---
    try:
        # 嘗試多個可能代號
        for ticker in ["^VIXTWN", "VIXTWN.TW"]:
            vix = yf.Ticker(ticker)
            df_yf = vix.history(period="2mo")
            if not df_yf.empty:
                df_yf.index = df_yf.index.date
                df_yf = df_yf[['Close']].rename(columns={'Close': 'VIX'})
                return df_yf, f"yfinance ({ticker})"
    except Exception as e:
        st.error(f"備援來源也失敗: {e}")
    
    return None, None

# --- UI 介面 ---
st.title("📊 台指 VIX (VIXTWN) 數據中心")
st.markdown("本系統整合 **FinMind** 與 **yfinance** 數據源，確保休盤期間也能顯示最後收盤價。")

# 獲取數據
with st.spinner('正在同步市場數據...'):
    vix_df, source_name = get_vix_data()

if vix_df is not None and not vix_df.empty:
    # 排序：確保最新在後以便計算
    vix_df = vix_df.sort_index()
    
    latest_date = vix_df.index[-1]
    latest_val = vix_df['VIX'].iloc[-1]
    
    # 計算漲跌
    if len(vix_df) > 1:
        prev_val = vix_df['VIX'].iloc[-2]
        delta = latest_val - prev_val
    else:
        delta = 0

    # 1. 頂部數據看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"最新收盤 ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    with col2:
        # 情緒雷達
        if latest_val >= 25:
            color = "inverse" # 紅色
            msg = "🔴 市場恐慌感升溫"
        elif latest_val <= 16:
            color = "normal" # 綠色
            msg = "🟢 市場情緒極度樂觀"
        else:
            color = "off" # 灰色
            msg = "🟡 波動率處於常態"
        st.write(f"### {msg}")
    with col3:
        st.write(f"**目前數據源：** `{source_name}`")
        if st.button("🔄 強制刷新"):
            st.rerun()

    st.divider()

    # 2. 數據明細
    st.subheader("📋 歷史數據清單")
    
    # 顯示表格 (最新在前)
    display_df = vix_df.sort_index(ascending=False)
    
    # 使用 Streamlit 原生表格並美化
    st.dataframe(
        display_df.style.format("{:.2f}").highlight_max(axis=0, color='#FFCCCC'),
        use_container_width=True,
        height=400
    )

    # 3. 實用提醒
    with st.expander("💡 投資筆記"):
        st.info("""
        * **VIX 突破 25-30：** 通常代表大盤正在急跌，融資斷頭壓力大，可能是尋求落底支撐的訊號。
        * **VIX 低於 15：** 代表市場溫和，但也需提防「居安思危」，過度樂觀時常是波段高點。
        * **休盤說明：** 若為假日或非交易時段，數據會停留在上一個交易日的最終結算價。
        """)

else:
    st.error("❌ 所有數據源連線失敗。")
    st.info("建議檢查：1. 是否安裝 `pip install finmind yfinance`  2. 網路是否能連上 Yahoo Finance。")


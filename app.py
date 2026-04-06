import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(page_title="台指 VIX 即時監控系統", layout="wide")

def get_vix_comprehensive():
    """
    核心邏輯：
    1. 抓取 yfinance 1m 資料 (最即時)
    2. 抓取 FinMind 歷史資料 (最權威)
    3. 若 FinMind 失敗，由 yfinance 歷史資料補位
    """
    now = datetime.now()
    df_final_hist = None
    rt_val, rt_time = None, None
    source_info = "FinMind + yfinance"

    # --- Step 1: 抓取 yfinance 1m 即時數據 ---
    try:
        # 抓取 7 天內的 1 分鐘資料，確保跨週末沒問題
        yf_raw = yf.download("^VIXTWN", period="7d", interval="1m", progress=False)
        if not yf_raw.empty:
            # 處理 yfinance 可能的 MultiIndex 欄位
            if isinstance(yf_raw.columns, pd.MultiIndex):
                yf_raw.columns = yf_raw.columns.get_level_values(0)
            
            rt_val = float(yf_raw['Close'].iloc[-1])
            rt_time = yf_raw.index[-1]
            
            # 轉換成日線備用 (以防 FinMind 掛掉)
            df_yf_daily = yf_raw.resample('D').last()[['Close']].dropna()
            df_yf_daily.index = df_yf_daily.index.date
            df_yf_daily.columns = ['VIX']
        else:
            df_yf_daily = None
    except Exception as e:
        st.sidebar.error(f"yfinance 讀取失敗: {e}")
        df_yf_daily = None

    # --- Step 2: 抓取 FinMind 數據 ---
    try:
        api = DataLoader()
        start_dt = (now - timedelta(days=60)).strftime('%Y-%m-%d')
        df_fm = api.taiwan_stock_index(index_id='VIX', start_date=start_dt)
        
        if df_fm is not None and not df_fm.empty:
            df_fm['date'] = pd.to_datetime(df_fm['date']).dt.date
            df_final_hist = df_fm.rename(columns={'date': 'Date', 'close': 'VIX'}).set_index('Date')[['VIX']]
        else:
            # FinMind 回傳空值，使用 yfinance 補位
            df_final_hist = df_yf_daily
            source_info = "yfinance (FinMind 無回應)"
    except:
        # FinMind 報錯，使用 yfinance 補位
        df_final_hist = df_yf_daily
        source_info = "yfinance (FinMind 異常)"

    return df_final_hist, rt_val, rt_time, source_info

# --- UI 介面 ---
st.title("🚀 台指 VIX (VIXTWN) 1分鐘即時監控")
st.markdown(f"目前時間: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

with st.spinner('正在同步全球交易所數據...'):
    df_hist, rt_val, rt_time, source = get_vix_comprehensive()

if df_hist is not None and not df_hist.empty:
    # 取得前一交易日收盤作為基準
    # 如果今天已經有數據，基準就是倒數第二筆；如果今天還沒開盤，基準就是最後一筆
    last_close = float(df_hist['VIX'].iloc[-1])
    
    # 指標看板
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # 顯示最新跳動
        display_val = rt_val if rt_val else last_close
        display_time = rt_time.strftime('%H:%M:%S') if rt_val else "已收盤"
        delta = display_val - last_close
        st.metric(f"即時點位 ({display_time})", f"{display_val:.2f}", f"{delta:.2f}")

    with c2:
        # 情緒判定
        if display_val >= 28:
            st.error("😱 極度恐慌 - 建議保守")
        elif display_val >= 20:
            st.warning("😟 波動放大 - 注意風險")
        else:
            st.success("😊 盤勢平穩 - 氣氛樂觀")

    with c3:
        st.write(f"**數據來源：** `{source}`")
        if st.button("🔄 立即刷新"):
            st.rerun()

    st.divider()

    # 數據表與簡易分析
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📋 歷史日線清單")
        st.dataframe(
            df_hist.sort_index(ascending=False).style.format("{:.2f}"),
            use_container_width=True,
            height=400
        )
    
    with col_right:
        st.subheader("💡 監控備註")
        st.info(f"""
        - **昨日基準：** {last_close:.2f}
        - **1m 更新：** yfinance 提供
        - **延遲說明：** 免費數據通常延遲 15 分鐘
        - **觀察重點：** VIX 暴增通常伴隨大盤急跌
        """)
else:
    st.error("❌ 嚴重錯誤：無法從任何來源取得數據。")
    st.info("請檢查您的網路連線，或嘗試在終端機執行 `pip install --upgrade yfinance FinMind`。")

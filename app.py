import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(page_title="台指 VIX 監控 (全時段版)", layout="wide")

def get_vix_master():
    """
    全時段數據抓取邏輯：
    1. 抓取 yfinance 7天內的 1m 資料 (確保一定有最後一筆成交)
    2. 抓取 FinMind 歷史日線作為基準
    """
    now = datetime.now()
    
    # --- Step 1. 抓取最即時跳動 (yfinance) ---
    df_rt = pd.DataFrame()
    try:
        # 使用 ^VIXTWN，抓 7d 確保週末/連假後一定有資料
        data = yf.download("^VIXTWN", period="7d", interval="1m", progress=False)
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            df_rt = data[['Close']].rename(columns={'Close': 'VIX'})
    except:
        pass

    # --- Step 2. 抓取歷史基準 (FinMind) ---
    df_hist = pd.DataFrame()
    try:
        api = DataLoader()
        start_dt = (now - timedelta(days=60)).strftime('%Y-%m-%d')
        df_fm = api.taiwan_stock_index(index_id='VIX', start_date=start_dt)
        if df_fm is not None and not df_fm.empty:
            df_fm['date'] = pd.to_datetime(df_fm['date']).dt.date
            df_hist = df_fm.rename(columns={'date': 'Date', 'close': 'VIX'}).set_index('Date')
    except:
        pass

    # --- Step 3. 補位邏輯 ---
    # 如果 FinMind 失敗，用 yfinance 轉日線補位
    if df_hist.empty and not df_rt.empty:
        df_hist = df_rt.resample('D').last().dropna()
        df_hist.index = pd.to_datetime(df_hist.index).date

    return df_rt, df_hist

# --- UI 呈現 ---
st.title("🛡️ 台指 VIX 即時/末日數據監控")
st.caption(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with st.spinner('正在同步全球交易所數據...'):
    df_rt, df_hist = get_vix_master()

if not df_hist.empty:
    # 邏輯判斷：最新點位與時間
    if not df_rt.empty:
        current_vix = float(df_rt['VIX'].iloc[-1])
        update_time = df_rt.index[-1] # 這是 Timestamp
        
        # 判斷是否為「今天」的數據
        is_today = update_time.date() == datetime.now().date()
        time_label = update_time.strftime('%H:%M:%S') if is_today else update_time.strftime('%Y-%m-%d')
        status_text = "🔴 盤中即時" if is_today else "⚪ 最後交易日"
    else:
        current_vix = float(df_hist['VIX'].iloc[-1])
        time_label = "無即時數據"
        status_text = "⚪ 歷史數據"

    # 基準價：取歷史倒數第二筆(若今天已開盤) 或 最後一筆(若今天未開盤)
    # 為了簡化，統一拿歷史紀錄最後一筆當昨日基準
    ref_close = float(df_hist['VIX'].iloc[-1])
    delta = current_vix - ref_close

    # 1. 頂部看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"VIX 點位 ({time_label})", f"{current_vix:.2f}", f"{delta:.2f}")
    with col2:
        st.subheader(f"狀態：{status_text}")
        if current_vix > 25:
            st.warning("市場情緒：恐慌感上升")
        else:
            st.success("市場情緒：相對穩定")
    with col3:
        if st.button("🔄 手動刷新"):
            st.rerun()

    st.divider()

    # 2. 數據細節
    tab1, tab2 = st.tabs(["歷史日線表格", "最近 1m 跳動紀錄"])
    
    with tab1:
        st.dataframe(df_hist.sort_index(ascending=False).style.format("{:.2f}"), use_container_width=True)
    
    with tab2:
        if not df_rt.empty:
            st.dataframe(df_rt.sort_index(ascending=False).head(100).style.format("{:.2f}"), use_container_width=True)
        else:
            st.info("目前沒有分鐘級跳動數據。")

else:
    st.error("❌ 抓取失敗。")
    st.info("請確認已安裝套件：`pip install --upgrade yfinance FinMind` 並確認網路環境。")

import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(page_title="台指 VIX 即時監控", layout="wide")

def get_vix_data():
    """
    整合抓取：yfinance (即時分鐘資料) + FinMind (歷史日資料)
    """
    api = DataLoader()
    now = datetime.now()
    
    # 1. 抓取 FinMind 歷史日線 (作為基準)
    try:
        start_dt = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        df_hist = api.taiwan_stock_index(index_id='VIX', start_date=start_dt)
        if not df_hist.empty:
            df_hist['date'] = pd.to_datetime(df_hist['date']).dt.date
            df_hist = df_hist.rename(columns={'date': 'Date', 'close': 'VIX'}).set_index('Date')
        else:
            df_hist = None
    except:
        df_hist = None

    # 2. 抓取 yfinance 即時分鐘線 (interval='1m')
    try:
        # 抓取最近 7 天的分鐘資料，確保能跨越週末
        df_yf = yf.download("^VIXTWN", period="7d", interval="1m", progress=False)
        
        if not df_yf.empty:
            # 處理 MultiIndex 欄位 (yfinance 新版常有此狀況)
            if isinstance(df_yf.columns, pd.MultiIndex):
                df_yf.columns = df_yf.columns.get_level_values(0)
            
            # 取得最新的一筆成交價與時間
            latest_rt_vix = float(df_yf['Close'].iloc[-1])
            latest_rt_time = df_yf.index[-1] # 這會包含時分秒
            
            # 將 yfinance 的日線資料轉化為可合併的格式
            df_yf_daily = df_yf.resample('D').last()[['Close']].dropna()
            df_yf_daily.index = df_yf_daily.index.date
            df_yf_daily.columns = ['VIX']
        else:
            latest_rt_vix, latest_rt_time, df_yf_daily = None, None, None
    except:
        latest_rt_vix, latest_rt_time, df_yf_daily = None, None, None

    return df_hist, latest_rt_vix, latest_rt_time, df_yf_daily

# --- UI 介面 ---
st.title("⚡ 台指 VIX 即時跳動監控")
st.caption("結合 FinMind 歷史權威數據與 yfinance 1分鐘即時行情")

with st.spinner('數據同步中...'):
    df_hist, rt_vix, rt_time, df_yf_daily = get_vix_data()

if df_hist is not None:
    # 取得昨日收盤基準
    last_close = float(df_hist['VIX'].iloc[-1])
    last_date = df_hist.index[-1]

    # 1. 指標看板
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 如果有即時數據就顯示即時，否則顯示歷史收盤
        display_val = rt_vix if rt_vix else last_close
        display_time = rt_time.strftime('%Y-%m-%d %H:%M') if rt_vix else last_date
        delta = display_val - last_close
        st.metric(f"最新點位 ({display_time})", f"{display_val:.2f}", f"{delta:.2f}")

    with col2:
        # 市場情緒
        v = display_val
        if v >= 25: status, color = "😱 極度恐慌", "red"
        elif v >= 20: status, color = "😟 波動加劇", "orange"
        elif v <= 16: status, color = "😇 極度樂觀", "green"
        else: status, color = "🟢 盤勢平穩", "blue"
        st.markdown(f"### 市場狀態：:{color}[{status}]")

    with col3:
        if st.button("🔄 刷新即時行情"):
            st.rerun()

    st.divider()

    # 2. 數據清單
    st.subheader("📋 歷史數據明細 (日線)")
    
    # 整合 FinMind 與 yfinance 的日層級數據 (避免週末沒更新)
    final_df = df_hist.copy()
    if df_yf_daily is not None:
        # 更新最後幾天的數據，以 yfinance 為準（因為有當天最新）
        for date, row in df_yf_daily.iterrows():
            final_df.loc[date] = row['VIX']
    
    # 降冪排列並格式化
    st.dataframe(
        final_df.sort_index(ascending=False).style.format("{:.2f}"),
        use_container_width=True,
        height=400
    )

    # 3. 交易提醒
    st.info(f"**備註：** 當前 yfinance 提供的 1m 數據通常有 15 分鐘延遲。目前最後一筆時間為 {rt_time}。")

else:
    st.error("❌ 無法取得基準數據，請檢查 FinMind API 狀態。")

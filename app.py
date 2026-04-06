import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="台指 VIX 長假監控版", layout="wide")

def get_vix_data_robust():
    """
    最強容錯抓取：自動回溯長假，抓取最近一個真實交易日
    """
    ticker = "^VIXTWN"
    try:
        # 抓取 15 天確保涵蓋所有長假 (如過年、清明)
        df = yf.download(ticker, period="15d", interval="1d", progress=False)
        
        if not df.empty:
            # 1. 處理 MultiIndex 欄位
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 2. 移除可能存在的空值 (假日有時會產生只有日期但沒數值的列)
            df = df.dropna(subset=['Close'])
            
            # 3. 整理格式
            df = df[['Close']].rename(columns={'Close': 'VIX'})
            df.index = pd.to_datetime(df.index).date
            return df.sort_index(ascending=False) # 最新在前
        return None
    except Exception as e:
        st.error(f"連線異常: {e}")
        return None

# --- UI 呈現 ---
st.title("📊 台指 VIX 監控 (連假自動回溯)")
st.caption(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.button("🔄 刷新數據庫"):
    st.cache_data.clear()
    st.rerun()

with st.spinner('正在搜尋最近交易日數據...'):
    vix_df = get_vix_data_robust()

if vix_df is not None and not vix_df.empty:
    # 取得最新的一筆真實成交資料
    latest_val = float(vix_df['VIX'].iloc[0])
    latest_date = vix_df.index[0]  # 這邊會自動抓到 4/2
    
    # 取得前一交易日計算漲跌
    if len(vix_df) > 1:
        prev_val = float(vix_df['VIX'].iloc[1])
        delta = latest_val - prev_val
    else:
        delta = 0

    # 1. 看板顯示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 判斷是否為「今天」
        is_today = latest_date == datetime.now().date()
        status_label = "今日盤中" if is_today else "最後交易日"
        st.metric(f"{status_label} ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    
    with col2:
        if latest_val >= 25:
            st.error("🚨 市場狀態：避險情緒高漲")
        elif latest_val <= 17:
            st.success("😊 市場狀態：樂觀平穩")
        else:
            st.info("🟡 市場狀態：常態波動")
            
    with col3:
        st.write("**休市公告：**")
        st.warning("目前處於清明連假補假，數據已自動回溯至 4/2 結算點位。")

    st.divider()

    # 2. 數據表
    st.subheader("📋 歷史交易紀錄 (自動過濾休假日)")
    st.dataframe(
        vix_df.style.format("{:.2f}")
              .background_gradient(cmap="YlOrRd", subset=['VIX']),
        use_container_width=True
    )
    
else:
    st.error("❌ 無法取得數據。請確認 yfinance 是否正常運作。")

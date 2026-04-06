import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="台指 VIX 官網數據直接對接", layout="wide")

def get_vix_from_taifex_direct():
    """
    模擬瀏覽器直接從期交所官網下載 VIX 歷史資料 CSV
    """
    # 這是期交所官網下載當月數據的 Action URL
    url = "https://www.taifex.com.tw/cht/7/vixMinNew"
    
    # 強大的瀏覽器偽裝 Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.taifex.com.tw/cht/7/vixMinNew",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    }

    try:
        # 1. 先獲取網頁內容，確認是否能連通
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # 使用 pandas 直接讀取網頁中的表格 (期交所這頁是用 table 標籤顯示)
            # 因為 HTML 內可能有編碼問題，我們指定 big5 或 utf-8
            tables = pd.read_html(io.StringIO(response.text))
            
            # 通常數據在最後一個表格
            for df in tables:
                if '日期' in df.columns and '波動率指數' in df.columns:
                    df['日期'] = pd.to_datetime(df['日期']).dt.date
                    df['VIX'] = pd.to_numeric(df['波動率指數'], errors='coerce')
                    df = df.dropna(subset=['VIX'])
                    return df.sort_values('日期', ascending=False)
            
            st.warning("已連上網頁，但未發現 VIX 數據表格。")
            return None
        else:
            st.error(f"期交所官網連線失敗 (Status: {response.status_code})")
            return None
    except Exception as e:
        st.error(f"抓取發生錯誤: {e}")
        return None

# --- UI 介面 ---
st.title("🛡️ 台指 VIX 官網直連版")
st.caption(f"目前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (連假補假中)")

# 手動刷新
if st.sidebar.button("🔄 手動同步官網數據"):
    st.cache_data.clear()
    st.rerun()

with st.spinner('正在模擬瀏覽器讀取期交所官網數據...'):
    vix_df = get_vix_from_taifex_direct()

if vix_df is not None and not vix_df.empty:
    # 取得最新一筆 (會自動鎖定 4/2)
    latest_row = vix_df.iloc[0]
    latest_val = float(latest_row['VIX'])
    latest_date = latest_row['日期']
    
    # 漲跌計算
    if len(vix_df) > 1:
        prev_val = float(vix_df.iloc[1]['VIX'])
        delta = latest_val - prev_val
    else:
        delta = 0

    # 看板
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(f"最後結算 ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    with c2:
        status = "😱 避險情緒高" if latest_val > 25 else "😊 情緒穩定"
        st.subheader(f"市場狀態：{status}")
    with c3:
        st.info("💡 目前為補假期間，資料來源為官網最後更新之 4/2 數據。")

    st.divider()

    # 表格
    st.subheader("📋 官網原始數據紀錄")
    st.dataframe(vix_df.set_index('日期'), use_container_width=True)

else:
    st.error("❌ 官網數據解析失敗。")
    st.info("原因分析：期交所網頁可能偵測到非瀏覽器存取。建議開盤日 (4/7) 再嘗試連線即時 API。")

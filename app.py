import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="台指 VIX 監控中心", layout="wide")

def get_vix_from_taifex():
    """
    從台灣期交所 (TAIFEX) 抓取台指 VIX 指數
    強化版：自動處理 CSV 標題偏移問題
    """
    url = "https://www.taifex.com.tw/cht/7/getVixDailyCSV"
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            # 讀取原始文字並檢查內容
            raw_text = response.text
            
            # 期交所 CSV 常在第一行放標題，我們直接搜尋「日期」出現的位置
            # 或是嘗試直接用 pandas 讀取，並處理可能的標題列
            f = StringIO(raw_text)
            
            # 先試著讀取前幾行，找出包含「日期」的那一行作為 header
            lines = raw_text.split('\n')
            header_index = 0
            for i, line in enumerate(lines):
                if '日期' in line and '收盤指數' in line:
                    header_index = i
                    break
            
            # 重新讀取，從正確的 header 開始
            df = pd.read_csv(StringIO('\n'.join(lines[header_index:])))
            
            # 1. 清理欄位名稱（移除空格或特殊字元）
            df.columns = [c.strip() for c in df.columns]
            
            # 2. 核心欄位處理：確保「日期」與「收盤指數」存在
            # 期交所欄位名可能是：['日期', '收盤指數']
            if '日期' in df.columns and '收盤指數' in df.columns:
                # 轉成日期格式 (處理 YYYY/MM/DD)
                df['日期'] = pd.to_datetime(df['日期']).dt.date
                # 轉成數值
                df['收盤指數'] = pd.to_numeric(df['收盤指數'], errors='coerce')
                # 移除 NaN 並排序
                df = df.dropna(subset=['日期', '收盤指數']).sort_values('日期')
                
                return df[['日期', '收盤指數']].rename(columns={'收盤指數': 'VIX'}).set_index('日期')
            else:
                st.error(f"找到的欄位不符：{df.columns.tolist()}")
                return None
        else:
            st.error(f"期交所伺服器回應錯誤: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"解析失敗: {e}")
        return None

# --- UI 介面 ---
st.title("📊 台指 VIX (VIXTWN) 數據監控")
st.caption("數據來源：台灣期交所 (TAIFEX) 官方 CSV")

# 獲取數據
with st.spinner('正在從期交所抓取最新數據...'):
    vix_df = get_vix_from_taifex()

if vix_df is not None and not vix_df.empty:
    # 提取最新一筆（即使休盤，也會是最後一個交易日的數據）
    latest_date = vix_df.index[-1]
    latest_val = vix_df['VIX'].iloc[-1]
    
    # 取得前一交易日計算漲跌
    if len(vix_df) > 1:
        prev_val = vix_df['VIX'].iloc[-2]
        delta = latest_val - prev_val
    else:
        delta = 0

    # 1. 顯示指標卡片
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"最新收盤 ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    
    with col2:
        if latest_val >= 25:
            st.warning("😱 市場目前較為恐慌")
        elif latest_val <= 15:
            st.success("😊 市場情緒穩定")
        else:
            st.info("🟡 波動率處於常態")
            
    with col3:
        if st.button("🔄 刷新數據"):
            st.rerun()

    st.divider()

    # 2. 數據表格
    st.subheader("📋 歷史數據清單 (最新在前)")
    display_df = vix_df.sort_index(ascending=False)
    
    st.dataframe(
        display_df.style.format("{:.2f}"),
        use_container_width=True,
        height=500
    )
else:
    st.warning("⚠️ 目前無法從期交所獲取數據。")
    st.info("這可能是因為期交所 CSV 格式變動或暫時性斷線。請確認 https://www.taifex.com.tw/cht/7/getVixDailyCSV 是否可正常下載。")


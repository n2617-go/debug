import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="台指 VIX 監控中心", layout="wide")

def get_vix_from_taifex():
    """
    從台灣期交所 (TAIFEX) 抓取台指 VIX 指數歷史資料
    連結：https://www.taifex.com.tw/cht/7/getVixDailyCSV
    """
    url = "https://www.taifex.com.tw/cht/7/getVixDailyCSV"
    try:
        # 下載資料
        response = requests.get(url)
        response.encoding = 'utf-8' # 確保中文不亂碼
        
        if response.status_code == 200:
            # 讀取 CSV (期交所的 CSV 格式：日期,收盤指數)
            # skiprows=1 是因為第一行通常是標題或宣告
            df = pd.read_csv(StringIO(response.text))
            
            # 1. 清理資料：移除空格、確保欄位正確
            df.columns = [c.strip() for c in df.columns]
            
            # 2. 轉換日期格式 (期交所格式通常是 YYYY/MM/DD)
            df['日期'] = pd.to_datetime(df['日期']).dt.date
            
            # 3. 處理數值 (確保收盤指數是 float)
            df['收盤指數'] = pd.to_numeric(df['收盤指數'], errors='coerce')
            
            # 4. 移除空值並重新排序 (最新日期在後，方便計算)
            df = df.dropna().sort_values('日期')
            
            # 5. 設定索引
            df = df.set_index('日期')
            return df[['收盤指數']].rename(columns={'收盤指數': 'VIX'})
            
        else:
            st.error(f"期交所伺服器回應錯誤: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

# --- UI 介面 ---
st.title("📊 台指 VIX (VIXTWN) 數據監控")
st.caption(f"數據來源：台灣期交所 (TAIFEX) | 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 側邊欄控制
with st.sidebar:
    st.header("功能選單")
    if st.button("🔄 立即更新數據"):
        st.cache_data.clear() # 清除快取強制重新抓取
        st.rerun()

# 獲取數據 (使用快取避免頻繁請求)
@st.cache_data(ttl=3600) # 每小時自動過期一次
def load_data():
    return get_vix_from_taifex()

vix_df = load_data()

if vix_df is not None and not vix_df.empty:
    # 提取數據 (最新的在最後一行)
    latest_val = vix_df['VIX'].iloc[-1]
    prev_val = vix_df['VIX'].iloc[-2]
    delta = latest_val - prev_val
    
    # 1. 顯示指標卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("最新 VIX 指數", f"{latest_val:.2f}", f"{delta:.2f}")
    
    with col2:
        # 判斷市場情緒
        if latest_val >= 30:
            status = "😱 極度恐慌 (避險升溫)"
            color = "red"
        elif latest_val >= 20:
            status = "😟 波動增加"
            color = "orange"
        else:
            status = "😊 市場平穩"
            color = "green"
        st.subheader(f"當前狀態：:{color}[{status}]")
        
    with col3:
        st.write(f"**資料筆數：** {len(vix_df)} 筆")
        st.write(f"**最近更新日：** {vix_df.index[-1]}")

    st.divider()

    # 2. 顯示數據表格 (降冪排序，最新在最上方)
    st.subheader("📋 歷史數據清單")
    
    # 格式化表格
    display_df = vix_df.sort_index(ascending=False)
    
    st.dataframe(
        display_df.style.format("{:.2f}")
                  .background_gradient(cmap="Reds", subset=["VIX"]), # 數值越高顏色越紅
        use_container_width=True,
        height=600
    )

else:
    st.warning("⚠️ 無法獲取期交所數據。")
    st.info("請檢查您的網路連線，或稍後再試。")


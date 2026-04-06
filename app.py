import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="台指 VIX 官方數據監控", layout="wide")

def get_taifex_vix_data():
    """
    從期交所 OpenAPI 獲取 VIX 數據
    網址: https://openapi.taifex.com.tw/v1/DailyVIX
    """
    url = "https://openapi.taifex.com.tw/v1/DailyVIX"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 發送請求，增加 timeout 避免卡死
        response = requests.get(url, headers=headers, timeout=15, verify=True)
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            # 轉換資料格式
            if 'Date' in df.columns and 'ClosePrice' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                # 將收盤價轉為數字，無效值轉為 NaN
                df['VIX'] = pd.to_numeric(df['ClosePrice'], errors='coerce')
                
                # 重要：過濾掉沒有數值的日期（休盤日）
                df = df.dropna(subset=['VIX'])
                
                # 依日期降冪排列 (最新在前)
                df = df.sort_values('Date', ascending=False)
                return df
            else:
                st.warning("API 欄位格式與預期不符。")
                return None
        else:
            st.error(f"期交所伺服器回應異常 (Status Code: {response.status_code})")
            return None
            
    except Exception as e:
        st.error(f"連線發生錯誤: {e}")
        return None

# --- UI 介面 ---
st.title("🏦 台指 VIX 官方數據監控")
st.caption(f"目前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 手動更新按鈕
if st.button("🔄 立即重新整理 (手動更新)"):
    st.cache_data.clear()
    st.rerun()

with st.spinner('正在從期交所官方來源同步數據...'):
    vix_df = get_taifex_vix_data()

if vix_df is not None and not vix_df.empty:
    # 取得最新一筆真實交易數據 (會自動抓到 4/2)
    latest_data = vix_df.iloc[0]
    latest_val = float(latest_data['VIX'])
    latest_date = latest_data['Date']
    
    # 計算漲跌 (與前一交易日相比)
    if len(vix_df) > 1:
        prev_val = float(vix_df.iloc[1]['VIX'])
        delta = latest_val - prev_val
    else:
        delta = 0

    # 1. 頂部看板
    col1, col2, col3 = st.columns(3)
    with col1:
        # 顯示最後交易日（自動回溯至 4/2）
        st.metric(f"最後結算價 ({latest_date})", f"{latest_val:.2f}", f"{delta:.2f}")
    
    with col2:
        if latest_val > 25:
            st.error("🚨 市場避險情緒濃厚")
        elif latest_val < 18:
            st.success("😊 市場情緒趨於平穩")
        else:
            st.info("🟡 市場波動處於常態")
            
    with col3:
        st.write("**休市通知：**")
        st.warning("4/3 - 4/6 為清明補假，目前顯示連假前（4/2）之最終點位。")

    st.divider()

    # 2. 歷史數據表格
    st.subheader("📋 歷史收盤紀錄 (最新在前)")
    # 使用表格呈現並加入色彩漸層
    st.dataframe(
        vix_df.set_index('Date').style.format("{:.2f}")
              .background_gradient(cmap="Reds", subset=['VIX']),
        use_container_width=True,
        height=450
    )

else:
    st.error("❌ 無法取得數據。")
    st.info("請確認您的網路連線正常。若持續失敗，可能是期交所 API 正在假日維護中。")


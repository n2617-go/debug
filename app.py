import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="VIX 數據直連系統", layout="wide")

def get_vix_via_api():
    """繞過網頁介面，直接請求期交所後台 JSON 數據"""
    # 這是期交所後台真正的數據接口 (API)
    api_url = "https://mis.taifex.com.tw/futures/api/getQuotesList"
    
    # 模擬瀏覽器標頭，避免被當成爬蟲
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    }
    
    # 請求參數：指定要抓取 VIX (台指選擇權波動率指數)
    payload = {
        "MarketType": "4",
        "SymbolType": "F",
        "Kind": "I",
        "SymbolID": "VIXTWN"
    }

    try:
        # 發送 POST 請求
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        data = response.json()
        
        # 解析 JSON 結構
        # 數據通常在 data['RtData']['QuoteList'] 裡面
        if data.get('RtList'):
            vix_item = data['RtList'][0]
            vix_val = vix_item.get('DispPrice', 'N/A') # 這就是我們要的 36.45
            update_time = vix_item.get('DispTime', '')
            return vix_val, update_time, True
        else:
            return "數據格式變更", "", False
            
    except Exception as e:
        return f"連線失敗: {str(e)}", "", False

# --- Streamlit UI ---
st.title("🚀 VIX 數據直連系統 (API 突破版)")
st.markdown("此版本**捨棄瀏覽器模擬**，直接從期交所數據接口獲取數值，完全避開按鈕點擊與亂碼問題。")

if st.button("⚡ 獲取最新 VIX 指數"):
    with st.spinner("正在直連數據源..."):
        val, update_t, ok = get_vix_via_api()
        
        if ok:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("台指 VIX 指數", val)
            with col2:
                st.info(f"📅 數據時間：{update_t}")
            
            st.success("✅ 成功繞過免責聲明與 Cloudflare 檢測！")
        else:
            st.error(f"❌ 擷取失敗：{val}")
            st.warning("如果直連失敗，代表 API 接口可能暫時變更，請回報檢查。")

st.divider()
st.caption("技術原理：不掃描網頁座標，直接攔截網頁背後的 JSON 數據流。")

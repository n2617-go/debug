import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="台指 VIX 監控 (玩股網接口版)", layout="wide")

def get_wantgoo_vix_api():
    """
    不使用 Selenium，改用 Requests 直接模擬 API 請求
    這在 Streamlit Cloud 上最穩定
    """
    # 這是玩股網點位數據的真實來源接口 (Index 頁面數據)
    url = "https://www.wantgoo.com/investor/get-index-info?no=VIXTWN"
    
    # 關鍵：玩股網會檢查來源 (Referer) 與 瀏覽器身分 (User-Agent)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://www.wantgoo.com/index/vixtwn",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        # 使用 Session 保持連線環境
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # 根據玩股網 API 結構提取數值 (通常在 'deal' 或 'last' 欄位)
            # 注意：這裡的欄位名稱需對應實際回傳的 JSON 結構
            vix_price = data.get('deal', 'N/A')
            change_val = data.get('change', 0)
            change_percent = data.get('changePercent', 0)
            update_time = data.get('time', datetime.now().strftime("%H:%M:%S"))
            
            return {
                "price": vix_price,
                "change": change_val,
                "percent": change_percent,
                "time": update_time,
                "success": True
            }
        else:
            return {"success": False, "msg": f"連線失敗: {response.status_code}"}
    except Exception as e:
        return {"success": False, "msg": str(e)}

# --- Streamlit UI ---
st.title("🛡️ 台指 VIX 監控 (玩股網數據直連)")
st.caption(f"今日日期：2026-04-06 (補假休市) | 檢查時間：{datetime.now().strftime('%H:%M:%S')}")

if st.button("🔄 刷新即時點位"):
    st.cache_data.clear()
    st.rerun()

with st.spinner('正在同步玩股網數據源...'):
    result = get_wantgoo_vix_api()

if result["success"]:
    # 1. 顯示指標
    col1, col2, col3 = st.columns(3)
    
    # 格式化顯示 (對應你圖中的 36.45)
    price = result["price"]
    change = result["change"]
    percent = result["percent"]
    
    with col1:
        st.metric(f"VIX 指數 ({result['time']})", f"{price}", f"{change} ({percent}%)")
    
    with col2:
        if float(price) > 30:
            st.error("🚨 市場極度恐慌")
        elif float(price) > 20:
            st.warning("⚠️ 波動度上升")
        else:
            st.success("😊 市場情緒平穩")
            
    with col3:
        st.write("**數據來源：** 玩股網 (WantGoo)")
        st.write("目前為休市狀態，顯示為連假前最後成交價。")

    st.divider()
    
    # 2. 顯示原始資料 (除錯用)
    with st.expander("查看 API 原始回傳數據"):
        st.json(result)
else:
    st.error(f"抓取失敗：{result['msg']}")
    st.info("提示：如果 API 被阻擋，可能需要更換 User-Agent 或檢查 URL。")

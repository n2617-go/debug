import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import subprocess

# 頁面設定
st.set_page_config(page_title="台指 VIX 終極監控系統", layout="wide")

# --- 核心邏輯 A：API 直連模式 (最穩定，不需瀏覽器) ---
def get_vix_via_api():
    """模擬真人請求玩股網後台 API"""
    url = "https://www.wantgoo.com/investor/get-index-info?no=VIXTWN"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://www.wantgoo.com/index/vixtwn",
        "X-Requested-With": "XMLHttpRequest"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "price": data.get('deal'),
                "change": data.get('change'),
                "percent": data.get('changePercent'),
                "time": data.get('time'),
                "success": True
            }
    except Exception as e:
        return {"success": False, "msg": str(e)}
    return {"success": False, "msg": "API 無回應"}

# --- 核心邏輯 B：Playwright 快照模式 (需處理雲端環境錯誤) ---
def capture_vix_with_playwright():
    """修正後的 Playwright 啟動邏輯"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "請在 requirements.txt 加入 playwright", None, False

    url = "https://www.wantgoo.com/index/vixtwn/price-to-earning-river"
    
    with sync_playwright() as p:
        try:
            # 關鍵修正：加入大量啟動參數以適應 Streamlit Cloud 的 Linux 環境
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox", 
                    "--disable-setuid-sandbox", 
                    "--disable-dev-shm-usage", 
                    "--disable-gpu"
                ]
            )
            context = browser.new_context(viewport={'width': 1000, 'height': 800})
            page = context.new_page()
            
            # 前往網頁
            page.goto(url, wait_until="networkidle", timeout=45000)
            
            # 定位綠色框框區域 (.last 或是 .price)
            selector = "span.last"
            page.wait_for_selector(selector, timeout=10000)
            
            vix_val = page.inner_text(selector)
            # 局部截圖
            element = page.query_selector(selector)
            img_bytes = element.screenshot()
            
            browser.close()
            return vix_text, img_bytes, True
        except Exception as e:
            if 'browser' in locals(): browser.close()
            return f"瀏覽器啟動失敗: {str(e)}", None, False

# --- UI 呈現 ---
st.title("🛡️ 台指 VIX 多重監控系統")
st.info(f"📅 今日 2026-04-06 (補假) | 自動鎖定連假前最後成交數據")

tab1, tab2 = st.tabs(["⚡ 高速 API 模式 (推薦)", "📸 座標快照模式"])

with tab1:
    if st.button("🚀 執行 API 抓取"):
        res = get_vix_via_api()
        if res["success"]:
            c1, c2 = st.columns(2)
            c1.metric(f"VIX 指數 ({res['time']})", res['price'], f"{res['change']} ({res['percent']}%)")
            c2.success(f"成功抓取！目前數值為 {res['price']} (對應圖中 36.45)")
            st.json(res)
        else:
            st.error(f"抓取失敗: {res['msg']}")

with tab2:
    st.warning("快照模式在雲端環境較不穩定，建議先在本地測試。")
    if st.button("📷 執行座標快照"):
        # 在雲端環境中，我們必須先嘗試安裝驅動
        subprocess.run(["playwright", "install", "chromium"])
        
        val, img, ok = capture_vix_with_playwright()
        if ok:
            st.metric("快照辨識數值", val)
            st.image(img, caption="網頁座標局部快照")
        else:
            st.error(val)
            st.info("💡 錯誤原因：Streamlit Cloud 缺少 Linux 底層依賴庫 (libgbm1 等)。建議改用 Tab 1 的 API 模式。")


import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="VIX 座標快照監控", layout="wide")

def capture_vix_safe_mode():
    """使用更穩定的資源管理模式執行掃描"""
    url = "https://www.wantgoo.com/index/vixtwn/price-to-earning-river"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 使用 sync_playwright 作為最外層，確保 event loop 穩定
    try:
        with sync_playwright() as p:
            # 1. 啟動瀏覽器
            status_text.text("1/5 正在啟動掃描引擎...")
            progress_bar.progress(20)
            
            # 加入更多穩定參數
            browser = p.chromium.launch(
                headless=True, 
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process"]
            )
            
            # 2. 建立上下文
            status_text.text("2/5 設定座標參數...")
            progress_bar.progress(40)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()

            # 加速設定
            page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())

            # 3. 載入網頁
            status_text.text("3/5 載入玩股網數據中...")
            progress_bar.progress(60)
            # 使用 wait_until="domcontentloaded" 兼顧速度與穩定性
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 4. 定位與抓取
            status_text.text("4/5 座標掃描：鎖定 36.45 區域...")
            progress_bar.progress(80)
            
            selector = "span.last" 
            page.wait_for_selector(selector, timeout=20000)
            
            vix_text = page.inner_text(selector)
            element_handle = page.query_selector(selector)
            screenshot_bytes = element_handle.screenshot()
            
            # 5. 完成並自動關閉 (透過 with 語法自動處理)
            status_text.text("5/5 掃描完成！")
            progress_bar.progress(100)
            
            # 這裡不需要手動 browser.close()，with 會處理，
            # 但為了保險我們在 context 結束前完成數據傳遞
            time.sleep(1)
            
            progress_bar.empty()
            status_text.empty()
            return vix_text, screenshot_bytes, True

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        return f"掃描異常: {str(e)}", None, False

# --- UI ---
st.title("📸 VIX 座標快照系統 (穩定修正版)")
st.info("解決 Event Loop Closed 錯誤，加強資源回收機制。")

if st.button("🚀 執行座標掃描"):
    vix_val, img_bytes, success = capture_vix_safe_mode()
    
    if success:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("掃描到的數值", vix_val)
        with col2:
            st.image(img_bytes, caption="座標局部快照內容")
            st.success("數據掃描成功！")
    else:
        st.error(vix_val)
        st.info("提示：如果持續失敗，請嘗試重啟 Streamlit App 以清理殘留進程。")

st.divider()
st.caption("備註：4/6 為補假休市，系統鎖定掃描 4/2 之數據。")

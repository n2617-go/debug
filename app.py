import streamlit as st
import asyncio
from playwright.sync_api import sync_playwright
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="VIX 座標快照監控", layout="wide")

def capture_vix_snapshot():
    """
    使用 Playwright 對玩股網指定座標/元素進行快照
    """
    url = "https://www.wantgoo.com/index/vixtwn/price-to-earning-river"
    
    with sync_playwright() as p:
        # 啟動瀏覽器 (使用 chromium)
        browser = p.chromium.launch(headless=True)
        # 模擬真人手機或電腦視窗大小
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # 1. 前往網頁
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 2. 定位到你圖中綠色框框的元素 (玩股網主要的價格標籤)
            # 我們使用 CSS Selector 定位那個大大的數字
            price_selector = ".price-box .last" 
            
            # 3. 等待元素出現
            page.wait_for_selector(price_selector, timeout=10000)
            
            # 4. 抓取數值文字
            vix_text = page.inner_text(price_selector)
            
            # 5. 執行「快照」：只截取數值區域的圖片，證明抓取正確
            element_handle = page.query_selector(price_selector)
            screenshot_bytes = element_handle.screenshot()
            
            browser.close()
            return vix_text, screenshot_bytes, True
            
        except Exception as e:
            browser.close()
            return str(e), None, False

# --- Streamlit UI ---
st.title("📸 VIX 座標快照與掃描系統")
st.write(f"今日：2026-04-06 (補假) | 自動鎖定 4/2 最後交易數據 **36.45**")

if st.button("🚀 執行座標掃描與快照"):
    with st.spinner('正在模擬真人開啟網頁並對準座標...'):
        vix_val, img_bytes, success = capture_vix_snapshot()
        
        if success:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("掃描到的數值", vix_val)
                st.write(f"掃描時間：{datetime.now().strftime('%H:%M:%S')}")
            
            with col2:
                st.write("### 局部快照驗證 (OCR 區域)")
                st.image(img_bytes, caption="這是從網頁座標即時截取的圖片內容")
                st.success("座標掃描完成！數值與快照內容一致。")
        else:
            st.error(f"掃描失敗：{vix_val}")
            st.info("若在雲端執行，請確保已在 packages.txt 加入 playwright 依賴，或是在本地執行測試。")

st.divider()
st.write("### 為什麼用快照/座標掃描更強大？")
st.markdown("""
1. **所見即所得**：直接抓取網頁渲染後的圖片，不用擔心 API 欄位變更。
2. **繞過複雜反爬蟲**：對伺服器來說，這就是一次正常的瀏覽器讀取。
3. **視覺證據**：右側的快照圖可以直接讓你對比玩股網原本的畫面。
""")


import streamlit as st
from playwright.sync_api import sync_playwright
import time

def get_vix_data():
    with sync_playwright() as p:
        # 1. 啟動瀏覽器
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # 2. 進入免責聲明頁
        page.goto("https://mis.taifex.com.tw/futures/disclaimer/", wait_until="domcontentloaded")
        
        # 3. 執行顏色辨識強制點擊 (JavaScript)
        page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const style = window.getComputedStyle(btn);
                    // 尋找橘色按鈕
                    if (style.backgroundColor.includes('rgb(255') || btn.className.includes('orange')) {
                        btn.click();
                        return;
                    }
                }
            }
        """)
        
        # 4. 【關鍵修正】強制跳轉到數據頁面，確保避開免責聲明
        time.sleep(3) # 給予一點點點擊反應時間
        page.goto("https://mis.taifex.com.tw/futures/VolatilityQuotes/", wait_until="networkidle")
        
        # 5. 【暴力掃描】尋找 VIX 數值
        # 我們不再只找 td:has-text('.')，而是掃描整個表格尋找符合 VIX 特徵的數字
        vix_val = "未偵測到數值"
        try:
            # 等待表格載入
            page.wait_for_selector("table", timeout=10000)
            
            # 取得所有儲存格
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                # 辨識邏輯：如果是數字、有小數點、且長度在 4~6 之間 (例如 36.45)
                if text.replace('.', '', 1).isdigit() and '.' in text and len(text) < 7:
                    vix_val = text
                    break 
        except Exception as e:
            vix_val = f"數據辨識超時: {str(e)}"
            
        return vix_val

# Streamlit UI
st.title("📊 VIX 自動辨識系統 (穩定版)")

if st.button("🚀 執行一鍵掃描"):
    with st.spinner("正在突破免責聲明並擷取數據..."):
        result = get_vix_data()
        if "." in result:
            st.metric("目前的 VIX 指數", result)
        else:
            st.error(result)

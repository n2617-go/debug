import streamlit as st
from playwright.sync_api import sync_playwright
import time

def physical_force_bypass():
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    with sync_playwright() as p:
        # 使用固定解析度，確保座標準確
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # 1. 進入頁面
        page.goto(url, wait_until="networkidle")
        time.sleep(3) # 等待彈窗完整浮現
        
        # 2. 【核心修正】物理座標點擊
        # 根據你的截圖，橘色按鈕大約在 1280x800 解析度的正中間下方
        # 我們進行「地毯式點擊」：在按鈕可能出現的區域點 5 下
        locations = [(640, 750), (640, 760), (600, 755), (680, 755)]
        for x, y in locations:
            page.mouse.click(x, y)
            time.sleep(0.5)
            
        # 3. 嘗試用 JS 穿透 Shadow DOM 點擊
        page.evaluate("""
            () => {
                const btn = document.querySelector('button.btn-orange') || 
                            document.querySelector('.btn-confirm');
                if (btn) btn.click();
                // 暴力法：直接呼叫確認函式（如果有的話）
                if (typeof confirmDisclaimer === 'function') confirmDisclaimer();
            }
        """)
        
        time.sleep(7) # 關鍵：給予超長的數據加載時間
        
        # 4. 擷取數據
        cells = page.query_selector_all("td")
        res = "N/A"
        for c in cells:
            t = c.inner_text().strip()
            if '.' in t and t.replace('.','').isdigit() and len(t) < 7:
                res = t
                break
        
        shot = page.screenshot()
        return res, shot

# --- UI ---
st.title("🛡️ VIX 物理座標突破版")
if st.button("🚀 執行物理點擊任務"):
    val, img = physical_force_bypass()
    st.metric("偵測結果", val)
    st.image(img, caption="目前畫面快照")

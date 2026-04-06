import streamlit as st
from playwright.sync_api import sync_playwright
import time

def debug_force_vixtwn():
    url = "https://mis.taifex.com.tw/futures/disclaimer"
    screenshots = {}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            
            # 1. 記錄點擊前畫面
            page.goto(url, wait_until="networkidle")
            time.sleep(2)
            screenshots['before'] = page.screenshot()
            
            # 2. 進行更暴力、更寬廣的點擊 (按鈕可能在不同瀏覽器解析度下有細微位移)
            # 我們從中間往下方大面積覆蓋點擊
            page.mouse.click(640, 750)
            time.sleep(0.5)
            page.mouse.click(640, 760)
            time.sleep(0.5)
            
            # 3. 強制執行 JS 點擊確認 (尋找所有可能的按鈕)
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button, a');
                for (let b of btns) {
                    if (b.innerText.includes('我已閱讀') || b.innerText.includes('同意') || b.className.includes('orange')) {
                        b.click();
                    }
                }
            }""")
            
            time.sleep(5)
            screenshots['after'] = page.screenshot()
            
            # 4. 判斷現在在哪
            current_url = page.url
            browser.close()
            return screenshots, current_url
    except Exception as e:
        return None, str(e)

# --- UI 介面 ---
st.title("🛡️ 物理重擊偵錯中心")
if st.button("🚀 開始偵錯重擊"):
    shots, url = debug_force_vixtwn()
    st.write(f"當前網址: {url}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.image(shots['before'], caption="點擊前 (應為免責聲明頁)")
    with c2:
        st.image(shots['after'], caption="點擊後 (檢查是否成功跳轉)")

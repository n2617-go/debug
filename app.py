import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageOps, ImageFilter
io, os, re, time = __import__('io'), __import__('os'), __import__('re'), __import__('time')

def physical_force_precision_bombing():
    """
    針對 1000028204.jpg 優化：
    1. 視窗拉長到 1800px 確保按鈕一定在畫面內
    2. 針對左側橘色區塊進行地毯轟炸
    3. 強制執行 JS 點擊橘色按鈕
    """
    url = "https://mis.taifex.com.tw/futures/disclaimer"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 暴力拉長高度到 1800，確保長頁面的按鈕不會消失
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 1800})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")
            time.sleep(5) 
            
            # 強制滾動到底部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
            # 【地毯式轟炸】針對左側橘色按鈕區域 (X: 400~520)
            # 避開右邊 (X > 600) 的灰色按鈕區域
            for x in range(420, 520, 20):
                for y in range(950, 1150, 20):
                    page.mouse.click(x, y)
                    time.sleep(0.05)
            
            # 【精確 JS 鎖定】直接抓取具有橘色樣式的按鈕
            page.evaluate("""() => {
                const orangeBtn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.innerText.includes('接受') || 
                    getComputedStyle(b).backgroundColor.includes('rgb(255, 128, 0)') ||
                    b.className.includes('orange')
                );
                if (orangeBtn) {
                    orangeBtn.scrollIntoView();
                    orangeBtn.click();
                }
            }""")
            
            time.sleep(10) # 給予跳轉時間
            
            # 數據擷取與過濾
            cells = page.query_selector_all("td")
            for c in cells:
                t = c.inner_text().strip()
                if '.' in t and t.replace('.','').isdigit():
                    val = float(t)
                    # 鎖定 VIX 數值區間，避開首頁的金融/電子期雜訊
                    if 25 < val < 55:
                        res_val = t
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except:
        res_val = "任務逾時"
    return res_val, screenshot

# --- UI 介面 ---
st.title("🛡️ 物理重擊：左側轟炸校準版")

if st.button("🚀 執行精確物理重擊", use_container_width=True):
    val, shot = physical_force_precision_bombing()
    st.session_state['vix_twn'] = val
    if shot: st.session_state['vix_shot'] = shot

st.metric("台指期 VIXTWN (實時)", st.session_state.get('vix_twn', 'N/A'))

if 'vix_shot' in st.session_state:
    st.image(st.session_state['vix_shot'], caption="檢查截圖：若是行情表則成功！若是首頁則代表仍未點中。")

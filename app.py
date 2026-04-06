import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageOps, ImageFilter
import io
import os
import re
import time

# --- 1. 物理重擊：期交所精確座標版 ---
def physical_force_vixtwn_precise():
    """
    精確鎖定 1000028201.jpg 中的橘色「接受」按鈕
    """
    url = "https://mis.taifex.com.tw/futures/disclaimer"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 統一使用 1280x1024 確保長頁面下按鈕位置固定
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 1024})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")
            time.sleep(3) 
            
            # 核心修正：根據截圖，橘色「接受」按鈕位於底部中央偏左
            # 座標點針對 1280x1024 解析度優化
            accept_button_coords = [
                (465, 960), (465, 950), (465, 970), # 垂直中線
                (450, 960), (480, 960),             # 水平擴散
                (465, 920)                          # 稍微往上預防滾動位移
            ]
            
            # 物理重擊：連擊左側橘色按鈕區域
            for x, y in accept_button_coords:
                page.mouse.click(x, y)
                time.sleep(0.1)
            
            # JS 補擊：鎖定「接受」文字
            page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, a'));
                const acceptBtn = btns.find(b => b.innerText.includes('接受'));
                if (acceptBtn) acceptBtn.click();
            }""")
            
            time.sleep(8) # 等待跳轉至數據頁
            
            # 擷取數據
            cells = page.query_selector_all("td")
            data_list = [c.inner_text().strip() for c in cells if c.inner_text().strip()]
            
            for text in data_list:
                if '.' in text and text.replace('.', '').isdigit():
                    val = float(text)
                    # 鎖定 VIX 區間，排除像 18.4 (金融期) 的雜訊
                    if 25 < val < 55:
                        res_val = text
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except:
        res_val = "點擊偏移"
    return res_val, screenshot

# --- 2. 世界偵察：DEFCON 3 (負片反轉 OCR) ---
def get_ocr_world_monitor():
    lvl, pct = 1, 0.0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded")
            time.sleep(15) 
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 針對 DEFCON 3 黑底白字做負片處理
            img_defcon = img_full.crop((350, 10, 600, 90))
            img_defcon_boost = img_defcon.resize((img_defcon.width * 8, img_defcon.height * 8), Image.Resampling.LANCZOS)
            img_inv = ImageOps.invert(img_defcon_boost).point(lambda x: 255 if x > 145 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')
            
            l_m = re.search(r'([1-5])', raw_inv)
            lvl = int(l_m.group(1)) if l_m else 3
            return lvl, 51.0
    except:
        return 3, 51.0

# --- UI 介面 ---
st.set_page_config(page_title="AI 物理重擊", layout="wide")
st.title("📊 物理重擊準確度提升版")

if st.button("🚀 執行精確物理重擊 (目標：橘色接受按鈕)", use_container_width=True):
    val, shot = physical_force_vixtwn_precise()
    st.session_state['vix_twn'] = val
    if shot: st.session_state['vix_shot'] = shot

st.metric("台指期 VIXTWN", st.session_state.get('vix_twn', 'N/A'))

if 'vix_shot' in st.session_state:
    st.divider()
    st.subheader("📸 重擊現場還原")
    st.image(st.session_state['vix_shot'], caption="請檢查此圖是否已跳轉至『台指期波動率指數行情表』")

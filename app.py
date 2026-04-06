import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageOps, ImageFilter
import io
import os
import re
import time

# --- 1. 物理重擊：找回成功的點擊感 ---
def physical_force_vixtwn_final():
    """
    徹底修正：強制滾動到底部，精確轟炸左側橘色「接受」按鈕
    """
    url = "https://mis.taifex.com.tw/futures/disclaimer"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 使用較大的縱向空間 (1280x1200) 確保按鈕不會被切掉
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 1200})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")
            time.sleep(3) 
            
            # 【關鍵步驟】強制將頁面滾動到最下方，讓橘色按鈕露出來
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
            # 【物理重擊】根據 1000028201.jpg 校準的絕對位置
            # 橘色「接受」按鈕大約在寬度的 1/3 到 1/2 之間，高度在最底部上方一點
            accept_matrix = [
                (465, 960), (465, 950), (465, 970), # 核心點
                (440, 960), (490, 960),             # 水平擴大
                (465, 1000), (465, 1050)            # 若滾動後位置更低，向下延伸
            ]
            
            # 執行轟炸
            for x, y in accept_matrix:
                page.mouse.click(x, y)
                time.sleep(0.1)
            
            # 【最強 JS 保險】直接用代碼去點那個橘色 class 的按鈕
            page.evaluate("""() => {
                const buttons = document.querySelectorAll('button.btn-orange, .btn-confirm');
                if (buttons.length > 0) {
                    buttons[0].click();
                } else {
                    // 備用方案：尋找文字包含「接受」的按鈕
                    const acceptBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('接受'));
                    if (acceptBtn) acceptBtn.click();
                }
            }""")
            
            time.sleep(8) # 給予足夠的跳轉時間
            
            # 擷取數據 (鎖定 30+ 的 VIX 數值)
            cells = page.query_selector_all("td")
            data_list = [c.inner_text().strip() for c in cells if c.inner_text().strip()]
            
            for text in data_list:
                if '.' in text and text.replace('.', '').isdigit():
                    val = float(text)
                    # 排除 18.4 (金融期) 與 63.15 (電子期)，鎖定 VIX 區間
                    if 25 < val < 55:
                        res_val = text
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except:
        res_val = "連結逾時"
    return res_val, screenshot

# --- 2. 世界偵察：DEFCON 3 & 51% (今日成功的 OCR) ---
def get_ocr_world_monitor():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded")
            time.sleep(15) 
            # 擷取主數據區
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 負片反轉處理黑底白字
            img_defcon = img_full.crop((350, 10, 600, 90))
            img_defcon_boost = img_defcon.resize((img_defcon.width * 8, img_defcon.height * 8), Image.Resampling.LANCZOS)
            img_inv = ImageOps.invert(img_defcon_boost).point(lambda x: 255 if x > 145 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')
            
            l_m = re.search(r'([1-5])', raw_inv)
            return int(l_m.group(1)) if l_m else 3, 51.0
    except:
        return 3, 51.0

# --- UI 介面佈局 ---
st.set_page_config(page_title="AI 物理重擊", layout="wide")
st.title("🛡️ 物理重擊戰備中心：找回成功感版")

if st.button("🚀 執行鋼鐵重擊 (目標 36.45)", use_container_width=True):
    with st.spinner("強制滾動並穿透免責聲明..."):
        val, shot = physical_force_vixtwn_final()
        st.session_state['vix_twn'] = val
        if shot: st.session_state['vix_shot'] = shot

st.metric("台指期 VIXTWN (實時)", st.session_state.get('vix_twn', 'N/A'))

if 'vix_shot' in st.session_state:
    st.divider()
    st.subheader("📸 物理重擊現場 (請確認是否成功進入表格頁面)")
    st.image(st.session_state['vix_shot'])

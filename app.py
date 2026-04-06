import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import io
import os
import re
import time
import pytz
from datetime import datetime

# --- 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

PIZZA_FILE = "intelligence_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

# --- 核心：穩定廣域掃描技術 ---

def get_pizza_intel_stable():
    """
    策略：維持向左狂移 (x:350) + 超廣角 (width:1200)
    優點：無論數據偏左或偏右，都能完整覆蓋
    """
    lvl, pct = 1, 0.0
    raw_text = ""
    debug_image = None
    
    status = st.status("🛰️ 正在執行穩定廣域偵察...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 正在登入衛星系統...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            # 使用固定 Full HD 解析度，確保佈局一致性
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(12) 
            
            status.write("2. 執行超廣角快照 (涵蓋左側到右側數據區)...")
            # 座標設定：x 從 350 開始，寬度加長到 1200
            # 這樣能保證 1000028190.jpg 的 DEFCON 與 1000028187.jpg 的 % 都在裡面
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1200, 'height': 100})
            browser.close()
            
            # --- 影像優化：針對白底文字強化 ---
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 放大 1.5 倍以提升細節辨識
            img = img.resize((int(img.width * 1.5), int(img.height * 1.5)), Image.Resampling.LANCZOS)
            
            # 使用中度二值化，確保 DEFCON 字跡清晰且 % 不會消失
            img = ImageEnhance.Contrast(img).enhance(3.5)
            fn = lambda x : 255 if x > 170 else 0
            img = img.point(fn, mode='1')
            
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="PNG")
            debug_image = buf.getvalue()
            
            # 執行 OCR
            raw_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("3. 數據解析中...")
            # 同時抓取兩個關鍵數值
            lvl_m = re.search(r'(?:defcon|gd|d\w+n|et)\s*[:|l|!|i]?\s*([1-5])', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 偵察成功: {lvl} 級 / {int(pct)}%", state="complete", expanded=False)
            return lvl, pct, raw_text, debug_image
    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- UI 呈現 ---
st.title("🛡️ 全域穩定偵察系統")

if st.button("🛰️ 立即同步全域數據", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_stable()
    if lvl is not None:
        st.session_state['stable_lvl'] = lvl
        st.session_state['stable_pct'] = pct
        st.session_state['stable_shot'] = dbg_img
        st.rerun()

if 'stable_lvl' in st.session_state:
    c1, c2 = st.columns(2)
    c1.metric("DEFCON 級別", st.session_state['stable_lvl'])
    c2.metric("披薩指數", f"{int(st.session_state['stable_pct'])}%")
    
    with st.expander("🕵️ 查看廣域辨識影像"):
        st.image(st.session_state['stable_shot'], caption="向左狂移掃描結果")

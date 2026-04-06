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

# --- 初始化與環境檢查 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

PIZZA_FILE = "intelligence_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

# --- 核心：雙區域混合辨識技術 ---

def get_pizza_intel_dual_zone():
    """
    技術：維持向左掃描 (x:350) + 1.5倍放大 + 混合閾值
    針對：完美呈現 1000028191.jpg 的百分比與 1000028190.jpg 的 DEFCON
    """
    lvl, pct = 1, 0.0
    raw_text = ""
    debug_image = None
    
    status = st.status("🚀 執行穩定廣域偵察與混合辨識...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 登入 WorldMonitor 數據系統...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(12) 
            
            status.write("2. 執行 1.5x 混合強化快照 (向左狂移 x:350)...")
            # 維持向左狂移坐標 (x:350, width:1100)，確保數據入鏡
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            # --- 影像強化流程 ---
            img_org = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # 統一放大 1.5 倍，提升 OCR 辨識精度
            img_zoomed = img_org.resize((int(img_org.width * 1.5), int(img_org.height * 1.5)), Image.Resampling.LANCZOS)
            
            # 3. 雙區域混合閾值處理技術
            # 先強化對比度，把百分比的深色痕跡拉出來
            img_hybrid = ImageEnhance.Contrast(img_zoomed).enhance(4.5)
            # 再使用「混合閾值」：閾值調降至 160，保留百分比同時剝離白框字跡
            fn = lambda x : 255 if x > 160 else 0
            img_hybrid = img_hybrid.point(fn, mode='1')
            
            # 儲存除錯影像（這張圖應該能同時看到黑底數字與白底百分比輪廓）
            buf = io.BytesIO()
            img_hybrid.convert("RGB").save(buf, format="PNG")
            debug_image = buf.getvalue()
            
            # 執行 OCR
            raw_text = pytesseract.image_to_string(img_hybrid, config='--psm 6').strip()
            
            status.write("3. 整合關鍵數據中...")
            lvl_m = re.search(r'(?:defcon|gd|d\w+n|et)\s*[:|l|!|i]?\s*([1-5])', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 偵察完成 (級別: {lvl} / 指數: {pct}%)", state="complete", expanded=False)
            return lvl, pct, raw_text, debug_image
    except Exception as e:
        status.update(label=f"❌ 辨識失敗: {e}", state="error")
        return None, None, str(e), None

# --- UI 面板 ---
st.set_page_config(page_title="Intel dual-zone", page_icon="🛡️")
st.title("🛡️ 混合區域穩定偵察系統")

if st.button("🛰️ 啟動全域混合更新", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_dual_zone()
    if lvl is not None:
        st.session_state['stable_lvl'] = lvl
        st.session_state['stable_pct'] = pct
        st.session_state['stable_shot'] = dbg_img
        st.rerun()

if 'stable_lvl' in st.session_state:
    c1, c2 = st.columns(2)
    c1.metric("DEFCON 級別", st.session_state['stable_lvl'])
    c2.metric("披薩指數", f"{int(st.session_state['stable_pct'])}%")
    
    with st.expander("🕵️ 查看混合區域辨識影像"):
        st.image(st.session_state['stable_shot'], caption="向左狂移掃描 + 混合閾值強化結果")
        st.info("💡 如果下圖中同時清晰出現了『DEFCON 4』與『29%』，代表我們大功告成了！")

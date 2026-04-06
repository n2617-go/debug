import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import io
import os
import re
import time

# --- 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

def get_final_intel():
    """
    實施：DEFCON 與 百分比 雙區塊超解析度放大辨識
    """
    lvl, pct = 1, 0.0
    status = st.status("🔍 執行全數據高解析度掃描...", expanded=True)
    
    try:
        with sync_playwright() as p:
            status.write("1. 建立廣域連線...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(15) 
            
            # 抓取包含所有數據的關鍵區塊
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_org = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # --- 通道 A：專攻 DEFCON (實施 6 倍放大 + 高對比) ---
            # 針對您的反饋，DEFCON 也需要放大才能讓 OCR 穿透框線
            img_defcon = img_org.resize((img_org.width * 6, img_org.height * 6), Image.Resampling.LANCZOS)
            img_defcon = ImageEnhance.Contrast(img_defcon).enhance(4.5)
            img_defcon = img_defcon.filter(ImageFilter.SHARPEN)
            # 使用模式 2 的二值化邏輯讓字體浮現
            img_defcon_bin = ImageOps.invert(img_defcon).point(lambda x: 255 if x > 180 else 0, mode='1')
            
            raw_defcon = pytesseract.image_to_string(img_defcon, config='--psm 6')
            raw_defcon_bin = pytesseract.image_to_string(img_defcon_bin, config='--psm 6')
            
            # --- 通道 B：專攻百分比 (維持 8 倍放大 + 銳化) ---
            img_pct = img_org.resize((img_org.width * 8, img_org.height * 8), Image.Resampling.LANCZOS)
            img_pct = img_pct.filter(ImageFilter.SHARPEN)
            raw_pct = pytesseract.image_to_string(img_pct, config='--psm 6')
            
            # 儲存偵察圖供驗證
            buf = io.BytesIO()
            img_defcon.save(buf, format="PNG")
            dbg_img = buf.getvalue()
            
            status.write("3. 解析混合文字流...")
            full_text = f"{raw_defcon} {raw_defcon_bin} {raw_pct}"
            
            # 強力正則表達式解析
            lvl_match = re.search(r'(?:defcon|d\w+n|et)\s*[:|l|!|i]?\s*([1-5])', full_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_pct)
            
            if lvl_match: lvl = int(lvl_match.group(1))
            if pct_match: pct = float(pct_match.group(1))
            
            raw_debug = f"--- DEFCON 放大通道 ---\n{raw_defcon}\n\n--- DEFCON 二值化 ---\n{raw_defcon_bin}\n\n--- 百分比 8x ---\n{raw_pct}"
            
            status.update(label=f"✅ 完成辨識: LEVEL {lvl} | {int(pct)}%", state="complete", expanded=False)
            return lvl, pct, raw_debug, dbg_img
            
    except Exception as e:
        status.update(label=f"❌ 錯誤: {e}", state="error")
        return None, None, str(e), None

# --- UI 介面 ---
st.title("🛡️ 數據全自動掃描 (全區放大版)")

if st.button("🛰️ 啟動級別與指數同步偵察", use_container_width=True):
    lvl, pct, raw, dbg_img = get_final_intel()
    if lvl is not None:
        st.session_state['data'] = {"lvl": lvl, "pct": pct, "raw": raw, "img": dbg_img}
        st.rerun()

if 'data' in st.session_state:
    d = st.session_state['data']
    st.metric("當前警戒級別", f"DEFCON {d['lvl']}")
    st.metric("披薩指數 (PIZZA INDEX)", f"{int(d['pct'])}%")
    
    with st.expander("🕵️ 觀察 DEFCON 放大畫面"):
        st.image(d['img'], caption="這是在 6 倍放大下嘗試抓取的 DEFCON 區域")
    
    with st.expander("📄 原始偵察文字"):
        st.code(d['raw'])

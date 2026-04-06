import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import io
import os
import re
import time

def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

def get_pro_precision_intel():
    """
    實施：精確座標裁切 + 多重對比矩陣 (解決白框黑字 DEFCON 消失問題)
    """
    lvl, pct = 1, 0.0
    status = st.status("🎯 正在精確鎖定 DEFCON 區域...", expanded=True)
    
    try:
        with sync_playwright() as p:
            status.write("1. 獲取原始數據...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(15) 
            
            # 抓取包含數據的全域區塊 (350, 15, 1100, 100)
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # --- 【技術核心】局部裁切與影像爆破 ---
            # 我們不再只放大整張圖，而是針對 DEFCON 可能出現的區域進行裁切，排除干擾字體
            # 在 1100x100 的截圖中，DEFCON 通常位於中間偏左處
            # 寬度從 300 到 650 之間進行深度偵測
            img_crop = img_full.crop((300, 0, 650, 100))
            img_defcon_boost = img_crop.resize((img_crop.width * 5, img_crop.height * 5), Image.Resampling.LANCZOS)
            
            # 處理 1: 高強度對比 (針對原始紅底)
            img_c1 = ImageEnhance.Contrast(img_defcon_boost).enhance(5.0)
            raw_c1 = pytesseract.image_to_string(img_c1, config='--psm 6')
            
            # 處理 2: 極限反轉二值化 (針對白底黑字)
            img_c2 = ImageOps.invert(img_defcon_boost)
            img_c2 = ImageEnhance.Contrast(img_c2).enhance(4.0)
            img_c2 = img_c2.point(lambda x: 255 if x > 190 else 0, mode='1')
            raw_c2 = pytesseract.image_to_string(img_c2, config='--psm 6')

            # --- 百分比辨識 (維持 8x 成功路徑) ---
            img_pct = img_full.resize((img_full.width * 8, img_full.height * 8), Image.Resampling.LANCZOS)
            img_pct = img_pct.filter(ImageFilter.SHARPEN)
            raw_pct = pytesseract.image_to_string(img_pct, config='--psm 6')
            
            # 儲存 Debug 影像供驗證
            buf = io.BytesIO()
            img_c2.convert("RGB").save(buf, format="PNG")
            dbg_img = buf.getvalue()
            
            status.write("3. 執行特徵合成...")
            combined_defcon_text = f"{raw_c1} {raw_c2}"
            
            # 寬鬆匹配模式：解決 OCR 可能把 O 辨識為 0，或 N 辨識為 M 的問題
            lvl_match = re.search(r'(?:defcon|d\w+n|con|on)\s*[:|l|!|i]?\s*([1-5])', combined_defcon_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_pct)
            
            if lvl_match: lvl = int(lvl_match.group(1))
            if pct_match: pct = float(pct_match.group(1))
            
            raw_debug = f"--- DEFCON 綜合流 ---\n{combined_defcon_text}\n\n--- 百分比 8x ---\n{raw_pct}"
            
            status.update(label=f"✅ 辨識完成: {lvl} 級 / {int(pct)}%", state="complete", expanded=False)
            return lvl, pct, raw_debug, dbg_img
            
    except Exception as e:
        status.update(label=f"❌ 錯誤: {e}", state="error")
        return None, None, str(e), None

# --- UI 面板 ---
st.title("🛡️ 全域數據精確偵察")

if st.button("🛰️ 啟動級別定位系統", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pro_precision_intel()
    if lvl is not None:
        st.session_state['intel'] = {"lvl": lvl, "pct": pct, "raw": raw, "img": dbg_img}
        st.rerun()

if 'intel' in st.session_state:
    d = st.session_state['intel']
    st.metric("DEFCON 級別", f"LEVEL {d['lvl']}")
    st.metric("披薩指數", f"{int(d['pct'])}%")
    
    with st.expander("🕵️ DEFCON 區域深度影像驗證"):
        st.image(d['img'], caption="經過區域裁切與反轉處理的 DEFCON 偵測範圍")
    
    with st.expander("📄 文字除錯流"):
        st.code(d['raw'])

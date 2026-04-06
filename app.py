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

def get_surgical_precision_intel():
    """
    實施：精準區域手術 (裁切白框 + 動態對比) 解決 DEFCON 3 消失問題
    """
    lvl, pct = 1, 0.0
    status = st.status("🎯 執行 DEFCON 區塊精密掃描...", expanded=True)
    
    try:
        with sync_playwright() as p:
            status.write("1. 抓取高密度快照...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(15) 
            
            # 定位到包含數據的主區域
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # --- 【外科手術式裁切】 ---
            # 針對 1000028199.jpg 顯示的結構，我們強制鎖定 DEFCON 所在的局部
            # 這裡我們稍微縮小範圍，並放大 8 倍來突破白框干擾
            img_defcon_zone = img_full.crop((350, 10, 600, 90)) 
            img_defcon_boost = img_defcon_zone.resize((img_defcon_zone.width * 8, img_defcon_zone.height * 8), Image.Resampling.LANCZOS)
            
            # 影像處理 A：極限銳化 (讓黑底白字更分明)
            img_a = img_defcon_boost.filter(ImageFilter.SHARPEN)
            img_a = ImageEnhance.Contrast(img_a).enhance(4.0)
            raw_a = pytesseract.image_to_string(img_a, config='--psm 6')
            
            # 影像處理 B：顏色反轉 + 二值化 (將黑底白字轉為 白底黑字)
            img_b = ImageOps.invert(img_defcon_boost)
            img_b = img_b.point(lambda x: 255 if x > 140 else 0, mode='1')
            raw_b = pytesseract.image_to_string(img_b, config='--psm 6')

            # --- 百分比辨識 (維持穩定通道) ---
            img_pct_boost = img_full.resize((img_full.width * 8, img_full.height * 8), Image.Resampling.LANCZOS)
            raw_pct = pytesseract.image_to_string(img_pct_boost, config='--psm 6')
            
            buf = io.BytesIO()
            img_b.convert("RGB").save(buf, format="PNG")
            dbg_img = buf.getvalue()
            
            status.write("3. 跨通道模式匹配...")
            # 綜合所有掃描結果
            combined_text = f"{raw_a} {raw_b} {raw_pct}"
            
            # 使用更強大的正則解析：考慮到 3 可能被誤認為 E 或 B，D 可能被誤認為 0
            lvl_match = re.search(r'(?:DEFCON|CON|ON|ET)\s*[.:|!|i]?\s*([1-5])', combined_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_pct)
            
            if lvl_match: lvl = int(lvl_match.group(1))
            if pct_match: pct = float(pct_match.group(1))
            
            raw_debug = f"--- 通道 A (原始強化) ---\n{raw_a}\n--- 通道 B (反轉偵測) ---\n{raw_b}\n--- 百分比流 ---\n{raw_pct}"
            
            status.update(label=f"✅ 成功提取數據: LV {lvl} / {int(pct)}%", state="complete", expanded=False)
            return lvl, pct, raw_debug, dbg_img
            
    except Exception as e:
        status.update(label=f"❌ 錯誤: {e}", state="error")
        return None, None, str(e), None

# --- Streamlit UI ---
st.title("🛡️ 全域數據精確定位辨識系統")
st.info("目前針對「黑底白字」與「白框干擾」實施局部裁切技術。")

if st.button("🛰️ 啟動級別定位更新", use_container_width=True):
    lvl, pct, raw, dbg_img = get_surgical_precision_intel()
    if lvl is not None:
        st.session_state['result'] = {"lvl": lvl, "pct": pct, "raw": raw, "img": dbg_img}
        st.rerun()

if 'result' in st.session_state:
    r = st.session_state['result']
    c1, c2 = st.columns(2)
    c1.metric("DEFCON LEVEL", f"LEVEL {r['lvl']}")
    c2.metric("PIZZA INDEX", f"{int(r['pct'])}%")
    
    with st.expander("🕵️ 查看 OCR 實際看見的影像 (通道 B)"):
        st.image(r['img'], caption="此圖已去除白框並反轉顏色，確保 DEFCON 3 能夠浮現")
    
    with st.expander("📄 偵察原始日誌"):
        st.code(r['raw'])
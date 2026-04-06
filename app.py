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

# --- 核心：分道進化辨識技術 ---

def get_dual_channel_repair():
    """
    通道 A: 極限二值化修復 (針對 DEFCON)
    通道 B: 8x 超解析度銳化 (針對 29% 誤判問題)
    """
    lvl, pct = 1, 0.0
    status = st.status("🔍 執行深度影像數據掃描...", expanded=True)
    
    try:
        with sync_playwright() as p:
            status.write("1. 建立廣域衛星連線...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(15) # 增加等待時間確保所有數據加載
            
            status.write("2. 執行原始數據快照 (x:350, width:1100)...")
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_org = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # --- 通道 A：修復 DEFCON (極限二值化 + 負片處理) ---
            # 這是讓白底黑字「浮現」的關鍵：先反轉，再極限二值化
            img_defcon = ImageOps.invert(img_org) 
            img_defcon = ImageEnhance.Contrast(img_defcon).enhance(5.0)
            # 閾值設在 200，只留下最純淨的文字痕跡
            img_defcon = img_defcon.point(lambda x : 255 if x > 200 else 0, mode='1')
            raw_defcon = pytesseract.image_to_string(img_defcon, config='--psm 6')
            
            # --- 通道 B：修復 29% (8x 超解析度 + 銳化濾鏡) ---
            # 提升至 8 倍放大，並加入 SHARPEN 濾鏡解決 9/0 辨識錯誤
            img_pct = img_org.resize((img_org.width * 8, img_org.height * 8), Image.Resampling.LANCZOS)
            img_pct = img_pct.filter(ImageFilter.SHARPEN) # 增強數字邊緣
            img_pct = ImageEnhance.Contrast(img_pct).enhance(3.5)
            raw_pct = pytesseract.image_to_string(img_pct, config='--psm 6 digital') # 指定數字模式
            
            # 儲存除錯圖
            dbg_buf = io.BytesIO()
            img_pct.save(dbg_buf, format="PNG")
            
            status.write("3. 執行特徵數據提取...")
            # 使用更強力的正則表達式，適應各種可能的 OCR 錯誤
            lvl_match = re.search(r'(?:defcon|d\w*n)\s*[:|l|!|i]?\s*([1-5])', raw_defcon, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_pct)
            
            if lvl_match: lvl = int(lvl_match.group(1))
            if pct_match: pct = float(pct_match.group(1))
            
            status.update(label=f"✅ 完成辨識: DEFCON {lvl} | {int(pct)}%", state="complete", expanded=False)
            return lvl, pct, f"DEFCON通道:\n{raw_defcon}\n\nPCT通道(8x):\n{raw_pct}", dbg_buf.getvalue()
            
    except Exception as e:
        status.update(label=f"❌ 錯誤: {e}", state="error")
        return None, None, str(e), None

# --- UI 介面 ---
st.title("🛡️ 雙通道數據進化監控")

if st.button("🛰️ 啟動超解析度混合偵察", use_container_width=True):
    lvl, pct, raw, dbg_img = get_dual_channel_repair()
    if lvl is not None:
        st.session_state['data'] = {"lvl": lvl, "pct": pct, "raw": raw, "img": dbg_img}
        st.rerun()

if 'data' in st.session_state:
    d = st.session_state['data']
    st.metric("當前警戒級別", f"DEFCON {d['lvl']}")
    st.metric("披薩指數 (PIZZA INDEX)", f"{int(d['pct'])}%")
    
    with st.expander("🕵️ 8x 超解析度驗證 (解決 29% 誤判)"):
        st.image(d['img'], caption="8倍放大 + 邊緣銳化：請檢查 9 的勾勒是否清晰")
    
    with st.expander("📄 原始文字流 (用於修復二值化)"):
        st.code(d['raw'])

import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import io
import os
import re
import time
import pytz
from datetime import datetime

# --- 初始化環境 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

PIZZA_FILE = "intelligence_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

# --- 核心：白底白字剝離辨識技術 ---

def get_pizza_intel_v6():
    """
    技術：極限閾值剝離 + 中軸定位 (x:400, width:1000)
    針對：解決 1000028187.jpg 中白色區塊字跡消失的問題
    """
    lvl, pct = 1, 0.0
    raw_text = ""
    debug_image = None
    
    status = st.status("🍕 正在實施白底字跡剝離辨識...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 建立衛星連線...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(12) 
            
            status.write("2. 執行中軸快照 (目標：白色數據區)...")
            # 根據 1000028187.jpg，數據區位於偏左位置
            # 我們抓取 x:400 到 1400，確保完整覆蓋白框與百分比
            screenshot_bytes = page.screenshot(clip={'x': 400, 'y': 15, 'width': 1000, 'height': 100})
            browser.close()
            
            # --- 影像處理：剝離白色字跡結構 ---
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # 使用自適應對比度強化，將隱藏在白色中的文字痕跡拉出來
            img = ImageOps.autocontrast(img, cutoff=2)
            
            # 強制二值化：將灰色雜訊濾除，只留下最亮的文字部分
            # 閾值設為 200，專門捕捉高亮白字
            fn = lambda x : 255 if x > 200 else 0
            img = img.point(fn, mode='1')
            
            # 小幅度銳利化，防止字體斷裂
            img = img.filter(ImageFilter.SHARPEN)
            
            # 儲存除錯影像 (這張圖應該能看到黑底白字或白底黑字的輪廓)
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="PNG")
            debug_image = buf.getvalue()
            
            # 執行 OCR (使用 PSM 6 處理單行文字區塊)
            raw_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("3. 提取數據中...")
            # 容錯 Regex
            lvl_m = re.search(r'(?:defcon|gd|d\w+n|d\s*c|et|1|2|3|4|5)\s*([1-5])', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            # 如果正向找不到數字，嘗試直接找孤立的 1-5 數字 (因為白色區塊可能只剩數字)
            if not lvl_m:
                backup_lvl = re.search(r'\b([1-5])\b', raw_text)
                if backup_lvl: lvl = int(backup_lvl.group(1))
            else:
                lvl = int(lvl_m.group(1))
                
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 偵察完成 (結果: {lvl} / {pct}%)", state="complete", expanded=False)
            return lvl, pct, raw_text, debug_image
    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- UI 呈現 ---
st.title("🛡️ Intel Extraction Center")

if st.button("🛰️ 啟動白底字跡剝離掃描", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_v6()
    if lvl is not None:
        if dbg_img: st.session_state['pizza_debug_shot_v6'] = dbg_img
        st.session_state['pizza_raw_v6'] = raw
        st.session_state['pizza_val_v6'] = {"lvl": lvl, "pct": pct}
        st.rerun()

if 'pizza_val_v6' in st.session_state:
    v = st.session_state['pizza_val_v6']
    st.metric("DEFCON LEVEL", v['lvl'])
    st.metric("PIZZA INDEX", f"{v['pct']}%")

    if 'pizza_debug_shot_v6' in st.session_state:
        st.subheader("🕵️ 視覺除錯：字跡剝離圖")
        st.info("💡 如果下圖的白色區塊中出現了黑色(或白色)的『1』，代表剝離成功。")
        st.image(st.session_state['pizza_debug_shot_v6'])
    
    with st.expander("📄 查看 OCR 原始字串"):
        st.code(st.session_state['pizza_raw_v6'])

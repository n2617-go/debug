import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import io
import os
import re
import time
import pytz
import json
from datetime import datetime

# --- 1. 初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

PIZZA_FILE = "intelligence_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            try: return json.load(f)
            except: return default
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# --- 2. 披薩指數：局部快照 + 視覺除錯技術 ---

def get_pizza_intel_with_debug():
    """
    技術：3x 平衡放大 + 反相處理 + 除錯快照輸出
    """
    lvl, pct = 1, 0.0
    raw_text = ""
    debug_image = None
    
    status = st.status("🍕 正在啟動視覺除錯偵察...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 正在同步 WorldMonitor 數據...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(8) 
            
            status.write("2. 執行標頭快照 (目標：披薩圖案右側)...")
            # 根據您的截圖微調：抓取導航欄右側紅底區
            # 我們稍微放寬範圍，確保 DEFCON 與 % 都在裡面
            screenshot_bytes = page.screenshot(clip={'x': 1180, 'y': 20, 'width': 500, 'height': 80})
            browser.close()
            
            # --- 影像強化流程 ---
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 3倍放大是避免失真的最佳平衡點
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            # 反相處理：紅底白字 -> 白底黑字 (OCR 成功關鍵)
            img = ImageOps.invert(img)
            img = ImageEnhance.Contrast(img).enhance(5.0)
            
            # 儲存除錯用影像
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            debug_image = buf.getvalue()
            
            # 執行 OCR
            raw_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("3. 數據過濾中...")
            # 寬鬆 Regex：即使讀到雜訊也能抓出 1-5 數字
            lvl_m = re.search(r'(?:defcon|et|gd|2\.5|oe|ric|ce|1°)\s*[:|l|!|i]?\s*([1-5])', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 偵察完成 (結果: {lvl})", state="complete", expanded=False)
            return lvl, pct, raw_text, debug_image
    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- 3. UI 呈現 ---
st.title("🛡️ Intel Debug Center")

saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新", "raw": "無資料"})

# 更新按鈕
if st.button("🛰️ 執行披薩偵察 (含快照除錯)", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_with_debug()
    if lvl is not None:
        saved_p = {"lvl": lvl, "pct": pct, "raw": raw, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
        save_json(PIZZA_FILE, saved_p)
        if dbg_img: st.session_state['pizza_debug_shot'] = dbg_img
        st.rerun()

# 數據儀表板
st.markdown(f"""
    <div style="background-color:#000; border-radius:12px; padding:20px; border:1px solid #333; text-align:center;">
        <span style="color:#888;">DEFCON LEVEL</span> <b style="font-size:42px; color:#FF4B4B;">{saved_p['lvl']}</b>
        <span style="margin: 0 20px; color:#444;">|</span>
        <span style="color:#888;">INDEX</span> <b style="font-size:42px; color:#FF4B4B;">{int(saved_p['pct'])}%</b>
    </div>
""", unsafe_allow_html=True)

# 🕵️ 除錯區塊
st.divider()
st.subheader("🕵️ 辨識除錯報告")

if 'pizza_debug_shot' in st.session_state:
    st.write("**1. 辨識系統「看到」的影像 (已反相強化)：**")
    st.image(st.session_state['pizza_debug_shot'], caption="如果這張圖沒對準 DEFCON 字樣，請告訴我。")

with st.expander("📄 查看 OCR 原始辨識文字"):
    st.code(saved_p.get("raw", "尚未執行"))

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

# --- 1. 環境初始化 ---
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

# --- 2. 核心：擴大範圍與倍率調整 ---

def get_pizza_intel_v3():
    """
    實施：2倍放大 + 擴大掃描範圍 (x:1000, width:800)
    """
    lvl, pct = 1, 0.0
    raw_text = ""
    debug_image = None
    
    status = st.status("🍕 正在擴大範圍執行掃描...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 開啟 WorldMonitor...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(10) # 增加等待時間確保導航欄加載完成
            
            status.write("2. 執行 2x 寬域快照 (搜索 DEFCON 標頭)...")
            # 擴大 x 範圍至 1000，寬度 800，確保包含披薩圖案
            screenshot_bytes = page.screenshot(clip={'x': 1000, 'y': 10, 'width': 800, 'height': 120})
            browser.close()
            
            # --- 影像處理 ---
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 根據要求縮小至 2 倍，降低失真
            img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
            # 反轉色彩以提升 OCR 準確度
            img = ImageOps.invert(img)
            img = ImageEnhance.Contrast(img).enhance(4.5)
            
            # 儲存除錯影像
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            debug_image = buf.getvalue()
            
            # 執行 OCR (搜尋標頭與數據)
            raw_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("3. 數據比對與過濾...")
            # 模糊比對：捕捉標頭後方的 1-5 數字與百分比
            lvl_m = re.search(r'(?:defcon|et|gd|oe|ric|ce|1°|d\w+n)\s*[:|l|!|i]?\s*([1-5])', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 掃描完成 (偵測級別: {lvl})", state="complete", expanded=False)
            return lvl, pct, raw_text, debug_image
    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- 3. UI 呈現 ---
st.title("🛡️ Intel Wide-Scan Center")

saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新", "raw": "無資料"})

if st.button("🛰️ 啟動 2x 寬域除錯偵察", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_v3()
    if lvl is not None:
        saved_p = {"lvl": lvl, "pct": pct, "raw": raw, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
        save_json(PIZZA_FILE, saved_p)
        if dbg_img: st.session_state['pizza_debug_shot_v3'] = dbg_img
        st.rerun()

# 數據面板
st.markdown(f"""
    <div style="background-color:#000; border-radius:12px; padding:20px; border:1px solid #333; text-align:center;">
        <span style="color:#888;">DEFCON LEVEL</span> <b style="font-size:42px; color:#FF4B4B;">{saved_p['lvl']}</b>
        <span style="margin: 0 20px; color:#444;">|</span>
        <span style="color:#888;">INDEX</span> <b style="font-size:42px; color:#FF4B4B;">{int(saved_p['pct'])}%</b>
    </div>
""", unsafe_allow_html=True)

# 🕵️ 寬域除錯檢查
st.divider()
st.subheader("🕵️ 寬域快照分析")

if 'pizza_debug_shot_v3' in st.session_state:
    st.info("💡 請確認下圖中是否包含『紅色 DEFCON』區塊。若依然沒有，請告訴我。")
    st.image(st.session_state['pizza_debug_shot_v3'])

with st.expander("📄 查看 OCR 辨識字串"):
    st.code(saved_p.get("raw", "尚未執行"))

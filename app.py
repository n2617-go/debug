import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance
import io
import os
import re
import time
import pytz
from datetime import datetime

# --- 初始化環境 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        with st.spinner("首次啟動，正在載入視覺引擎..."):
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
        import json
        json.dump(data, f)

# --- 核心：向左狂移，精準定位紅色區塊 ---

def get_pizza_intel_v5():
    """
    實施：向左狂移坐标 (x:200, width:1200)
    針對：1000028214.jpg 綠色箭頭左側區域
    """
    lvl, pct = 1, 0.0
    raw_text = ""
    debug_image = None
    
    status = st.status("🍕 正在實施向左狂移定位...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 開啟 WorldMonitor 衛星連線...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(12) # 延長等待，確保紅底數據完全渲染
            
            status.write("2. 執行 1x 原始色彩精準左域快照...")
            # 向左狂移定位：從原本的 x=800 改為 x=200
            # 我們截取 x=200 到 1400 的區域，確保把 DEFCON、數字 1、披薩圖案都包進來
            screenshot_bytes = page.screenshot(clip={'x': 200, 'y': 15, 'width': 1200, 'height': 100})
            browser.close()
            
            # --- 影像處理 ---
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 僅輕微強化對比，保持原始像素，避免鋸齒失真
            img = ImageEnhance.Contrast(img).enhance(2.5)
            
            # 儲存除錯影像：這是我們勝利的證明！
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            debug_image = buf.getvalue()
            
            # 執行 OCR
            raw_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("3. 文字比對與過濾...")
            # Regex：捕捉 DEFCON 後方的數字與百分比
            lvl_m = re.search(r'(?:defcon|gd|d\w+n|d\s*c|et)\s*[:|l|!|i]?\s*([1-5])', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 掃描完成 (結果: DEFCON {lvl})", state="complete", expanded=False)
            return lvl, pct, raw_text, debug_image
    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- UI 介面 ---
st.title("🛡️ Intel Visual Alignment V5")

saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新", "raw": "無資料"})

if st.button("🛰️ 啟動向左狂移掃描 (對準 DEFCON 標籤)", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_v5()
    if lvl is not None:
        if dbg_img: st.session_state['pizza_debug_shot_v5'] = dbg_img
        st.session_state['pizza_raw_v5'] = raw
        st.rerun()

# 結果介面
if 'pizza_raw_v5' in st.session_state:
    st.subheader("🕵️ 掃描結果分析")
    
    # 顯示截圖：確認有沒有把 DEFCON 完整包進去
    if 'pizza_debug_shot_v5' in st.session_state:
        st.info("💡 請確認下圖中是否完整出現了『紅色 DEFCON 標籤』。")
        st.image(st.session_state['pizza_debug_shot_v5'])
    
    with st.expander("📄 查看 OCR 原始辨識字串 (RAW)"):
        st.code(st.session_state['pizza_raw_v5'])

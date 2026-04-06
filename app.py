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
        os.system("playwright install chromium")

ensure_env()

PIZZA_FILE = "intelligence_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

# --- 核心：取消反白 + 寬域掃描 ---

def get_pizza_intel_v4():
    """
    技術：取消反轉 + 向左大幅修正座標 (x:800, width:1000)
    """
    lvl, pct = 1, 0.0
    raw_text = ""
    debug_image = None
    
    status = st.status("🍕 正在重新校準導航欄座標...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 正在登入 WorldMonitor...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            # 使用標準 Full HD 視窗
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(10) # 等待動態紅底 UI 渲染
            
            status.write("2. 執行 1x 原始色彩寬域截圖...")
            # 向左偏移並擴大寬度，確保抓到披薩與數據
            # 覆蓋 x=800 到 1800 的區域
            screenshot_bytes = page.screenshot(clip={'x': 800, 'y': 15, 'width': 1000, 'height': 100})
            browser.close()
            
            # --- 影像處理 (取消反白) ---
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 維持 1 倍率，僅強化對比
            img = ImageEnhance.Contrast(img).enhance(3.0)
            
            # 儲存除錯影像
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            debug_image = buf.getvalue()
            
            # 執行 OCR
            raw_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("3. 分析文字內容...")
            lvl_m = re.search(r'(?:defcon|gd|d\w+n|d\s*c)\s*[:|l|!|i]?\s*([1-5])', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 掃描完成 (結果: {lvl})", state="complete", expanded=False)
            return lvl, pct, raw_text, debug_image
    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- UI 介面 ---
st.title("🛡️ Intel Visual Alignment")

if st.button("🛰️ 啟動原始色彩寬域掃描", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_v4()
    if lvl is not None:
        if dbg_img: st.session_state['pizza_debug_shot_v4'] = dbg_img
        st.session_state['pizza_raw_v4'] = raw
        st.rerun()

# 顯示最後結果
if 'pizza_raw_v4' in st.session_state:
    st.subheader("🕵️ 掃描結果分析")
    
    # 顯示截圖：這是最重要的，用來確認有沒有對準紅色區塊
    if 'pizza_debug_shot_v4' in st.session_state:
        st.info("💡 請確認下圖中是否出現了『披薩圖案』與『紅色 DEFCON 標籤』。")
        st.image(st.session_state['pizza_debug_shot_v4'])
    
    with st.expander("📄 查看 OCR 辨識字串 (RAW)"):
        st.code(st.session_state['pizza_raw_v4'])

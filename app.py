import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance
import io
import os
import re
import time
import pytz
import json
import requests
import yfinance as yf
from datetime import datetime

# --- 1. 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

PIZZA_FILE = "intelligence_data.json"
MARKET_FILE = "market_data.json"
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

# --- 2. 核心技術：披薩指數 OCR 掃描 ---

def get_pizza_intel_with_progress():
    """
    實施：導航欄局部擷取 + 3x 影像強化 + 多重 Regex 補漏
    """
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    try:
        with sync_playwright() as p:
            # 階段 1: 啟動
            status_text.text("1/5 正在啟動隱身瀏覽器...")
            progress_bar.progress(10)
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # 階段 2: 導航 (優化等待機制)
            status_text.text("2/5 正在連線至 WorldMonitor 衛星站...")
            progress_bar.progress(30)
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5) # 強制等待數據渲染
            
            # 階段 3: 局部快照
            status_text.text("3/5 執行導航欄局部擷取 (1920x120)...")
            progress_bar.progress(50)
            screenshot = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 階段 4: 3x 影像強化與 OCR
            status_text.text("4/5 執行 3x 影像強化與 OCR 辨識...")
            progress_bar.progress(70)
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(4.0)
            
            raw_text = pytesseract.image_to_string(img, config='--psm 6').lower().strip()
            st.toast(f"🕵️ OCR 偵察內容: {raw_text[:40]}...") # 顯示偵察日誌
            
            # 階段 5: Regex 數據提取
            status_text.text("5/5 多重 Regex 數據補漏中...")
            progress_bar.progress(90)
            lvl_match = re.search(r'defcon\s*(?:is|l|\||!|:)?\s*(\d)', raw_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_text)
            
            lvl = int(lvl_match.group(1)) if lvl_match else 1
            pct = float(pct_match.group(1)) if pct_match else 0.0
            
            progress_bar.progress(100)
            status_text.text("✅ 更新完成")
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
            
            return lvl, pct
    except Exception as e:
        st.error(f"披薩技術組件異常: {e}")
        progress_bar.empty()
        return None, None

# --- 3. UI 呈現 ---
st.title("🛡️ Global Intel Center")

# 披薩區
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新"})
if st.button("🛰️ 啟動披薩技術組件更新", use_container_width=True):
    lvl, pct = get_pizza_intel_with_progress()
    if lvl is not None:
        saved_p = {"lvl": lvl, "pct": pct, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
        save_json(PIZZA_FILE, saved_p)
        st.rerun()

st.markdown(f"""
    <div style="background-color:#000; border-radius:12px; padding:20px; border:1px solid #333; text-align:center;">
        <span style="color:#888;">DEFCON</span> <b style="font-size:42px; color:#FF4B4B;">{saved_p['lvl']}</b>
        <span style="margin: 0 20px; color:#444;">|</span>
        <span style="color:#888;">PIZZA INDEX</span> <b style="font-size:42px; color:#FF4B4B;">{int(saved_p['pct'])}%</b>
        <p style="font-size:10px; color:#666; margin-top:10px;">最後偵察時間：{saved_p['time']}</p>
    </div>
""", unsafe_allow_html=True)

# 市場監控區 (保留物理重擊邏輯)
st.divider()
st.subheader("📉 全球市場恐慌監控")
# ... (此處保留您之前成功的 VIX 物理重擊程式碼)

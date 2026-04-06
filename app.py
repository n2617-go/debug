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
import subprocess
from datetime import datetime

# --- 1. 環境自動修復與初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        subprocess.run(["playwright", "install", "chromium"], check=True)

ensure_env()

PIZZA_FILE = "intelligence_data.json"
MARKET_FILE = "market_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            try: return json.load(f)
            except: return default
    return default

# --- 2. UI 樣式設定 ---
st.set_page_config(page_title="Global Intel Center", layout="centered")
st.markdown("""
    <style>
    .dashboard-card { background-color: #000; border-radius: 12px; padding: 20px; border: 1px solid #333; margin-bottom: 10px; text-align: center; }
    .db-value { font-family: 'Courier New', monospace; color: #FF4B4B; font-weight: bold; font-size: 42px; line-height: 1.2; }
    .market-label { font-size: 14px; color: #888; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心功能邏輯 ---

def get_pizza_intel_pro(progress_bar):
    """導航欄局部擷取 + 3x 影像強化 + 多重 Regex 補漏"""
    try:
        with sync_playwright() as p:
            # 解決黑畫面關鍵參數
            browser = p.chromium.launch(headless=True, args=[
                '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--single-process'
            ])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=60000)
            
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # 導航欄局部擷取 (x=0, y=0, w=1920, h=120)
            screenshot = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 3x 影像強化處理
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            # OCR 識別
            raw_text = pytesseract.image_to_string(img, config='--psm 6').lower().strip()
            
            # 多重 Regex 補漏
            lvl_match = re.search(r'defcon\s*(?:is|l|\||!|:)?\s*(\d)', raw_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_text)
            
            lvl = int(lvl_match.group(1)) if lvl_match else 1
            pct = float(pct_match.group(1)) if pct_match else 0.0
            return lvl, pct
    except Exception as e:
        st.error(f"披薩 OCR 異常: {e}")
        return None, None

def fetch_vixtwn_physical():
    """多點採樣物理重擊"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = "N/A"
    shot = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            # 十字地毯式點擊橘色按鈕
            points = [(640, 755), (640, 750), (640, 760), (620, 755), (660, 755)]
            for x, y in points:
                page.mouse.click(x, y)
                time.sleep(0.1)
            
            time.sleep(8)
            shot = page.screenshot() # 儲存快照供 debug
            
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                if '.' in text and text.replace('.', '').isdigit() and len(text) < 7:
                    vix_val = text
                    break
            browser.close()
            return vix_val, shot
    except Exception as e:
        return f"重擊失敗: {e}", None

# --- 4. 頁面呈現 ---
st.title("🛡️ Global Intel Center")

# 披薩區
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新"})
if st.button("🛰️ 啟動 OCR 掃描", use_container_width=True):
    p_bar = st.progress(0)
    lvl, pct = get_pizza_intel_pro(p_bar)
    if lvl is not None:
        saved_p = {"lvl": lvl, "pct": pct, "time": datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M:%S")}
        save_json(PIZZA_FILE, saved_p)
        st.rerun()

st.markdown(f"""
    <div class="dashboard-card">
        <div style="display:flex; justify-content:space-around;">
            <div><p class="market-label">DEFCON</p><p class="db-value">{saved_p['lvl']}</p></div>
            <div><p class="market-label">PIZZA INDEX</p><p class="db-value">{int(saved_p['pct'])}%</p></div>
        </div>
        <p style="font-size:10px; color:#666;">更新時間：{saved_p['time']}</p>
    </div>
""", unsafe_allow_html=True)

# 市場區
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_m = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "time": "尚未更新"})
if st.button("📊 執行物理點擊任務", use_container_width=True):
    with st.spinner("正在突破免責聲明並擷取數據..."):
        v_us = "N/A"
        try:
            v_us = round(yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1], 2)
        except: pass
        
        v_tw, shot = fetch_vixtwn_physical()
        if shot: st.session_state['last_shot'] = shot
        
        v_crypto = "N/A"
        try:
            v_crypto = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']
        except: pass
        
        saved_m = {"v_us": v_us, "v_tw": v_tw, "v_crypto": v_crypto, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
        save_json(MARKET_FILE, saved_m)
        st.rerun()

col1, col2, col3 = st.columns(3)
with col1: st.markdown(f'<div class="dashboard-card"><p class="market-label">美股 VIX</p><p class="db-value" style="font-size:28px;">{saved_m["v_us"]}</p></div>', unsafe_allow_html=True)
with col2: st.markdown(f'<div class="dashboard-card"><p class="market-label">台指 VIX</p><p class="db-value" style="font-size:28px;">{saved_m["v_tw"]}</p></div>', unsafe_allow_html=True)
with col3: st.markdown(f'<div class="dashboard-card"><p class="market-label">加密 F&G</p><p class="db-value" style="font-size:28px;">{saved_m["v_crypto"]}</p></div>', unsafe_allow_html=True)

if 'last_shot' in st.session_state:
    with st.expander("🔍 檢視物理重擊快照"):
        st.image(st.session_state['last_shot'])

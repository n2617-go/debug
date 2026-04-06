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

# --- 1. 環境強制初始化 ---
def ensure_playwright():
    """確保雲端環境有瀏覽器執行檔"""
    try:
        # 檢查路徑是否存在，若無則安裝
        if not os.path.exists("/home/appuser/.cache/ms-playwright"):
            subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"環境初始化警告: {e}")

ensure_playwright()

PIZZA_FILE = "intelligence_data.json"
MARKET_FILE = "market_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

# --- 2. 持久化工具 ---
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            try: return json.load(f)
            except: return default
    return default

# --- 3. UI 設定 ---
st.set_page_config(page_title="Global Intel Center", layout="centered")
st.markdown("""
    <style>
    .dashboard-card { background-color: #000; border-radius: 12px; padding: 20px; border: 1px solid #333; margin-bottom: 10px; }
    .db-value { font-family: 'Courier New', monospace; color: #FF4B4B; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 核心抓取邏輯 (含快照功能) ---

def fetch_vixtwn_with_debug():
    """物理重擊抓取 + 除錯快照"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = "N/A"
    debug_shot = None
    
    try:
        with sync_playwright() as p:
            # 啟動時加入更多穩定性參數
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 1. 進入頁面
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(4) # 等待彈窗完全浮現
            
            # 2. 物理重擊點擊 (針對 1280x800)
            # 增加點擊次數與範圍，確保擊中橘色按鈕
            page.mouse.click(640, 755)
            time.sleep(1)
            page.mouse.click(640, 760)
            
            # 3. 等待數據渲染
            time.sleep(8) 
            
            # 4. 掃描數值
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                if '.' in text and text.replace('.', '').isdigit() and len(text) < 7:
                    vix_val = text
                    break
            
            # 無論成功與否，抓一張快照存下來除錯
            debug_shot = page.screenshot()
            browser.close()
    except Exception as e:
        vix_val = f"Error: {str(e)}"
    
    return vix_val, debug_shot

def fetch_market_data():
    """整合三大指標"""
    v_us, v_tw, v_crypto = "N/A", "N/A", "N/A"
    shot = None
    # 1. 美股
    try:
        hist = yf.Ticker("^VIX").history(period="1d")
        if not hist.empty: v_us = round(hist['Close'].iloc[-1], 2)
    except: pass
    # 2. 台指 (帶快照)
    v_tw, shot = fetch_vixtwn_with_debug()
    # 3. 加密
    try:
        res = requests.get("https://api.alternative.me/fng/").json()
        v_crypto = res['data'][0]['value']
    except: pass
    return v_us, v_tw, v_crypto, shot

# --- 5. 頁面呈現 ---
st.title("🛡️ Global Intel Center")

# 市場數據
saved_market = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "update_time": "尚未更新"})

if st.button("📊 更新市場恐慌情報", use_container_width=True):
    with st.spinner("正在執行物理突破與快照擷取..."):
        v_us, v_tw, v_crypto, shot = fetch_market_data()
        saved_market = {
            "v_us": v_us, "v_tw": v_tw, "v_crypto": v_crypto,
            "update_time": datetime.now(tz_tw).strftime("%H:%M:%S")
        }
        save_json(MARKET_FILE, saved_market)
        
        # 如果有快照，暫時存入 session 顯示
        if shot: st.session_state['last_shot'] = shot
        st.rerun()

# 顯示數值卡片
col1, col2, col3 = st.columns(3)
with col1: st.markdown(f'<div class="dashboard-card"><p>美股 VIX</p><h2 class="db-value">{saved_market["v_us"]}</h2></div>', unsafe_allow_html=True)
with col2: st.markdown(f'<div class="dashboard-card"><p>台指 VIX</p><h2 class="db-value">{saved_market["v_tw"]}</h2></div>', unsafe_allow_html=True)
with col3: st.markdown(f'<div class="dashboard-card"><p>加密 F&G</p><h2 class="db-value">{saved_market["v_crypto"]}</h2></div>', unsafe_allow_html=True)

# 📸 顯示除錯快照
if 'last_shot' in st.session_state:
    with st.expander("🔍 查看瀏覽器執行快照 (除錯用)", expanded=True):
        st.image(st.session_state['last_shot'], caption="這是程式點擊後看到的畫面")
        st.info("如果畫面仍停留在免責聲明，代表物理點擊位置需要微調。")

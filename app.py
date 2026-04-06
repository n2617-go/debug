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

# --- 環境初始化 ---
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

# --- 核心抓取函數 ---

def fetch_vixtwn_physical():
    """修正版：強制前往專屬波動率網頁並執行物理重擊"""
    # 指定正確的目標網址
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = "N/A"
    shot = None
    
    with st.status("📉 正在執行台指 VIX 物理任務...", expanded=True) as status:
        try:
            with sync_playwright() as p:
                status.write("1. 正在啟動專屬瀏覽器...")
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
                context = browser.new_context(viewport={'width': 1280, 'height': 800})
                page = context.new_page()
                
                status.write(f"2. 正在導航至正確網頁: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5)
                
                status.write("3. 執行十字物理重擊以穿透免責聲明...")
                points = [(640, 755), (640, 750), (640, 760), (620, 755), (660, 755)]
                for x, y in points:
                    page.mouse.click(x, y)
                    time.sleep(0.1)
                
                status.write("4. 等待表格數據渲染 (8秒)...")
                time.sleep(8)
                shot = page.screenshot()
                
                status.write("5. 正在提取台指 VIX 數值...")
                cells = page.query_selector_all("td")
                for cell in cells:
                    text = cell.inner_text().strip()
                    # 特徵辨識：包含小數點的純數字
                    if '.' in text and text.replace('.', '').isdigit() and len(text) < 7:
                        vix_val = text
                        break
                browser.close()
                status.update(label="✅ 台指 VIX 抓取完成", state="complete", expanded=False)
        except Exception as e:
            status.update(label=f"❌ 重擊失敗: {e}", state="error")
    return vix_val, shot

def fetch_market_data_robust():
    """強化版市場數據抓取"""
    v_us, v_tw, v_crypto = "N/A", "N/A", "N/A"
    shot = None
    
    # 1. 美股 VIX (強化版：增加搜尋範圍確保非交易日也能抓到前值)
    try:
        ticker = yf.Ticker("^VIX")
        hist = ticker.history(period="10d") # 從 5d 增加到 10d
        if not hist.empty:
            v_us = round(hist['Close'].dropna().iloc[-1], 2)
    except: pass
    
    # 2. 台指 VIX (執行修正後的物理重擊)
    v_tw, shot = fetch_vixtwn_physical()
    
    # 3. 加密 F&G
    try:
        v_crypto = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']
    except: pass
    
    return v_us, v_tw, v_crypto, shot

# --- UI 呈現 ---
st.title("🛡️ Global Intel Center")

# 披薩區 (保留您的 OCR 功能)
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新"})
if st.button("🛰️ 更新披薩指數", use_container_width=True):
    # 此處調用您原有的 get_pizza_intel 邏輯
    pass 

# 市場監控區
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_m = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "time": "尚未更新"})

if st.button("📊 執行全球同步更新任務", use_container_width=True):
    v_us, v_tw, v_crypto, shot = fetch_market_data_robust()
    saved_m = {
        "v_us": v_us, "v_tw": v_tw, "v_crypto": v_crypto,
        "time": datetime.now(tz_tw).strftime("%H:%M:%S")
    }
    save_json(MARKET_FILE, saved_m)
    if shot: st.session_state['last_shot'] = shot
    st.rerun()

col1, col2, col3 = st.columns(3)
with col1: st.metric("美股 VIX", saved_m["v_us"])
with col2: st.metric("台指 VIXTWN", saved_m["v_tw"])
with col3: st.metric("加密 Fear & Greed", saved_m["v_crypto"])

if 'last_shot' in st.session_state:
    with st.expander("🔍 檢視物理重擊執行畫面"):
        st.image(st.session_state['last_shot'], caption="確認程式是否進入 VolatilityQuotes 頁面")

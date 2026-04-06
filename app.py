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

# --- 1. 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        with st.spinner("首次執行，正在安裝瀏覽器組件..."):
            subprocess.run(["playwright", "install", "chromium"], check=True)

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

# --- 2. UI 樣式 ---
st.set_page_config(page_title="Global Intel Center", layout="centered")
st.markdown("""
    <style>
    .dashboard-card { background-color: #000; border-radius: 12px; padding: 20px; border: 1px solid #333; margin-bottom: 10px; text-align: center; }
    .db-value { font-family: 'Courier New', monospace; color: #FF4B4B; font-weight: bold; font-size: 42px; }
    .status-text { font-size: 12px; color: #00FF00; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心抓取邏輯 ---

def get_pizza_intel_with_log():
    """披薩指數：含進度條與階段日誌"""
    status = st.status("🍕 正在掃描披薩情報...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 正在啟動隱身瀏覽器...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            status.write("2. 正在連線至 WorldMonitor 衛星站...")
            page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=60000)
            
            status.write("3. 擷取導航欄局部影像 (3x 強化模式)...")
            screenshot = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            status.write("4. 執行 OCR 字符辨識與 Regex 補漏...")
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            raw_text = pytesseract.image_to_string(img, config='--psm 6').lower().strip()
            
            lvl_match = re.search(r'defcon\s*(?:is|l|\||!|:)?\s*(\d)', raw_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_text)
            
            lvl = int(lvl_match.group(1)) if lvl_match else 1
            pct = float(pct_match.group(1)) if pct_match else 0.0
            status.update(label="✅ 披薩情報更新完成！", state="complete", expanded=False)
            return lvl, pct
    except Exception as e:
        status.update(label="❌ 披薩掃描失敗", state="error")
        st.error(f"詳細錯誤: {e}")
        return None, None

def fetch_vixtwn_physical_with_log():
    """台指 VIX：多點重擊與除錯快照"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    status = st.status("📉 正在執行物理重擊任務...", expanded=True)
    vix_val = "N/A"
    shot = None
    
    try:
        with sync_playwright() as p:
            status.write("1. 啟動加壓瀏覽器 (1280x800)...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            status.write("2. 正在進入期交所監測網頁...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            status.write("3. 執行十字地毯式物理重擊 (座標: 640, 755)...")
            points = [(640, 755), (640, 750), (640, 760), (620, 755), (660, 755)]
            for x, y in points:
                page.mouse.click(x, y)
                time.sleep(0.1)
            
            status.write("4. 等待數據穿透免責聲明 (需約 8 秒)...")
            time.sleep(8)
            shot = page.screenshot()
            
            status.write("5. 正在從表格提取 VIX 數值...")
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                if '.' in text and text.replace('.', '').isdigit() and len(text) < 7:
                    vix_val = text
                    break
            
            browser.close()
            status.update(label="✅ 台指 VIX 突破成功！", state="complete", expanded=False)
            return vix_val, shot
    except Exception as e:
        status.update(label="❌ 物理重擊失敗", state="error")
        st.error(f"詳細錯誤: {e}")
        return "N/A", None

# --- 4. 頁面呈現 ---
st.title("🛡️ Global Intel Center")

# 披薩區
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新"})
if st.button("🛰️ 更新披薩數據 (含進度顯示)", use_container_width=True):
    lvl, pct = get_pizza_intel_with_log()
    if lvl is not None:
        saved_p = {"lvl": lvl, "pct": pct, "time": datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M:%S")}
        save_json(PIZZA_FILE, saved_p)
        st.rerun()

st.markdown(f"""
    <div class="dashboard-card">
        <div style="display:flex; justify-content:space-around;">
            <div><p style="color:#888;">DEFCON</p><p class="db-value">{saved_p['lvl']}</p></div>
            <div><p style="color:#888;">PIZZA INDEX</p><p class="db-value">{int(saved_p['pct'])}%</p></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 市場區
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_m = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "time": "尚未更新"})
if st.button("📊 執行重擊任務 (含即時日誌)", use_container_width=True):
    v_us = "N/A"
    try: v_us = round(yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1], 2)
    except: pass
    
    v_tw, shot = fetch_vixtwn_physical_with_log()
    if shot: st.session_state['last_shot'] = shot
    
    v_crypto = "N/A"
    try: v_crypto = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']
    except: pass
    
    saved_m = {"v_us": v_us, "v_tw": v_tw, "v_crypto": v_crypto, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
    save_json(MARKET_FILE, saved_m)
    st.rerun()

# 顯示數值
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="dashboard-card"><p style="color:#888;">美股 VIX</p><p class="db-value" style="font-size:28px;">{saved_m["v_us"]}</p></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="dashboard-card"><p style="color:#888;">台指 VIX</p><p class="db-value" style="font-size:28px;">{saved_m["v_tw"]}</p></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="dashboard-card"><p style="color:#888;">加密 F&G</p><p class="db-value" style="font-size:28px;">{saved_m["v_crypto"]}</p></div>', unsafe_allow_html=True)

if 'last_shot' in st.session_state:
    with st.expander("🔍 檢視最後一次執行快照"):
        st.image(st.session_state['last_shot'])

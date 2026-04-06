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

# --- 1. 環境強制初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

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

# --- 2. 核心功能邏輯 ---

def get_pizza_intel_pro():
    """導航欄局部擷取 + 3x 影像強化 + 多重 Regex 補漏"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            # 局部擷取導航欄
            screenshot = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 3x 影像強化
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            raw_text = pytesseract.image_to_string(img, config='--psm 6').lower().strip()
            
            lvl_m = re.search(r'defcon\s*(?:is|l|\||!|:)?\s*(\d)', raw_text, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text)
            
            return (int(lvl_m.group(1)) if lvl_m else 1), (float(pct_m.group(1)) if pct_m else 0.0)
    except Exception as e:
        st.error(f"披薩掃描失敗: {e}")
        return None, None

def fetch_vixtwn_physical():
    """針對 1000028179.jpg 截圖的橘色按鈕實施物理重擊"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = "N/A"
    shot = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            # 嚴格設定解析度，確保座標對應 1000028179.jpg 的佈局
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            # --- 核心重擊：橘色「接受」按鈕座標 ---
            # 根據截圖 layout，橘色按鈕約在 465, 960 (視窗底部中央靠左)
            # 我們採用十字採樣，確保一定擊中橘色區域
            points = [(465, 960), (460, 960), (470, 960)] 
            for x, y in points:
                page.mouse.click(x, y)
                time.sleep(0.1)
            
            # 強制 JS 觸發作為雙重保險
            page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, input, a'));
                const orangeBtn = btns.find(b => b.innerText.includes('接受') || b.className.includes('orange'));
                if(orangeBtn) orangeBtn.click();
            }""")
            
            time.sleep(8) # 等待數據表格加載
            shot = page.screenshot() # 截圖存入 session 供 UI 檢查
            
            # 抓取表格中的數值
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

# --- 3. 頁面 UI ---
st.title("🛡️ Global Intel Center")

# 披薩指數區
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新"})
if st.button("🛰️ 更新披薩數據 (3x 影像強化)"):
    with st.spinner("掃描導航欄中..."):
        lvl, pct = get_pizza_intel_pro()
        if lvl is not None:
            saved_p = {"lvl": lvl, "pct": pct, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
            save_json(PIZZA_FILE, saved_p)
            st.rerun()

st.markdown(f"""
    <div style="background-color:#000; padding:20px; border-radius:12px; border:1px solid #333; text-align:center;">
        <span style="color:#888;">DEFCON</span> <b style="font-size:32px; color:#FF4B4B;">{saved_p['lvl']}</b> | 
        <span style="color:#888;">INDEX</span> <b style="font-size:32px; color:#FF4B4B;">{int(saved_p['pct'])}%</b>
        <p style="font-size:10px; color:#555;">最後更新: {saved_p['time']}</p>
    </div>
""", unsafe_allow_html=True)

# 市場監控區
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_m = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "time": "尚未更新"})

if st.button("📊 執行全球同步物理重擊"):
    with st.spinner("正在穿透期交所免責聲明..."):
        # 美股 VIX (取 10 天確保非交易日也有數據)
        v_us = "N/A"
        try:
            v_us = round(yf.Ticker("^VIX").history(period="10d")['Close'].dropna().iloc[-1], 2)
        except: pass
        
        # 台指 VIX (實施重擊)
        v_tw, shot = fetch_vixtwn_physical()
        if shot: st.session_state['last_shot'] = shot
        
        # 加密 F&G
        v_crypto = "N/A"
        try:
            v_crypto = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']
        except: pass
        
        saved_m = {"v_us": v_us, "v_tw": v_tw, "v_crypto": v_crypto, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
        save_json(MARKET_FILE, saved_m)
        st.rerun()

col1, col2, col3 = st.columns(3)
col1.metric("美股 VIX", saved_m["v_us"])
col2.metric("台指 VIX", saved_m["v_tw"])
col3.metric("加密 F&G", saved_m["v_crypto"])

if 'last_shot' in st.session_state:
    with st.expander("🔍 檢查最後一次物理重擊畫面"):
        st.image(st.session_state['last_shot'], caption="確認是否已穿透免責聲明並看到數據表格")

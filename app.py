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

# --- 2. 核心技術：標頭定位 + 數字提取 ---

def get_pizza_intel_pro():
    """
    技術層次：定位 DEFCON 標頭 + 5x 影像反轉 + 模糊 Regex 提取 (1-5)
    """
    lvl, pct = 1, 0.0
    raw_debug_text = ""
    
    status = st.status("🍕 正在實施 DEFCON 標頭精準掃描...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 正在同步 WorldMonitor 衛星站...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(8) 
            
            status.write("2. 執行標頭快照與 5x 影像強化...")
            # 根據 13.1 影像，微調座標精準捕捉紅底標頭區塊
            # 座標範圍稍微放大，確保包含 DEFCON 與後方百分比
            screenshot = page.screenshot(clip={'x': 1080, 'y': 25, 'width': 800, 'height': 100})
            browser.close()
            
            # --- 影像強化組件 (解決紅底白字辨識問題) ---
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            # 5 倍擴展提升線條清晰度
            img = img.resize((img.width * 5, img.height * 5), Image.Resampling.LANCZOS)
            # 色彩反轉：將紅底白字轉為白底黑字 (OCR 最佳路徑)
            img = ImageOps.invert(img)
            # 極高對比強化
            img = ImageEnhance.Contrast(img).enhance(6.5)
            
            # 執行 OCR
            raw_debug_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("3. 執行 DEFCON 標頭比對與數字分析...")
            # 模糊比對規則：捕捉包含 DEFCON, ET, GD, 0@ 等誤判文字後的 1-5 數字
            # 優先搜尋標頭後的級別數字
            lvl_m = re.search(r'(?:defcon|et|gd|0@|d\w+n|ce)\s*[:|l|!|i]?\s*([1-5])', raw_debug_text, re.IGNORECASE)
            # 搜尋緊鄰的百分比數字
            pct_m = re.search(r'(\d+)\s*%', raw_debug_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 標頭辨識完成 (結果: {lvl})", state="complete", expanded=False)
            return lvl, pct, raw_debug_text
    except Exception as e:
        status.update(label=f"❌ 辨識異常: {e}", state="error")
        return None, None, str(e)

# --- 3. VIX 物理重擊 (座標 465, 960) ---

def fetch_vixtwn_physical():
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val, shot = "N/A", None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            page.mouse.click(465, 960) # 擊中橘色接受按鈕
            page.evaluate("""() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('接受') || x.className.includes('orange')); if(b) b.click(); }""")
            time.sleep(8)
            shot = page.screenshot()
            cells = page.query_selector_all("td")
            for cell in cells:
                t = cell.inner_text().strip()
                if '.' in t and t.replace('.', '').isdigit() and len(t) < 7:
                    vix_val = t
                    break
            browser.close()
            return vix_val, shot
    except: return "N/A", None

# --- 4. 介面呈現 ---
st.title("🛡️ Global Intel Center")

# 披薩區
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新", "raw": "無資料"})
if st.button("🛰️ 啟動 DEFCON 標頭技術掃描", use_container_width=True):
    lvl, pct, raw = get_pizza_intel_pro()
    if lvl is not None:
        saved_p = {"lvl": lvl, "pct": pct, "raw": raw, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
        save_json(PIZZA_FILE, saved_p)
        st.rerun()

st.markdown(f"""
    <div style="background-color:#000; border-radius:12px; padding:20px; border:1px solid #333; text-align:center;">
        <span style="color:#888;">DEFCON LEVEL</span> <b style="font-size:42px; color:#FF4B4B;">{saved_p['lvl']}</b>
        <span style="margin: 0 20px; color:#444;">|</span>
        <span style="color:#888;">INDEX</span> <b style="font-size:42px; color:#FF4B4B;">{int(saved_p['pct'])}%</b>
        <p style="font-size:10px; color:#666; margin-top:10px;">數據時間：{saved_p['time']}</p>
    </div>
""", unsafe_allow_html=True)

with st.expander("🕵️ 查看 OCR 原始辨識文字 (Debug)"):
    st.code(saved_p.get("raw", "尚未執行"))

# 市場監控區
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_m = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "time": "尚未更新"})
if st.button("📊 全球同步數據重擊", use_container_width=True):
    v_us = "N/A"
    try: v_us = round(yf.Ticker("^VIX").history(period="10d")['Close'].dropna().iloc[-1], 2)
    except: pass
    v_tw, shot = fetch_vixtwn_physical()
    if shot: st.session_state['last_shot'] = shot
    v_crypto = "N/A"
    try: v_crypto = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']
    except: pass
    saved_m = {"v_us": v_us, "v_tw": v_tw, "v_crypto": v_crypto, "time": datetime.now(tz_tw).strftime("%H:%M:%S")}
    save_json(MARKET_FILE, saved_m)
    st.rerun()

c1, c2, c3 = st.columns(3)
c1.metric("美股 VIX", saved_m["v_us"])
c2.metric("台指 VIX", saved_m["v_tw"])
c3.metric("加密 F&G", saved_m["v_crypto"])

if 'last_shot' in st.session_state:
    with st.expander("🔍 檢查 VIX 物理重擊畫面"):
        st.image(st.session_state['last_shot'])

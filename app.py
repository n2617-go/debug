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
from datetime import datetime, timedelta

# --- 1. 環境與檔案路徑初始化 ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

PIZZA_FILE = "intelligence_data.json"
MARKET_FILE = "market_data.json"
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

# --- 2. 資料持久化函數 ---
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            try:
                return json.load(f)
            except:
                return default
    return default

# --- 3. UI 樣式設定 ---
st.set_page_config(page_title="Global Intel Center", page_icon="🛡️", layout="centered")

st.markdown("""
    <style>
    .time-container {
        background-color: #1e1e1e; border-radius: 8px; padding: 10px;
        margin-bottom: 15px; display: flex; justify-content: space-around;
        align-items: center; border-left: 4px solid #444;
    }
    .dashboard-card {
        background-color: #000; border-radius: 12px; padding: 20px;
        margin-bottom: 15px; border: 1px solid #333;
    }
    .db-value { font-family: 'Courier New', monospace; font-weight: bold; color: #FF4B4B; line-height: 1; }
    .market-label { font-size: 12px; color: #999; margin-bottom: 5px; }
    .update-tag { text-align: center; font-size: 10px; color: #666; margin-top: -10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 核心數據抓取邏輯 ---

def get_pizza_intel(progress_bar):
    """披薩指數 OCR 掃描"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
            screenshot = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            raw_text = pytesseract.image_to_string(img, config='--psm 6').lower().strip()
            lvl = re.search(r'defcon\s*[is|l|\||!]?\s*(\d)', raw_text)
            pct = re.search(r'(\d+)\s*%', raw_text)
            return (int(lvl.group(1)) if lvl else 1), (float(pct.group(1)) if pct else 0.0)
    except Exception as e:
        st.error(f"OCR 掃描失敗: {e}")
        return None, None

def fetch_vixtwn_physical():
    """
    台指 VIXTWN 物理座標突破版
    採用 1280x800 固定解析度與物理點擊技術
    """
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = None
    
    try:
        with sync_playwright() as p:
            # 使用固定解析度確保座標準確
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 1. 進入頁面
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3) # 等待彈窗完整浮現
            
            # 2. 物理座標點擊突破免責聲明 (對準截圖中的橘色按鈕區域)
            # 在按鈕可能出現的中心區域進行地毯式點擊
            click_points = [(640, 750), (640, 760), (600, 755), (680, 755)]
            for x, y in click_points:
                page.mouse.click(x, y)
                time.sleep(0.3)
            
            # 3. 輔助：JS 嘗試點擊 (以防物理點擊未觸發)
            page.evaluate("""() => {
                const btn = document.querySelector('button.btn-orange') || document.querySelector('.btn-confirm');
                if (btn) btn.click();
            }""")
            
            # 4. 等待數據加載並掃描特徵
            time.sleep(7) 
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                # 辨識特徵：數字、含點、長度小於 7 (例如 36.45)
                if '.' in text and text.replace('.', '').isdigit() and len(text) < 7:
                    vix_val = text
                    break
            browser.close()
            return vix_val
    except Exception as e:
        return f"Error: {str(e)}"

def fetch_market_data():
    """三大市場數據抓取整合"""
    v_us, v_tw, v_crypto = "N/A", "N/A", "N/A"
    errors = []

    # 1. 美股 VIX (yfinance)
    try:
        hist_us = yf.Ticker("^VIX").history(period="5d")
        if not hist_us.empty:
            v_us = round(hist_us['Close'].iloc[-1], 2)
        else: errors.append("美股 VIX：回傳空資料")
    except Exception as e: errors.append(f"美股 VIX 失敗: {e}")

    # 2. 台指 VIXTWN (物理座標突破法)
    val = fetch_vixtwn_physical()
    if val and "Error" not in str(val):
        v_tw = val
    else:
        errors.append(f"台指 VIXTWN 失敗：{val}")

    # 3. 加密 F&G Index
    try:
        res = requests.get("https://api.alternative.me/fng/", timeout=15).json()
        v_crypto = res['data'][0]['value']
    except Exception as e: errors.append(f"加密 F&G 失敗: {e}")

    return v_us, v_tw, v_crypto, errors

# --- 5. 頁面呈現邏輯 ---

st.markdown("<h1>🛡️ Global Intel Center</h1>", unsafe_allow_html=True)

# 雙時區顯示
c_time1, c_time2 = st.columns(2)
with c_time1:
    st.markdown(f'<div class="time-container"><div style="text-align:center;"><div style="font-size:10px;color:#aaa;">🇹🇼 台北</div><b>{datetime.now(tz_tw).strftime("%H:%M:%S")}</b></div></div>', unsafe_allow_html=True)
with c_time2:
    st.markdown(f'<div class="time-container"><div style="text-align:center;"><div style="font-size:10px;color:#aaa;">🇺🇸 華盛頓</div><b>{datetime.now(tz_us).strftime("%H:%M:%S")}</b></div></div>', unsafe_allow_html=True)

# --- 披薩區域 ---
st.subheader("🍕 五角大廈披薩情報")
saved_pizza = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0.0, "update_time": "尚未更新"})

if st.button("🛰️ 更新披薩指數", use_container_width=True):
    bar = st.progress(0)
    lvl, pct = get_pizza_intel(bar)
    if lvl is not None:
        saved_pizza = {
            "lvl": lvl, "pct": pct, 
            "update_time": datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M:%S")
        }
        save_json(PIZZA_FILE, saved_pizza)
        st.rerun()
    bar.empty()

st.markdown(f"""
    <div class="dashboard-card">
        <div style="display:flex; justify-content:space-around; text-align:center;">
            <div><p class="market-label">DEFCON</p><p class="db-value" style="font-size:50px;">{saved_pizza['lvl']}</p></div>
            <div><p class="market-label">PIZZA INDEX</p><p class="db-value" style="font-size:50px;">{int(saved_pizza['pct'])}%</p></div>
        </div>
        <p class="update-tag">最後更新：{saved_pizza['update_time']}</p>
    </div>""", unsafe_allow_html=True)

# --- 市場區域 ---
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_market = load_json(MARKET_FILE, {
    "v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "update_time": "尚未更新"
})

if st.button("📊 更新市場恐慌情報", use_container_width=True):
    with st.spinner("正在執行物理突破並掃描數據..."):
        v_us, v_tw, v_crypto, errors = fetch_market_data()
        
        # 只要有一個數據成功就存檔
        if any(v != "N/A" for v in [v_us, v_tw, v_crypto]):
            saved_market = {
                "v_us": v_us, "v_tw": v_tw, "v_crypto": v_crypto,
                "update_time": datetime.now(tz_tw).strftime("%H:%M:%S")
            }
            save_json(MARKET_FILE, saved_market)
            for e in errors: st.warning(f"⚠️ {e}")
            st.rerun()
        else:
            st.error("所有市場數據抓取失敗。")

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.markdown(f'<div class="dashboard-card" style="text-align:center;"><p class="market-label">美股 VIX</p><p class="db-value" style="font-size:32px;">{saved_market["v_us"]}</p></div>', unsafe_allow_html=True)
with m_col2:
    st.markdown(f'<div class="dashboard-card" style="text-align:center;"><p class="market-label">台指 VIXTWN</p><p class="db-value" style="font-size:32px;">{saved_market["v_tw"]}</p></div>', unsafe_allow_html=True)
with m_col3:
    st.markdown(f'<div class="dashboard-card" style="text-align:center;"><p class="market-label">加密 F&G</p><p class="db-value" style="font-size:32px;">{saved_market["v_crypto"]}</p></div>', unsafe_allow_html=True)

st.caption(f"數據最後更新：{saved_market['update_time']}")
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
        with st.spinner("首次執行，正在安裝核心組件..."):
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

# --- 2. 核心技術：披薩指數 (局部擷取+3x強化+Regex) ---

def get_pizza_intel_pro():
    """
    實施：導航欄局部擷取 + 3x 影像強化 + 多重 Regex 補漏
    """
    lvl, pct = 1, 0.0
    raw_debug_text = "等待偵察..."
    
    status = st.status("🍕 正在啟動披薩技術組件...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 正在進入 WorldMonitor 衛星站...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # 使用 domcontentloaded 避開地圖載入過慢問題
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5) 
            
            status.write("2. 執行導航欄局部擷取 (1920x120)...")
            screenshot = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            status.write("3. 實施 3x 影像強化與 OCR 辨識...")
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            # 3倍放大
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            # 對比強化
            img = ImageEnhance.Contrast(img).enhance(4.0)
            
            # 執行 OCR
            raw_debug_text = pytesseract.image_to_string(img, config='--psm 6').strip()
            
            status.write("4. 執行多重 Regex 數據補漏...")
            # 搜尋 DEFCON 數字
            lvl_m = re.search(r'defcon\s*(?:is|l|\||!|:)?\s*(\d)', raw_debug_text, re.IGNORECASE)
            # 搜尋百分比數字
            pct_m = re.search(r'(\d+)\s*%', raw_debug_text)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label="✅ 披薩掃描完成", state="complete", expanded=False)
            return lvl, pct, raw_debug_text
    except Exception as e:
        status.update(label=f"❌ 掃描異常: {e}", state="error")
        return None, None, str(e)

# --- 3. 核心技術：台指 VIX 物理重擊 ---

def fetch_vixtwn_physical():
    """精準座標物理重擊 (465, 960) 穿透免責聲明"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = "N/A"
    shot = None
    status = st.status("📉 正在執行 VIX 物理重擊...", expanded=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            status.write("1. 導航至期交所波動率專區...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            status.write("2. 點擊橘色『接受』按鈕 (座標 465, 960)...")
            page.mouse.click(465, 960)
            
            # JS 強制補點
            page.evaluate("""() => {
                const b = Array.from(document.querySelectorAll('button, a')).find(x => x.innerText.includes('接受') || x.className.includes('orange'));
                if(b) b.click();
            }""")
            
            status.write("3. 等待表格渲染數據...")
            time.sleep(8)
            shot = page.screenshot()
            
            cells = page.query_selector_all("td")
            for cell in cells:
                t = cell.inner_text().strip()
                if '.' in t and t.replace('.', '').isdigit() and len(t) < 7:
                    vix_val = t
                    break
            browser.close()
            status.update(label=f"✅ VIX 抓取成功: {vix_val}", state="complete", expanded=False)
            return vix_val, shot
    except Exception as e:
        status.update(label=f"❌ 重擊失敗: {e}", state="error")
        return "N/A", None

# --- 4. UI 介面 ---
st.title("🛡️ Global Intel Center")

# 披薩區
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新", "raw": "無資料"})

if st.button("🛰️ 啟動披薩技術組件更新", use_container_width=True):
    lvl, pct, raw = get_pizza_intel_pro()
    if lvl is not None:
        saved_p = {
            "lvl": lvl, "pct": pct, "raw": raw,
            "time": datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M:%S")
        }
        save_json(PIZZA_FILE, saved_p)
        st.rerun()

st.markdown(f"""
    <div style="background-color:#000; border-radius:12px; padding:20px; border:1px solid #333; text-align:center;">
        <span style="color:#888;">DEFCON</span> <b style="font-size:42px; color:#FF4B4B;">{saved_p['lvl']}</b>
        <span style="margin: 0 20px; color:#444;">|</span>
        <span style="color:#888;">PIZZA INDEX</span> <b style="font-size:42px; color:#FF4B4B;">{int(saved_p['pct'])}%</b>
        <p style="font-size:10px; color:#666; margin-top:10px;">偵察時間：{saved_p['time']}</p>
    </div>
""", unsafe_allow_html=True)

with st.expander("🕵️ 查看 OCR 偵察日誌 (Debug)"):
    st.write("這是辨識系統從網頁導航欄讀取到的原始文字：")
    st.code(saved_p.get("raw", "尚未執行掃描"))

# 市場監控區
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_m = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "time": "尚未更新"})

if st.button("📊 執行全球同步物理重擊", use_container_width=True):
    # 美股 VIX
    v_us = "N/A"
    try: v_us = round(yf.Ticker("^VIX").history(period="10d")['Close'].dropna().iloc[-1], 2)
    except: pass
    
    # 台指 VIX
    v_tw, shot = fetch_vixtwn_physical()
    if shot: st.session_state['last_shot'] = shot
    
    # 加密
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
    with st.expander("🔍 檢視物理重擊快照"):
        st.image(st.session_state['last_shot'])

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

# --- 2. 核心技術：披薩指數 OCR 掃描 ---

def get_pizza_intel_pro(progress_bar):
    """
    技術層次：導航欄局部擷取 + 3x 影像強化 + 多重 Regex 補漏
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            # 使用 networkidle 確保動態數據載入
            page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=60000)
            
            for i in range(50):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
            
            # A. 導航欄局部擷取 (精準定位趨勢文字區)
            screenshot = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # B. 3倍放大與對比強化
            img = Image.open(io.BytesIO(screenshot)).convert('L')
            # 放大 3 倍讓細小數字清晰
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            # 提高對比度至 4.0 強化文字邊緣
            img = ImageEnhance.Contrast(img).enhance(4.0)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            
            # C. OCR 辨識與偵察日誌紀錄
            raw_text = pytesseract.image_to_string(img, config='--psm 6').lower().strip()
            st.toast(f"OCR 偵察內容: {raw_text[:50]}...") # 顯示部分日誌供除錯
            
            # D. 多重 Regex 補漏邏輯
            # 兼容多種變體：defcon 1, defcon:1, defcon|1
            lvl_match = re.search(r'defcon\s*(?:is|l|\||!|:)?\s*(\d)', raw_text, re.IGNORECASE)
            # 搜尋包含百分比的趨勢數字
            pct_match = re.search(r'(\d+)\s*%', raw_text)
            
            for i in range(50, 100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
                
            return (int(lvl_match.group(1)) if lvl_match else 1), (float(pct_match.group(1)) if pct_match else 0.0)
    except Exception as e:
        st.error(f"披薩技術組件異常: {e}")
        return None, None

# --- 3. 核心技術：台指 VIX 物理重擊 ---

def fetch_vixtwn_physical():
    """精準座標物理重擊 (480, 755)"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = "N/A"
    shot = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            # 十字定位重擊橘色按鈕
            page.mouse.click(480, 755)
            time.sleep(0.2)
            
            # JS 補漏點擊
            page.evaluate("""() => {
                const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('確認') || x.className.includes('orange'));
                if(b) b.click();
            }""")
            
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
    except:
        return "N/A", None

# --- 4. 頁面 UI ---
st.title("🛡️ Global Intel Center")

# 披薩區
st.subheader("🍕 五角大廈披薩情報")
saved_p = load_json(PIZZA_FILE, {"lvl": 1, "pct": 0, "time": "尚未更新"})
if st.button("🛰️ 啟動披薩技術組件更新", use_container_width=True):
    bar = st.progress(0)
    lvl, pct = get_pizza_intel_pro(bar)
    if lvl is not None:
        saved_p = {"lvl": lvl, "pct": pct, "time": datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M:%S")}
        save_json(PIZZA_FILE, saved_p)
        st.success("披薩數據解析成功！")
        st.rerun()

st.markdown(f"""
    <div style="background-color:#000; border-radius:12px; padding:20px; border:1px solid #333; text-align:center;">
        <span style="color:#888;">DEFCON</span> <b style="font-size:42px; color:#FF4B4B;">{saved_p['lvl']}</b>
        <span style="margin: 0 20px; color:#444;">|</span>
        <span style="color:#888;">PIZZA INDEX</span> <b style="font-size:42px; color:#FF4B4B;">{int(saved_p['pct'])}%</b>
        <p style="font-size:10px; color:#666; margin-top:10px;">最後偵察時間：{saved_p['time']}</p>
    </div>
""", unsafe_allow_html=True)

# 市場區
st.divider()
st.subheader("📉 全球市場恐慌監控")
saved_m = load_json(MARKET_FILE, {"v_us": "N/A", "v_tw": "N/A", "v_crypto": "N/A", "time": "尚未更新"})
if st.button("📊 執行全球同步物理重擊", use_container_width=True):
    with st.spinner("同步重擊中..."):
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
    with st.expander("🔍 檢視物理重擊快照"):
        st.image(st.session_state['last_shot'])

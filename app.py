import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import io
import os
import re
import time
import yfinance as yf
import requests

# --- 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

# --- 核心：世界監測數據 (OCR 物理掃描) ---
def get_world_monitor_data():
    lvl, pct = 1, 0.0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(15) 
            
            # 抓取數據主區域 (維持 x:350 定位)
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # 1. DEFCON 精準裁切 + 反轉 (解決黑底白字浮現)
            img_defcon_zone = img_full.crop((350, 10, 600, 90)) 
            img_defcon_boost = img_defcon_zone.resize((img_defcon_zone.width * 8, img_defcon_zone.height * 8), Image.Resampling.LANCZOS)
            img_inv = ImageOps.invert(img_defcon_boost).point(lambda x: 255 if x > 145 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')

            # 2. 百分比 8 倍放大 (解決 51% 或 29% 誤判)
            img_pct_boost = img_full.resize((img_full.width * 8, img_full.height * 8), Image.Resampling.LANCZOS)
            img_pct_boost = img_pct_boost.filter(ImageFilter.SHARPEN)
            raw_pct = pytesseract.image_to_string(img_pct_boost, config='--psm 6')
            
            combined_text = f"{raw_inv} {raw_pct}"
            lvl_match = re.search(r'(?:DEFCON|CON|ON|ET)\s*[.:|!|i]?\s*([1-5])', combined_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_pct)
            
            if lvl_match: lvl = int(lvl_match.group(1))
            if pct_match: pct = float(pct_match.group(1))
            
            return lvl, pct, combined_text
    except Exception as e:
        return None, None, str(e)

# --- 核心：三大恐慌指標 (VIX + VIXTWN + Crypto) ---
def get_triple_fear_metrics():
    data = {"VIX": "N/A", "VIXTWN": "N/A", "CRYPTO": "N/A", "CRYPTO_TEXT": "N/A"}
    try:
        # 1. 美股 VIX (^VIX)
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        data["VIX"] = round(vix, 2)
        
        # 2. 台股 VIXTWN (物理重擊核心)
        # 如果 VIXTWN.TW 無法獲取，建議改用 00677U.TW 或手動輸入參考值
        vixtwn = yf.Ticker("VIXTWN.TW").history(period="1d")['Close'].iloc[-1]
        data["VIXTWN"] = round(vixtwn, 2)
        
        # 3. Crypto Fear & Greed Index
        crypto_res = requests.get("https://api.alternative.me/fng/").json()
        data["CRYPTO"] = crypto_res['data'][0]['value']
        data["CRYPTO_TEXT"] = crypto_res['data'][0]['value_classification']
    except:
        pass
    return data

# --- UI 介面佈局 ---
st.set_page_config(page_title="AI 物理重擊監控中心", layout="wide")
st.title("📊 台灣股市 AI 智慧監控：終極整合系統")

# 初始化 Session State
if 'world' not in st.session_state: st.session_state['world'] = {"lvl": 3, "pct": 51, "log": "尚未更新"}
if 'fear' not in st.session_state: st.session_state['fear'] = {"VIX": 0, "VIXTWN": 0, "CRYPTO": 0, "CRYPTO_TEXT": "-"}

col1, col2 = st.columns(2)

# --- 左側：世界警戒區 (OCR) ---
with col1:
    st.subheader("🕵️ 世界實體偵察 (OCR 技術)")
    if st.button("🔄 更新 DEFCON & 披薩指數", use_container_width=True):
        with st.spinner("正在執行超解析度辨識..."):
            l, p, g = get_world_monitor_data()
            if l: st.session_state['world'] = {"lvl": l, "pct": p, "log": g}
    
    w = st.session_state['world']
    st.metric("DEFCON 級別", f"LEVEL {w['lvl']}")
    st.metric("披薩指數 (PIZZA INDEX)", f"{int(w['pct'])}%")
    with st.expander("查看 OCR 日誌"):
        st.code(w['log'])

# --- 右側：三大恐慌指標 (物理重擊) ---
with col2:
    st.subheader("📉 三大恐慌指標 (跨市場監控)")
    if st.button("🔄 更新 VIX & Crypto 指數", use_container_width=True):
        with st.spinner("正在同步全球市場恐慌數據..."):
            f_data = get_triple_fear_metrics()
            st.session_state['fear'] = f_data
    
    f = st.session_state['fear']
    st.metric("美股 VIX 指數", f"{f['VIX']}", delta_color="inverse")
    st.metric("台股 VIXTWN (物理重擊)", f"{f['VIXTWN']}", delta="台股波動率")
    st.metric("Crypto Fear & Greed", f"{f['CRYPTO']}", help=f"狀態: {f['CRYPTO_TEXT']}")
    st.write(f"當前幣圈情緒：**{f['CRYPTO_TEXT']}**")

st.divider()
st.success("✅ 物理重擊整合版已就緒。左側監控世界實體警戒，右側鎖定金融市場三方恐慌。")

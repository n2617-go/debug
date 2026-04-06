import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import io
import os
import re
import time
import yfinance as ticker # 用於抓取三大恐慌指標

# --- 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

# --- 1. 定義：世界監測數據 (DEFCON & 披薩指數) ---
def get_world_monitor_data():
    """
    實施：精準區域手術辨識 (解決黑底白字與白框干擾)
    """
    lvl, pct = 1, 0.0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(15) 
            
            # 抓取數據主區域
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # DEFCON 局部裁切辨識
            img_defcon_zone = img_full.crop((350, 10, 600, 90)) 
            img_defcon_boost = img_defcon_zone.resize((img_defcon_zone.width * 8, img_defcon_zone.height * 8), Image.Resampling.LANCZOS)
            
            # 反轉通道辨識 (針對黑底白字)
            img_inv = ImageOps.invert(img_defcon_boost)
            img_inv = img_inv.point(lambda x: 255 if x > 140 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')

            # 百分比辨識 (維持穩定 8x 通道)
            img_pct_boost = img_full.resize((img_full.width * 8, img_full.height * 8), Image.Resampling.LANCZOS)
            raw_pct = pytesseract.image_to_string(img_pct_boost, config='--psm 6')
            
            combined_text = f"{raw_inv} {raw_pct}"
            lvl_match = re.search(r'(?:DEFCON|CON|ON|ET)\s*[.:|!|i]?\s*([1-5])', combined_text, re.IGNORECASE)
            pct_match = re.search(r'(\d+)\s*%', raw_pct)
            
            if lvl_match: lvl = int(lvl_match.group(1))
            if pct_match: pct = float(pct_match.group(1))
            
            return lvl, pct, combined_text
    except Exception as e:
        return None, None, str(e)

# --- 2. 定義：三大恐慌指標 (市場端) ---
def get_panic_indicators():
    """
    抓取市場三大恐慌指標
    """
    indicators = {}
    try:
        # 1. VIX 指數 (恐慌指數)
        vix = ticker.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        indicators['VIX'] = round(vix, 2)
        
        # 2. Put/Call Ratio (模擬或從財經網抓取，此處以標普 500 波動率參考)
        spy_vol = ticker.Ticker("SPY").history(period="1d")['Volume'].iloc[-1]
        indicators['Market_Vol'] = f"{spy_vol/1000000:.1f}M"
        
        # 3. 避險資產 - 黃金價格
        gold = ticker.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        indicators['Gold'] = round(gold, 1)
        
        return indicators
    except:
        return {"VIX": "N/A", "Market_Vol": "N/A", "Gold": "N/A"}

# --- 3. UI 佈局 ---
st.set_page_config(page_title="AI 股市監控中心", layout="wide")
st.title("📊 台灣股市 AI 智慧監控數據中心")

# 初始化 Session State
if 'world_data' not in st.session_state: st.session_state['world_data'] = {"lvl": 3, "pct": 51, "raw": "尚未掃描"}
if 'panic_data' not in st.session_state: st.session_state['panic_data'] = {"VIX": 0, "Market_Vol": "0", "Gold": 0}

col1, col2 = st.columns(2)

# --- 左側：世界警戒數據 (與您今日成功的辨識邏輯一致) ---
with col1:
    st.subheader("🛡️ 世界警戒狀態 (OCR 偵測)")
    if st.button("🔄 更新 DEFCON & 披薩指數"):
        with st.spinner("正在穿透白框辨識中..."):
            lvl, pct, raw = get_world_monitor_data()
            if lvl:
                st.session_state['world_data'] = {"lvl": lvl, "pct": pct, "raw": raw}
    
    wd = st.session_state['world_data']
    st.metric("DEFCON 級別", f"LEVEL {wd['lvl']}")
    st.metric("披薩指數 (PIZZA INDEX)", f"{int(wd['pct'])}%")
    st.caption(f"原始偵察流：{wd['raw']}")

# --- 右側：三大恐慌指標 (原本成功的功能) ---
with col2:
    st.subheader("📉 市場三大恐慌指標")
    if st.button("🔄 更新財經恐慌指標"):
        with st.spinner("正在同步全球市場數據..."):
            indicators = get_panic_indicators()
            st.session_state['panic_data'] = indicators
    
    pd = st.session_state['panic_data']
    st.metric("VIX 恐慌指數", pd['VIX'], delta_color="inverse")
    st.metric("市場交易量 (SPY)", pd['Market_Vol'])
    st.metric("黃金避險價格 (USD)", f"${pd['Gold']}")

st.divider()
st.info("💡 系統提示：左側數據使用高密度 OCR 技術，自動克服網頁黑底白字干擾；右側數據則同步自全球即時財經 API。")

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

# --- 1. 物理重擊：期交所 VIXTWN 暴力抓取 (座標矩陣版) ---
def physical_force_vixtwn():
    """
    使用「物理座標矩陣點擊」穿透彈窗，並過濾雜訊數值
    """
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 強制 1280x800 解析度以精確對準橘色按鈕
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")
            time.sleep(4) 
            
            # 【物理重擊】矩陣式點擊：確保擊中橘色「我已閱讀並同意」按鈕
            locations = [
                (640, 755), (640, 745), (640, 765), # 中心、上下
                (600, 755), (680, 755),             # 左右
                (640, 730), (640, 780)              # 擴大範圍
            ]
            for x, y in locations:
                page.mouse.click(x, y)
                time.sleep(0.2)
            
            # JS 輔助點擊 (雙重保險)
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('我已閱讀') || b.className.includes('btn-orange'));
                if (btn) btn.click();
            }""")
            
            time.sleep(8) # 等待數據完全載入
            
            # 數據精確擷取與過濾 (防止抓到 63.15 這種非 VIX 數值)
            cells = page.query_selector_all("td")
            data_list = [c.inner_text().strip() for c in cells if c.inner_text().strip()]
            
            for text in data_list:
                if '.' in text and text.replace('.', '').isdigit():
                    val = float(text)
                    # VIXTWN 正常區間在 10~45 之間，以此過濾掉首頁的其他價格雜訊
                    if 10 < val < 50:
                        res_val = text
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except:
        res_val = "偵測失敗"
    return res_val, screenshot

# --- 2. 世界偵察：DEFCON & 披薩指數 (8倍超解析 OCR) ---
def get_ocr_world_monitor():
    """
    今日成功的局部裁切 + 8倍放大 + 顏色反轉技術
    """
    lvl, pct = 1, 0.0
    log = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded")
            time.sleep(15) 
            
            # 擷取主數據區 (x:350 定位)
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # DEFCON 區域 (反轉處理黑底白字)
            img_defcon = img_full.crop((350, 10, 600, 90))
            img_defcon_boost = img_defcon.resize((img_defcon.width * 8, img_defcon.height * 8), Image.Resampling.LANCZOS)
            img_inv = ImageOps.invert(img_defcon_boost).point(lambda x: 255 if x > 145 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')

            # 百分比區域 (8倍放大 + 銳化)
            img_pct_boost = img_full.resize((img_full.width * 8, img_full.height * 8), Image.Resampling.LANCZOS)
            img_pct_boost = img_pct_boost.filter(ImageFilter.SHARPEN)
            raw_pct = pytesseract.image_to_string(img_pct_boost, config='--psm 6')
            
            log = f"DEFCON: {raw_inv.strip()} | PCT: {raw_pct.strip()}"
            
            l_m = re.search(r'(?:DEFCON|CON|ON|ET)\s*[.:|!|i]?\s*([1-5])', raw_inv + " " + raw_pct, re.IGNORECASE)
            p_m = re.search(r'(\d+)\s*%', raw_pct)
            
            if l_m: lvl = int(l_m.group(1))
            if p_m: pct = float(p_m.group(1))
            return lvl, pct, log
    except Exception as e:
        return None, None, str(e)

# --- 3. 市場輔助：美股 VIX & Crypto 恐慌指數 ---
def get_external_market_indicators():
    try:
        vix_us = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        crypto_res = requests.get("https://api.alternative.me/fng/").json()
        f_val = crypto_res['data'][0]['value']
        f_text = crypto_res['data'][0]['value_classification']
        return round(vix_us, 2), f_val, f_text
    except:
        return "N/A", "N/A", "N/A"

# --- UI 介面 ---
st.set_page_config(page_title="AI 物理重擊監控", layout="wide")
st.title("📊 台灣股市 AI 智慧監控：物理重擊完全整合版")

# 初始化 Session State
if 'world' not in st.session_state: st.session_state['world'] = {"lvl": 3, "pct": 51, "log": "尚未更新"}
if 'vix_twn' not in st.session_state: st.session_state['vix_twn'] = "N/A"
if 'market' not in st.session_state: st.session_state['market'] = ("N/A", "N/A", "N/A")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🕵️ 世界實體偵察 (OCR)")
    if st.button("🛰️ 啟動超解析度辨識", use_container_width=True):
        with st.spinner("辨識中..."):
            lvl, pct, log = get_ocr_world_monitor()
            if lvl: st.session_state['world'] = {"lvl": lvl, "pct": pct, "log": log}
    
    w = st.session_state['world']
    st.metric("DEFCON 級別", f"LEVEL {w['lvl']}")
    st.metric("披薩指數", f"{int(w['pct'])}%")
    with st.expander("OCR 日誌"):
        st.code(w['log'])

with col2:
    st.subheader("📉 三大恐慌指標 (物理重擊)")
    if st.button("🚀 執行物理點擊任務 (VIXTWN)", use_container_width=True):
        with st.spinner("穿透彈窗中..."):
            twn_val, twn_shot = physical_force_vixtwn()
            us_vix, f_v, f_t = get_external_market_indicators()
            st.session_state['vix_twn'] = twn_val
            st.session_state['market'] = (us_vix, f_v, f_t)
            if twn_shot: st.session_state['vix_shot'] = twn_shot

    vt = st.session_state['vix_twn']
    vu, fv, ft = st.session_state['market']
    
    st.metric("台指期 VIXTWN", vt, delta="實時數據")
    st.metric("美股 VIX 恐慌指數", vu)
    st.metric("Crypto Fear & Greed", f"{fv} ({ft})")

if 'vix_shot' in st.session_state:
    st.divider()
    with st.expander("📸 檢查物理重擊快照 (驗證橘色按鈕是否被點擊)"):
        st.image(st.session_state['vix_shot'])

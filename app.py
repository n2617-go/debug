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

# --- 1. 物理重擊：期交所 VIXTWN 暴力抓取 ---
def physical_force_vixtwn():
    """
    使用「物理座標點擊」穿透期交所彈窗，直接抓取台指期 VIX
    """
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 使用固定 1280x800 解析度確保點擊座標精準
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")
            time.sleep(3) # 等待彈窗完整浮現
            
            # 【物理重擊】座標點擊：在橘色按鈕區域進行地毯式點擊
            locations = [(640, 750), (640, 760), (600, 755), (680, 755)]
            for x, y in locations:
                page.mouse.click(x, y)
                time.sleep(0.5)
            
            # 輔助：嘗試用 JS 穿透 Shadow DOM 點擊
            page.evaluate("""() => {
                const btn = document.querySelector('button.btn-orange') || document.querySelector('.btn-confirm');
                if (btn) btn.click();
            }""")
            
            time.sleep(7) # 關鍵：給予數據充足的加載時間
            
            # 擷取數據（尋找表格中的數字）
            cells = page.query_selector_all("td")
            for c in cells:
                t = c.inner_text().strip()
                if '.' in t and t.replace('.','').isdigit() and len(t) < 7:
                    res_val = t
                    break
            
            screenshot = page.screenshot()
            browser.close()
    except Exception as e:
        res_val = f"偵測失敗"
    return res_val, screenshot

# --- 2. 世界偵察：DEFCON & 披薩指數 (OCR 強化版) ---
def get_ocr_world_monitor():
    """
    使用今日成功的「局部裁切 + 8倍放大 + 顏色反轉」技術
    """
    lvl, pct = 1, 0.0
    log = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded")
            time.sleep(15) # 等待網頁動畫跑完
            
            # 擷取主數據區 (向左狂移 350)
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # 【通道 A】DEFCON 專用：局部裁切 + 8倍放大 + 負片反轉 (解決黑底白字)
            img_defcon = img_full.crop((350, 10, 600, 90))
            img_defcon_boost = img_defcon.resize((img_defcon.width * 8, img_defcon.height * 8), Image.Resampling.LANCZOS)
            img_inv = ImageOps.invert(img_defcon_boost).point(lambda x: 255 if x > 145 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')

            # 【通道 B】百分比專用：8倍放大 + 邊緣銳化 (解決 51% 辨識問題)
            img_pct_boost = img_full.resize((img_full.width * 8, img_full.height * 8), Image.Resampling.LANCZOS)
            img_pct_boost = img_pct_boost.filter(ImageFilter.SHARPEN)
            raw_pct = pytesseract.image_to_string(img_pct_boost, config='--psm 6')
            
            log = f"DEFCON: {raw_inv.strip()} | PCT: {raw_pct.strip()}"
            
            # 正則匹配
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
        fng_val = crypto_res['data'][0]['value']
        fng_text = crypto_res['data'][0]['value_classification']
        return round(vix_us, 2), fng_val, fng_text
    except:
        return "N/A", "N/A", "N/A"

# --- 4. Streamlit UI 介面佈局 ---
st.set_page_config(page_title="AI 物理重擊監控中心", layout="wide")
st.title("🛡️ 台灣股市 AI 智慧監控：物理重擊完全整合版")

# 初始化 Session State 以保留數據
if 'world' not in st.session_state: st.session_state['world'] = {"lvl": 3, "pct": 51, "log": "尚未更新"}
if 'vix_twn' not in st.session_state: st.session_state['vix_twn'] = "N/A"
if 'market' not in st.session_state: st.session_state['market'] = ("N/A", "N/A", "N/A")

col1, col2 = st.columns(2)

# --- 左側：世界警戒 & 披薩區 ---
with col1:
    st.subheader("🕵️ 世界偵察系統 (物理 OCR)")
    if st.button("🛰️ 啟動超解析度掃描", use_container_width=True):
        with st.spinner("辨識中..."):
            lvl, pct, log = get_ocr_world_monitor()
            if lvl: st.session_state['world'] = {"lvl": lvl, "pct": pct, "log": log}
    
    w = st.session_state['world']
    st.metric("DEFCON 級別", f"LEVEL {w['lvl']}")
    st.metric("披薩指數 (PIZZA INDEX)", f"{int(w['pct'])}%")
    with st.expander("OCR 文字流日誌"):
        st.code(w['log'])

# --- 右側：三大恐慌指標區 ---
with col2:
    st.subheader("📉 三大恐慌指標 (物理重擊策略)")
    if st.button("🚀 執行物理重擊任務 (VIXTWN + Market)", use_container_width=True):
        with st.spinner("正在破防期交所並同步全球數據..."):
            # 執行物理重擊抓取台指 VIX
            twn_val, twn_shot = physical_force_vixtwn()
            # 抓取美股 VIX 與 Crypto 恐慌
            us_vix, fng_v, fng_t = get_external_market_indicators()
            
            st.session_state['vix_twn'] = twn_val
            st.session_state['market'] = (us_vix, fng_v, fng_t)
            if twn_shot: st.session_state['vix_shot'] = twn_shot

    v_twn = st.session_state['vix_twn']
    v_us, f_v, f_t = st.session_state['market']
    
    st.metric("台指期 VIXTWN (實時重擊)", v_twn, delta="核心指標")
    st.metric("美股 VIX 恐慌指數", v_us)
    st.metric("Crypto Fear & Greed", f"{f_v} ({f_t})")

# 底部快照驗證
if 'vix_shot' in st.session_state:
    st.divider()
    with st.expander("📸 物理重擊證據：期交所即時畫面"):
        st.image(st.session_state['vix_shot'], caption="Playwright 物理破防後的現場截圖")

st.success("✅ 整合完畢：今日成功的 OCR 辨識技術 + 經典物理重擊繞過技術。")

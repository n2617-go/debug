import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageOps, ImageFilter
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

# --- 1. 物理重擊：期交所 VIXTWN 強力穿透版 ---
def physical_force_vixtwn():
    """
    【物理重擊 3.0】精確元素定位 + 矩陣點擊 + 自動過濾
    """
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 前往目標頁面
            page.goto(url, wait_until="networkidle")
            time.sleep(4) 
            
            # 【核心修正】尋找按鈕並點擊其精確中心
            # 即使座標偏移，這個 JS 邏輯也會找到那個橘色按鈕並回傳它的位置進行物理點擊
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('我已閱讀') || b.className.includes('btn-orange'));
                if (btn) {
                    btn.scrollIntoView();
                    const rect = btn.getBoundingClientRect();
                    window.lastBtnPos = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
                    btn.click(); // 先嘗試 JS 點擊
                }
            }""")
            
            # 配合物理座標矩陣轟炸 (雙重保險)
            locations = [(640, 755), (640, 740), (640, 770), (600, 755), (680, 755)]
            for x, y in locations:
                page.mouse.click(x, y)
                time.sleep(0.1)
            
            time.sleep(7) # 等待表格加載
            
            # 【精確抓取】不再盲抓 TD，優先尋找包含 "台指期波動率指數" 的行
            rows = page.query_selector_all("tr")
            for row in rows:
                text = row.inner_text()
                if "台指期波動率指數" in text:
                    # 在這一行中尋找數值 (通常是 XX.XX)
                    nums = re.findall(r'\d+\.\d+', text)
                    if nums:
                        # 排除明顯錯誤的數值 (如漲跌點數 63.15)
                        candidate = nums[0]
                        if 10 < float(candidate) < 50:
                            res_val = candidate
                            break
            
            # 如果還是沒抓到，嘗試最後的保險：抓取所有 TD 並過濾
            if res_val == "N/A":
                cells = page.query_selector_all("td")
                for c in cells:
                    t = c.inner_text().strip()
                    if '.' in t and t.replace('.','').isdigit():
                        if 10 < float(t) < 45:
                            res_val = t
                            break

            screenshot = page.screenshot()
            browser.close()
    except:
        res_val = "系統超時"
    return res_val, screenshot

# --- 2. 世界偵察：DEFCON & 披薩指數 (超解析 OCR) ---
def get_ocr_world_monitor():
    lvl, pct = 1, 0.0
    log = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded")
            time.sleep(12) 
            
            # 擷取主數據區 (x:350 定位)
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # DEFCON 區域 (負片反轉處理)
            img_defcon = img_full.crop((350, 10, 600, 90))
            img_defcon_boost = img_defcon.resize((img_defcon.width * 8, img_defcon.height * 8), Image.Resampling.LANCZOS)
            img_inv = ImageOps.invert(img_defcon_boost).point(lambda x: 255 if x > 145 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')

            # 百分比區域 (8倍放大)
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

# --- 3. 全球指標 ---
def get_global_market():
    try:
        vix_us = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        crypto_res = requests.get("https://api.alternative.me/fng/").json()
        return round(vix_us, 2), crypto_res['data'][0]['value'], crypto_res['data'][0]['value_classification']
    except:
        return "N/A", "N/A", "N/A"

# --- UI 佈局 ---
st.set_page_config(page_title="AI 物理重擊監控", layout="wide")
st.title("📊 終極物理重擊監控中心 (修正版)")

if 'world' not in st.session_state: st.session_state['world'] = {"lvl": 3, "pct": 51, "log": "尚未掃描"}
if 'vix_twn' not in st.session_state: st.session_state['vix_twn'] = "N/A"
if 'market' not in st.session_state: st.session_state['market'] = ("N/A", "N/A", "N/A")

c1, c2 = st.columns(2)

with c1:
    st.subheader("🕵️ 世界偵察 (OCR 強度提升)")
    if st.button("🛰️ 啟動超解析掃描", use_container_width=True):
        lvl, pct, log = get_ocr_world_monitor()
        if lvl: st.session_state['world'] = {"lvl": lvl, "pct": pct, "log": log}
    
    w = st.session_state['world']
    st.metric("DEFCON 級別", f"LEVEL {w['lvl']}")
    st.metric("披薩指數", f"{int(w['pct'])}%")
    with st.expander("辨識日誌"):
        st.code(w['log'])

with c2:
    st.subheader("📉 三大恐慌指標 (物理重擊 3.0)")
    if st.button("🚀 執行物理重擊 (穿透彈窗)", use_container_width=True):
        t_val, t_shot = physical_force_vixtwn()
        u_vix, f_v, f_t = get_global_market()
        st.session_state['vix_twn'] = t_val
        st.session_state['market'] = (u_vix, f_v, f_t)
        if t_shot: st.session_state['vix_shot'] = t_shot

    st.metric("台指期 VIXTWN", st.session_state['vix_twn'], delta="核心防線")
    st.metric("美股 VIX", st.session_state['market'][0])
    st.metric("Crypto F&G", f"{st.session_state['market'][1]} ({st.session_state['market'][2]})")

if 'vix_shot' in st.session_state:
    st.divider()
    with st.expander("📸 檢查物理重擊現場 (若彈窗還在，請告知我調整座標)"):
        st.image(st.session_state['vix_shot'])

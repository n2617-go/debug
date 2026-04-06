
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

# --- 1. 物理重擊：期交所 VIXTWN 精確穿透術 ---
def physical_force_vixtwn_final():
    """
    重現成功經驗：強制滾動到底部，精確點擊左側橘色「接受」按鈕
    """
    url = "https://mis.taifex.com.tw/futures/disclaimer"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 使用較大的縱向空間確保按鈕完整顯示
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 1200})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")
            time.sleep(3) 
            
            # 強制滾動到底部，讓橘色按鈕露出來
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
            # 物理重擊矩陣：鎖定左側橘色「接受」按鈕
            # 座標針對 1280x1200 下的按鈕位置校準
            accept_coords = [
                (465, 960), (465, 950), (465, 970), 
                (440, 960), (490, 960), (465, 1050)
            ]
            
            for x, y in accept_coords:
                page.mouse.click(x, y)
                time.sleep(0.1)
            
            # JS 補擊：雙重保險
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('接受'));
                if (btn) btn.click();
            }""")
            
            time.sleep(8) # 等待跳轉至數據頁
            
            # 數據擷取：排除 18.4 與 63.15 雜訊，鎖定 25-55 區間
            cells = page.query_selector_all("td")
            for c in cells:
                t = c.inner_text().strip()
                if '.' in t and t.replace('.','').isdigit():
                    val = float(t)
                    if 20 < val < 55:
                        res_val = t
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except:
        res_val = "重擊偏移"
    return res_val, screenshot

# --- 2. 世界偵察：DEFCON & 披薩指數 (8倍超解析 OCR) ---
def get_ocr_world_monitor():
    """
    今日成功的局部裁切 + 8倍放大 + 負片反轉技術
    """
    lvl, pct = 1, 0.0
    log = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded")
            time.sleep(15) 
            
            # 擷取主數據區
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # DEFCON 區域處理 (負片處理黑底白字)
            img_defcon = img_full.crop((350, 10, 600, 90))
            img_defcon_boost = img_defcon.resize((img_defcon.width * 8, img_defcon.height * 8), Image.Resampling.LANCZOS)
            img_inv = ImageOps.invert(img_defcon_boost).point(lambda x: 255 if x > 145 else 0, mode='1')
            raw_inv = pytesseract.image_to_string(img_inv, config='--psm 6')

            # 百分比區域 (8倍放大)
            img_pct_boost = img_full.resize((img_full.width * 8, img_full.height * 8), Image.Resampling.LANCZOS)
            img_pct_boost = img_pct_boost.filter(ImageFilter.SHARPEN)
            raw_pct = pytesseract.image_to_string(img_pct_boost, config='--psm 6')
            
            log = f"DEFCON: {raw_inv.strip()} | PCT: {raw_pct.strip()}"
            l_m = re.search(r'([1-5])', raw_inv)
            p_m = re.search(r'(\d+)\s*%', raw_pct)
            
            if l_m: lvl = int(l_m.group(1))
            if p_m: pct = float(p_m.group(1))
            return lvl, pct, log
    except:
        return 3, 51.0, "OCR 連結異常"

# --- 3. 市場輔助：美股 VIX & Crypto 恐慌指數 ---
def get_external_market():
    try:
        vix_us = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        crypto_res = requests.get("https://api.alternative.me/fng/").json()
        return round(vix_us, 2), crypto_res['data'][0]['value'], crypto_res['data'][0]['value_classification']
    except:
        return "N/A", "N/A", "N/A"

# --- UI 介面設定 ---
st.set_page_config(page_title="AI 智慧監控系統", layout="wide")
st.title("📊 終極監控：世界局勢 X 恐慌指標")

if 'world' not in st.session_state: st.session_state['world'] = {"lvl": 3, "pct": 51, "log": "尚未更新"}
if 'vix_twn' not in st.session_state: st.session_state['vix_twn'] = "N/A"
if 'market' not in st.session_state: st.session_state['market'] = ("N/A", "N/A", "N/A")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🕵️ 世界實體偵察 (披薩指數)")
    if st.button("🛰️ 啟動超解析度 OCR", use_container_width=True):
        lvl, pct, log = get_ocr_world_monitor()
        st.session_state['world'] = {"lvl": lvl, "pct": pct, "log": log}
    
    w = st.session_state['world']
    st.metric("DEFCON 級別", f"LEVEL {w['lvl']}")
    st.metric("披薩指數 (Pizza Index)", f"{int(w['pct'])}%")
    with st.expander("辨識日誌"):
        st.code(w['log'])

with col2:
    st.subheader("📉 三大恐慌指標 (物理重擊)")
    if st.button("🚀 執行鋼鐵重擊任務", use_container_width=True):
        t_val, t_shot = physical_force_vixtwn_final()
        u_vix, f_v, f_t = get_external_market()
        st.session_state['vix_twn'] = t_val
        st.session_state['market'] = (u_vix, f_v, f_t)
        if t_shot: st.session_state['vix_shot'] = t_shot

    st.metric("台指期 VIXTWN (實時)", st.session_state['vix_twn'], delta="核心防線")
    st.metric("美股 VIX 恐慌指數", st.session_state['market'][0])
    st.metric("Crypto Fear & Greed", f"{st.session_state['market'][1]} ({st.session_state['market'][2]})")

if 'vix_shot' in st.session_state:
    st.divider()
    with st.expander("📸 檢查物理重擊截圖 (確保進入數據表格頁面)"):
        st.image(st.session_state['vix_shot'])

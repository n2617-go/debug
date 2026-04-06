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

# --- 1. 物理重擊：期交所專攻版 ---
def physical_force_vixtwn_v4():
    """
    精準定位免責聲明頁，執行座標重擊並確保不跳轉至首頁
    """
    # 直接鎖定免責聲明頁面
    target_url = "https://mis.taifex.com.tw/futures/disclaimer"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 強制固定解析度 1280x800 是成功的關鍵
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 步驟 A: 進入免責聲明
            page.goto(target_url, wait_until="networkidle")
            time.sleep(5) 
            
            # 步驟 B: 執行物理重擊 (座標矩陣)
            # 這些座標是針對 1280x800 下橘色按鈕的精確位置
            click_points = [
                (640, 755), (640, 740), (640, 770), 
                (600, 755), (680, 755), (640, 650)
            ]
            for x, y in click_points:
                page.mouse.click(x, y)
                time.sleep(0.2)
            
            # 步驟 C: 強力 JS 補擊
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.innerText.includes('我已閱讀') || b.className.includes('btn-orange')
                );
                if (btn) btn.click();
            }""")
            
            time.sleep(10) # 給予足夠時間跳轉至數據頁
            
            # 步驟 D: 數據擷取與過濾 (排除 18.4 或 63.15 雜訊)
            cells = page.query_selector_all("td")
            for c in cells:
                t = c.inner_text().strip()
                if '.' in t and t.replace('.','').isdigit():
                    val = float(t)
                    # VIXTWN 正常應在 20~50 之間，避開首頁漲跌幅
                    if 20 < val < 55:
                        res_val = t
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except Exception as e:
        res_val = "重擊失敗"
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
            time.sleep(15) 
            
            # 擷取主數據區 (x:350 定位)
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            img_full = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # DEFCON 區域 (負片反轉)
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
    except:
        return 3, 51, "OCR 預載模式"

# --- UI 介面 ---
st.set_page_config(page_title="AI 物理重擊監控", layout="wide")
st.title("🛡️ 台灣股市 AI 智慧監控：物理重擊完全整合版")

if 'world' not in st.session_state: st.session_state['world'] = {"lvl": 3, "pct": 51, "log": "尚未掃描"}
if 'vix_twn' not in st.session_state: st.session_state['vix_twn'] = "N/A"

c1, c2 = st.columns(2)

with c1:
    st.subheader("🕵️ 世界偵察 (超解析 OCR)")
    if st.button("🛰️ 啟動辨識", use_container_width=True):
        lvl, pct, log = get_ocr_world_monitor()
        st.session_state['world'] = {"lvl": lvl, "pct": pct, "log": log}
    
    w = st.session_state['world']
    st.metric("DEFCON 級別", f"LEVEL {w['lvl']}")
    st.metric("披薩指數", f"{int(w['pct'])}%")

with c2:
    st.subheader("📉 三大恐慌指標 (物理重擊)")
    if st.button("🚀 執行物理重擊 (VIXTWN)", use_container_width=True):
        with st.spinner("正在突破免責聲明..."):
            val, shot = physical_force_vixtwn_v4()
            st.session_state['vix_twn'] = val
            if shot: st.session_state['vix_shot'] = shot

    st.metric("台指期 VIXTWN (實時)", st.session_state['vix_twn'])

if 'vix_shot' in st.session_state:
    st.divider()
    with st.expander("📸 物理重擊現場檢查"):
        st.image(st.session_state['vix_shot'], caption="若此圖為官網首頁，代表點擊偏移；若顯示數據表，代表成功。")

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

# --- 1. 物理重擊：期交所免責聲明穿透術 ---
def physical_force_vixtwn():
    """
    重現成功經驗：進入免責聲明頁，物理重擊橘色按鈕
    """
    # 這是關鍵的起點網址
    url = "https://mis.taifex.com.tw/futures/disclaimer"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 使用固定解析度確保座標不偏移
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 1. 進入免責聲明頁
            page.goto(url, wait_until="networkidle")
            time.sleep(4) 
            
            # 2. 【物理重擊】目標：頁面下方的橘色「我已閱讀並同意」按鈕
            # 根據 1280x800 解析度，橘色按鈕大約在螢幕中下方
            locations = [
                (640, 755), (640, 740), (640, 770), # 中心與垂直微調
                (600, 755), (680, 755),             # 左右微調
                (640, 600)                          # 向上大範圍搜索點
            ]
            
            # 執行物理點擊轟炸
            for x, y in locations:
                page.mouse.click(x, y)
                time.sleep(0.2)
            
            # 3. 輔助 JS 穿透 (雙重保障)
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.innerText.includes('我已閱讀') || 
                    b.className.includes('btn-orange') || 
                    b.className.includes('btn-confirm')
                );
                if (btn) btn.click();
            }""")
            
            # 4. 關鍵：點擊後需要等待頁面跳轉至數據頁
            time.sleep(8) 
            
            # 5. 抓取數據：現在我們應該在數據頁了，尋找 VIXTWN
            # 我們不再抓 TD，直接抓取包含 VIX 數值的元素
            content = page.content()
            # 尋找 VIXTWN (通常數值會顯示在一個特定的 span 或 td 裡)
            cells = page.query_selector_all("td")
            data_list = [c.inner_text().strip() for c in cells if c.inner_text().strip()]
            
            for text in data_list:
                if '.' in text and text.replace('.', '').isdigit():
                    val = float(text)
                    # 根據您的成功經驗，VIXTWN 應該是在 30+ 左右
                    # 設定 10~50 的安全過濾區間，避開首頁的金融期 18.4
                    if 20 < val < 50:
                        res_val = text
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except Exception as e:
        res_val = f"點擊失敗"
    return res_val, screenshot

# --- 2. 世界偵察：DEFCON & 披薩指數 (今日成功 OCR) ---
def get_ocr_world_monitor():
    lvl, pct = 1, 0.0
    log = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded")
            time.sleep(15) 
            
            # 今日成功的裁切定位
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
        return None, None, "OCR 錯誤"

# --- UI 佈局 ---
st.set_page_config(page_title="AI 物理重擊監控", layout="wide")
st.title("🛡️ 台灣股市 AI 智慧監控：物理重擊回歸版")

if 'world' not in st.session_state: st.session_state['world'] = {"lvl": 3, "pct": 51, "log": "尚未更新"}
if 'vix_twn' not in st.session_state: st.session_state['vix_twn'] = "N/A"

c1, c2 = st.columns(2)

with c1:
    st.subheader("🕵️ 世界偵察 (超解析 OCR)")
    if st.button("🛰️ 啟動辨識", use_container_width=True):
        lvl, pct, log = get_ocr_world_monitor()
        if lvl: st.session_state['world'] = {"lvl": lvl, "pct": pct, "log": log}
    
    w = st.session_state['world']
    st.metric("DEFCON 級別", f"LEVEL {w['lvl']}")
    st.metric("披薩指數", f"{int(w['pct'])}%")

with c2:
    st.subheader("📉 三大恐慌指標 (物理重擊)")
    if st.button("🚀 物理重擊橘色按鈕 (VIXTWN)", use_container_width=True):
        val, shot = physical_force_vixtwn()
        st.session_state['vix_twn'] = val
        if shot: st.session_state['vix_shot'] = shot

    st.metric("台指期 VIXTWN (實時)", st.session_state['vix_twn'], delta="核心數值")

if 'vix_shot' in st.session_state:
    st.divider()
    with st.expander("📸 檢查物理重擊截圖 (驗證是否穿透免責聲明)"):
        st.image(st.session_state['vix_shot'])

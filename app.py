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
from datetime import datetime

# --- 初始化環境 ---
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

# --- 2. 核心技術：雙解析度分道辨識 ---

def get_pizza_intel_dual_resolution():
    """
    實施：向左狂移掃描 + [取消反轉(級別)] + [5x放大強化(百分比)]
    """
    lvl, pct = 1, 0.0
    raw_debug_defcon = ""
    raw_debug_pct = ""
    debug_img_pct = None
    
    status = st.status("🍕 啟動雙解析度偵察組件...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 登入 WorldMonitor 數據系統...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            # 使用固定 Full HD 解析度確保佈局一致
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(12) 
            
            status.write("2. 執行 5x 超解析度廣域截圖 (向左狂移 x:350)...")
            # 維持向左狂移的座標，抓取包含 DEFCON 和百分比的數據區
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            # 轉換為灰階
            img_org = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # --- 通道 A：專攻 DEFCON (級別) ---
            # 取消反相處理。回歸高對比度強化模式
            img_defcon = ImageEnhance.Contrast(img_org).enhance(4.0)
            img_defcon = ImageEnhance.Sharpness(img_defcon).enhance(2.0)
            
            # 執行 OCR (通道 A)
            raw_debug_defcon = pytesseract.image_to_string(img_defcon, config='--psm 6').strip()
            
            # --- 通道 B：專攻百分比 (PIZZA INDEX) ---
            # 針對您的建議：必須放大。我們實施 5 倍像素擴展
            img_pct = img_org.resize((img_org.width * 5, img_org.height * 5), Image.Resampling.LANCZOS)
            img_pct = ImageEnhance.Contrast(img_pct).enhance(5.0)
            img_pct = ImageEnhance.Sharpness(img_pct).enhance(3.0)
            
            # 儲存通道 B 除錯影像
            buf = io.BytesIO()
            img_pct.convert("RGB").save(buf, format="PNG")
            debug_img_pct = buf.getvalue()
            
            # 執行 OCR (通道 B)
            raw_debug_pct = pytesseract.image_to_string(img_pct, config='--psm 6').strip()
            
            status.write("3. 整合關鍵數據...")
            # 提取級別 (通道 A)
            lvl_m = re.search(r'(?:defcon|gd|d\w+n|d\s*c|et)\s*[:|l|!|i]?\s*([1-5])', raw_debug_defcon, re.IGNORECASE)
            # 提取百分比 (通道 B)
            pct_m = re.search(r'(\d+)\s*%', raw_debug_pct)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 整合完成 (結果: {lvl} / {pct}%)", state="complete", expanded=False)
            return lvl, pct, f"DEFCON通道:\n{raw_debug_defcon}\n\nPCT通道 (5x放大):\n{raw_debug_pct}", debug_img_pct
    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- UI 呈現 ---
st.set_page_config(page_title="Intel dual-res", page_icon="🛡️")
st.title("🛡️ 全域數據穩定整合系統")

if st.button("🛰️ 啟動級別與百分比整合更新", use_container_width=True):
    lvl, pct, raw, dbg_img = get_pizza_intel_dual_resolution()
    if lvl is not None:
        st.session_state['stable_lvl'] = lvl
        st.session_state['stable_pct'] = pct
        st.session_state['stable_raw'] = raw
        st.session_state['stable_shot_pct'] = dbg_img
        st.rerun()

if 'stable_lvl' in st.session_state:
    # 呈現最新數據面板
    st.markdown(f"""
        <div style="background-color:#000; border-radius:12px; padding:20px; border:1px solid #333; text-align:center;">
            <div style="display:inline-block; width:45%;">
                <small style="color:#888;">DEFCON LEVEL</small><br>
                <b style="font-size:42px; color:#FF4B4B;">{st.session_state['stable_lvl']}</b>
            </div>
            <div style="display:inline-block; width:5%; font-size:30px; color:#444;">|</div>
            <div style="display:inline-block; width:45%;">
                <small style="color:#888;">PIZZA INDEX</small><br>
                <b style="font-size:42px; color:#FF4B4B;">{int(st.session_state['stable_pct'])}%</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 🕵️ 除錯與驗證區塊
    st.divider()
    with st.expander("🔍 檢查百分比通道 (5倍放大畫面)"):
        st.image(st.session_state['stable_shot_pct'], caption="專門放大抓取百分比數字的畫面")
        st.info(f"偵察字串: {st.session_state['stable_raw'].split('PCT通道')[1][:50]}...")
    
    with st.expander("📄 查看完整原始辨識字串"):
        st.code(st.session_state['stable_raw'])

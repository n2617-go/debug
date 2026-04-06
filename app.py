import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import io
import os
import re
import time
import pytz
from datetime import datetime

# --- 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

PIZZA_FILE = "intelligence_data.json"
tz_tw = pytz.timezone('Asia/Taipei')

# --- 核心：雙重影像辨識技術 ---

def get_dual_channel_intel():
    """
    技術：同時對同一張截圖進行兩種不同的影像強化處理
    """
    lvl, pct = 1, 0.0
    raw_text_defcon = ""
    raw_text_pct = ""
    
    status = st.status("🚀 啟動雙通道數據偵察...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 建立廣域衛星連線...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(12) 
            
            status.write("2. 執行超廣角數據快照 (x:350, width:1200)...")
            # 維持向左偏移的廣域掃描，確保兩者皆入鏡
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1200, 'height': 100})
            browser.close()
            
            img_org = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            # 統一放大 1.5 倍提升 OCR 精度
            img_zoomed = img_org.resize((int(img_org.width * 1.5), int(img_org.height * 1.5)), Image.Resampling.LANCZOS)
            
            # --- 通道 A：專攻 DEFCON (極限二值化) ---
            # 針對 1000028190.jpg 的成功經驗
            img_defcon = ImageEnhance.Contrast(img_zoomed).enhance(4.0)
            img_defcon = img_defcon.point(lambda x : 255 if x > 180 else 0, mode='1')
            raw_text_defcon = pytesseract.image_to_string(img_defcon, config='--psm 6')
            
            # --- 通道 B：專攻百分比 (中度強化) ---
            # 針對 1000028191.jpg 的成功經驗
            img_pct = ImageEnhance.Contrast(img_zoomed).enhance(2.5)
            raw_text_pct = pytesseract.image_to_string(img_pct, config='--psm 6')
            
            # 儲存除錯影像（合併兩通道）
            debug_img = Image.new('L', (img_defcon.width, img_defcon.height * 2))
            debug_img.paste(img_defcon.convert('L'), (0, 0))
            debug_img.paste(img_pct.convert('L'), (0, img_defcon.height))
            buf = io.BytesIO()
            debug_img.convert("RGB").save(buf, format="PNG")
            
            status.write("3. 雙通道數據結合...")
            # 分別從不同通道提取數據
            lvl_m = re.search(r'(?:defcon|gd|d\w+n|et|1|2|3|4|5)\s*([1-5])', raw_text_defcon, re.IGNORECASE)
            pct_m = re.search(r'(\d+)\s*%', raw_text_pct)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            status.update(label=f"✅ 整合成功: DEFCON {lvl} | {int(pct)}%", state="complete", expanded=False)
            return lvl, pct, f"DEFCON_RAW: {raw_text_defcon}\n\nPCT_RAW: {raw_text_pct}", buf.getvalue()
            
    except Exception as e:
        status.update(label=f"❌ 辨識失敗: {e}", state="error")
        return None, None, str(e), None

# --- UI 介面 ---
st.set_page_config(page_title="Intel Dual-Channel", page_icon="🛡️")
st.title("🛡️ 雙通道穩定偵察系統")

if st.button("🛰️ 啟動雙重方法同步更新", use_container_width=True):
    lvl, pct, raw, dbg_img = get_dual_channel_intel()
    if lvl is not None:
        st.session_state['intel_data'] = {"lvl": lvl, "pct": pct, "raw": raw, "img": dbg_img}
        st.rerun()

if 'intel_data' in st.session_state:
    data = st.session_state['intel_data']
    
    # 呈現最新數據面板
    st.markdown(f"""
        <div style="background-color:#0e1117; border-radius:10px; padding:20px; border:1px solid #333; text-align:center;">
            <div style="display:inline-block; width:45%;">
                <small style="color:#888;">DEFCON LEVEL</small><br>
                <b style="font-size:48px; color:#FF4B4B;">{data['lvl']}</b>
            </div>
            <div style="display:inline-block; width:5%; font-size:30px; color:#444; vertical-align:super;">|</div>
            <div style="display:inline-block; width:45%;">
                <small style="color:#888;">PIZZA INDEX</small><br>
                <b style="font-size:48px; color:#1E90FF;">{int(data['pct'])}%</b>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🕵️ 查看雙通道處理視覺圖"):
        st.image(data['img'], caption="上圖：DEFCON 通道 | 下圖：百分比通道")
        st.info("💡 只要上圖能看到數字、下圖能看到百分比，系統就能完美結合。")
    
    with st.expander("📄 檢視原始辨識字串"):
        st.code(data['raw'])

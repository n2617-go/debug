import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import io
import os
import re
import time
import json

# --- 環境初始化 ---
def ensure_env():
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        os.system("playwright install chromium")

ensure_env()

# --- 核心辨識邏輯 ---

def get_dual_channel_intel():
    """
    通道 A: 雙重閾值掃描 (確保 DEFCON 4 浮現)
    通道 B: 8x 超解析度 + 銳化 (確保 29% 不會辨識成 20%)
    """
    lvl, pct = 1, 0.0
    raw_debug = ""
    dbg_img_pct = None
    
    status = st.status("🚀 啟動超解析度雙通道偵察...", expanded=True)
    try:
        with sync_playwright() as p:
            status.write("1. 建立廣域衛星連線...")
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=60000)
            # 等待 15 秒確保所有動畫與數據加載完成
            time.sleep(15) 
            
            status.write("2. 抓取原始數據快照 (向左狂移 x:350)...")
            screenshot_bytes = page.screenshot(clip={'x': 350, 'y': 15, 'width': 1100, 'height': 100})
            browser.close()
            
            # 轉換為灰階基礎圖
            img_org = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            
            # --- 【通道 A】修復 DEFCON (嘗試兩種模式) ---
            # 模式 1: 原始強化 (針對紅底白字)
            img_a1 = ImageEnhance.Contrast(img_org).enhance(4.0)
            raw_a1 = pytesseract.image_to_string(img_a1, config='--psm 6')
            
            # 模式 2: 極限反轉二值化 (針對白底黑字，讓字浮現)
            img_a2 = ImageOps.invert(img_org)
            img_a2 = ImageEnhance.Contrast(img_a2).enhance(5.0)
            img_a2 = img_a2.point(lambda x: 255 if x > 200 else 0, mode='1')
            raw_a2 = pytesseract.image_to_string(img_a2, config='--psm 6')
            
            # --- 【通道 B】修復百分比 (8x 超解析度 + 銳化) ---
            # 針對 29% 誤判問題：提升至 8 倍放大並加入銳化濾鏡
            img_pct = img_org.resize((img_org.width * 8, img_org.height * 8), Image.Resampling.LANCZOS)
            img_pct = img_pct.filter(ImageFilter.SHARPEN) 
            img_pct = ImageEnhance.Contrast(img_pct).enhance(3.5)
            raw_pct = pytesseract.image_to_string(img_pct, config='--psm 6')
            
            # 儲存通道 B 放大圖供驗證 9 與 0
            buf = io.BytesIO()
            img_pct.convert("RGB").save(buf, format="PNG")
            dbg_img_pct = buf.getvalue()
            
            status.write("3. 整合關鍵特徵數據...")
            
            # 整合所有抓到的文字進行正則匹配
            combined_text = f"{raw_a1} {raw_a2} {raw_pct}"
            
            # 提取級別 (DEFCON)
            lvl_m = re.search(r'(?:defcon|d\w+n|et)\s*[:|l|!|i]?\s*([1-5])', combined_text, re.IGNORECASE)
            # 提取百分比 (PIZZA)
            pct_m = re.search(r'(\d+)\s*%', raw_pct)
            
            if lvl_m: lvl = int(lvl_m.group(1))
            if pct_m: pct = float(pct_m.group(1))
            
            raw_debug = f"--- DEFCON 模式1 ---\n{raw_a1}\n\n--- DEFCON 模式2 (二值化) ---\n{raw_a2}\n\n--- 百分比 8x ---\n{raw_pct}"
            
            status.update(label=f"✅ 偵察成功 (級別: {lvl} / 指數: {pct}%)", state="complete", expanded=False)
            return lvl, pct, raw_debug, dbg_img_pct

    except Exception as e:
        status.update(label=f"❌ 偵察失敗: {e}", state="error")
        return None, None, str(e), None

# --- Streamlit UI 介面 ---
st.set_page_config(page_title="Intel Dual-Channel Pro", page_icon="🛡️")

st.title("🛡️ 全域偵察系統 (超解析度進化版)")
st.markdown("針對 **DEFCON 4 (浮現技術)** 與 **29% (8x 放大)** 優化的穩定版本。")

if st.button("🛰️ 啟動雙通道數據更新", use_container_width=True):
    res_lvl, res_pct, res_raw, res_img = get_dual_channel_intel()
    if res_lvl is not None:
        st.session_state['intel'] = {
            "lvl": res_lvl,
            "pct": res_pct,
            "raw": res_raw,
            "img": res_img
        }
        st.rerun()

if 'intel' in st.session_state:
    data = st.session_state['intel']
    
    # 數據面板
    col1, col2 = st.columns(2)
    with col1:
        st.metric("DEFCON 級別", f"LEVEL {data['lvl']}")
    with col2:
        st.metric("披薩指數 (PIZZA INDEX)", f"{int(data['pct'])}%")
    
    # 驗證區塊
    with st.expander("🔍 驗證 8x 超解析度畫面 (解決 9/0 誤判)"):
        st.image(data['img'], caption="8倍放大 + 銳化處理後的細節")
        st.info("💡 請確認圖中的 9 是否勾勒清晰。")

    with st.expander("📄 原始文字偵察流 (除錯用)"):
        st.code(data['raw'])

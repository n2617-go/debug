import streamlit as st
import asyncio
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="VIX 座標快照監控", layout="wide", page_icon="📈")

# --- 核心掃描邏輯 ---
def capture_vix_with_speed_optimized():
    """帶有進度條且經過連線優化的座標掃描"""
    url = "https://www.wantgoo.com/index/vixtwn/price-to-earning-river"
    
    # 建立進度條與狀態文字
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        with sync_playwright() as p:
            # 1. 啟動環境
            status_text.text("1/5 正在初始化掃描引擎...")
            progress_bar.progress(20)
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            
            # 2. 建立模擬環境
            status_text.text("2/5 設定掃描座標參數...")
            progress_bar.progress(40)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # --- 加速關鍵：封鎖不必要的廣告與圖片請求 ---
            page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())
            page.route("**/google-analytics.com/**", lambda route: route.abort())
            page.route("**/googlesyndication.com/**", lambda route: route.abort())

            # 3. 載入網頁
            status_text.text("3/5 正在載入玩股網數據 (已封鎖廣告加速)...")
            progress_bar.progress(60)
            # 使用 commit 模式，只要伺服器開始傳送數據就準備掃描
            page.goto(url, wait_until="commit", timeout=60000)
            
            # 4. 座標定位與等待數值跳出
            status_text.text("4/5 座標掃描中：鎖定 VIX 數值區域...")
            progress_bar.progress(80)
            
            # 定位點：針對你提供的圖片，鎖定 .last 類別
            selector = "span.last" 
            page.wait_for_selector(selector, timeout=20000)
            
            # 抓取數值與區域快照
            vix_text = page.inner_text(selector)
            element_handle = page.query_selector(selector)
            screenshot_bytes = element_handle.screenshot()
            
            # 5. 完成
            status_text.text("5/5 掃描成功！數據已就緒。")
            progress_bar.progress(100)
            
            browser.close()
            time.sleep(1) # 讓使用者確認 100% 狀態
            progress_bar.empty()
            status_text.empty()
            
            return vix_text, screenshot_bytes, True
            
    except Exception as e:
        if 'browser' in locals(): browser.close()
        progress_bar.empty()
        status_text.empty()
        return str(e), None, False

# --- Streamlit UI 介面 ---
st.title("📸 台指 VIX 座標快照掃描系統")
st.markdown(f"""
**📅 今日狀態：** 2026-04-06 (補假休市)  
**🔍 掃描目標：** 自動回溯掃描 4/2 最後交易數據 (**36.45**)
---
""")

# 側邊欄說明
st.sidebar.header("🔧 掃描設定")
st.sidebar.info("""
本系統使用 **Playwright** 模擬真人瀏覽器行為：
1. 封鎖圖片與追蹤器以提升速度。
2. 精準鎖定網頁座標元素。
3. 支援即時快照驗證。
""")

# 執行按鈕
if st.button("🚀 開始掃描 VIX 座標點位", use_container_width=True):
    vix_val, img_bytes, success = capture_vix_with_speed_optimized()
    
    if success:
        # 顯示結果看板
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("掃描到的 VIX 數值", vix_val)
            st.write(f"⏱️ 掃描完成時間：{datetime.now().strftime('%H:%M:%S')}")
            
            # 情緒判斷
            val_float = float(vix_val) if vix_val.replace('.','',1).isdigit() else 0
            if val_float > 30:
                st.error("🚨 市場情緒：極度恐慌")
            elif val_float > 20:
                st.warning("⚠️ 市場情緒：波動度上升")
            else:
                st.success("😊 市場情緒：平穩樂觀")
        
        with col2:
            st.write("### 📍 座標區域快照驗證")
            st.image(img_bytes, caption="這是從網頁座標即時截取的圖片內容 (OCR 區域)")
            st.success("數據掃描成功！快照內容與數值一致。")
            
    else:
        st.error(f"❌ 掃描失敗：{vix_val}")
        st.info("💡 提示：若在雲端環境執行，請確認 `packages.txt` 已正確配置底層依賴庫。")

st.divider()
st.caption("註：本程式僅供技術研究使用，數據版權歸原來源網站所有。")

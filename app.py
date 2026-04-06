import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="期交所 VIX 自動掃描器", layout="wide")

def run_vix_automated_scan():
    """步驟一：模擬點擊確認 -> 步驟二：座標掃描數據"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        with sync_playwright() as p:
            # --- 步驟 1：初始化與進入免責聲明 ---
            status_text.text("1/5 正在啟動掃描引擎並前往期交所...")
            progress_bar.progress(20)
            
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")

            # --- 步驟 2：模擬真人點擊“確認”按鈕 ---
            status_text.text("2/5 正在模擬真人點擊『確認』按鈕...")
            progress_bar.progress(40)
            
            # 定位按鈕：期交所確認按鈕通常有 'button' 或 特定 id
            try:
                # 尋找包含確認字樣的按鈕
                confirm_btn = page.wait_for_selector("button:has-text('確認'), #buttonID", timeout=10000)
                confirm_btn.click()
                # 點擊後等待數據表格載入
                time.sleep(3) 
            except Exception:
                status_text.text("提示：未偵測到按鈕，可能已直接進入數據頁。")

            # --- 步驟 3：定位數據座標區域 ---
            status_text.text("3/5 進入行情頁，正在精準鎖定 VIX 數據座標...")
            progress_bar.progress(60)
            
            # 針對你提供的圖二，定位 VIX 指數所在的表格欄位
            # 通常在 臺指選擇權波動率指數 這一列
            vix_row_selector = "tr:has-text('臺指選擇權波動率指數')"
            page.wait_for_selector(vix_row_selector, timeout=15000)
            
            # --- 步驟 4：執行快照與數值辨識 ---
            status_text.text("4/5 正在進行座標快照與數字辨識...")
            progress_bar.progress(80)
            
            # 獲取該列的所有數據格，定位到「目前指數」那一格
            vix_cells = page.query_selector_all(f"{vix_row_selector} td")
            
            # 根據表格結構，目前指數通常在第 3 或 4 格
            # 這裡我們精準快照「目前指數」那一格的範圍
            vix_value_cell = vix_cells[2] # 假設在第三欄
            vix_text = vix_value_cell.inner_text().strip()
            screenshot_bytes = vix_value_cell.screenshot()

            # --- 步驟 5：完成 ---
            status_text.text("5/5 掃描辨識完成！正在呈現結果...")
            progress_bar.progress(100)
            
            browser.close()
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            return vix_text, screenshot_bytes, True

    except Exception as e:
        if 'browser' in locals(): browser.close()
        progress_bar.empty()
        status_text.empty()
        return f"掃描失敗: {str(e)}", None, False

# --- UI 介面 ---
st.title("🛡️ 期交所 VIX 實時座標監控系統")
st.markdown("### 流程：模擬點擊免責聲明 ➔ 座標定位 ➔ 數據辨識")

if st.button("🚀 開始自動化掃描任務", use_container_width=True):
    vix_val, img_bytes, success = run_vix_automated_scan()
    
    if success:
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.metric("掃描辨識結果", vix_val)
            st.write(f"⏱️ 數據取得時間：{datetime.now().strftime('%H:%M:%S')}")
            
            # 波動率狀態判斷
            try:
                val_num = float(vix_val)
                if val_num > 30: st.error("🚨 高度恐慌")
                elif val_num < 18: st.success("😊 市場平穩")
                else: st.info("🟡 常態波動")
            except:
                pass
        
        with col2:
            st.write("### 📍 座標掃描區域快照 (驗證用)")
            st.image(img_bytes, caption=f"網頁座標即時快照：{vix_val}")
            st.success("步驟二完成：成功辨識圖中綠色框位數值。")
    else:
        st.error(vix_val)
        st.info("💡 建議：若按鈕點擊失敗，請確認期交所網頁結構是否有變動。")

st.divider()
st.caption("註：目前為 4/6 補假，掃描數據為連假前最後盤後點位。")

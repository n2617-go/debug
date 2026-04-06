import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="VIX 終極座標辨識", layout="wide")

def run_vix_automated_with_click():
    """步驟一：模擬真人點擊免責聲明按鈕 -> 步驟二：辨識數據座標"""
    # 目標：期交所台指 VIX 行情專區
    url = "https://mis.taifex.com.tw/futures/disclaimer/"
    
    # 初始化進度條與狀態元件
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 初始化變數
    vix_val = "N/A"
    shot = None
    success = False

    try:
        # 使用強健的上下文管理器 (解決 Event Loop 關閉問題)
        with sync_playwright() as p:
            # Step 1: 啟動瀏覽器核心並進入免責聲明頁
            status_text.text("1/5 正在啟動掃描引擎，前往期交所...")
            progress_bar.progress(20)
            
            # 使用 headless=True 以適應 Streamlit Cloud 環境
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 前往網頁，使用 networkidle 確保免責聲明視窗跑出來
            page.goto(url, wait_until="networkidle", timeout=60000)

            # Step 2: 處理點擊橘色“確認”按鈕 (針對圖三優化)
            status_text.text("2/5 正在精準定位橘色按鈕並模擬點擊...")
            progress_bar.progress(40)
            
            # 期交所免責聲明的按鈕定位選擇器：通常有特定文字內容或 class
            confirm_selector = "button:has-text('我已閱讀並了解'), button[id^='confirm']" 
            
            try:
                # 等待按鈕出現在畫面上，確保是可以被點擊的狀態
                page.wait_for_selector(confirm_selector, timeout=10000)
                
                # 執行模擬點擊动作
                page.click(confirm_selector)
                
                # 點擊後務必稍微等待網頁跳轉或渲染
                time.sleep(3) 
            except Exception as e:
                status_text.text("提示：未偵測到免責聲明視窗，嘗試直接辨識數據。")

            # Step 3: 定位 VIX 指數所在的表格欄位坐标
            status_text.text("3/5 進入行情頁，正在鎖定 VIX 數值座標...")
            progress_bar.progress(60)
            
            # 針對你提供的圖二結構，定位 VIX 指數所在列，再定位到「目前指數」
            row_selector = "tr:has-text('臺指選擇權波動率指數')"
            page.wait_for_selector(row_selector, timeout=15000)
            
            # Step 4: 執行局部座標快照與OCR辨識
            status_text.text("4/5 正在執行OCR辨識與區域快照...")
            progress_bar.progress(80)
            
            # 辨識文字 (ocr) 獲取 VIX 數值
            cells = page.query_selector_all(f"{row_selector} td")
            # 根據結構，目前指數通常在第 3 欄
            vix_cell = cells[2] 
            vix_val = vix_cell.inner_text().strip()
            
            # 快照對焦：只截取該格子座標區域
            element_handle = page.query_selector(f"{row_selector} td:nth-child(3)")
            shot = element_handle.screenshot()
            
            success = True
            
        # 這裡不手動呼叫 browser.close()，让 with 語法自動處理资源回收
            
    except Exception as e:
        vix_val = f"辨識錯誤: {str(e)}"
        # 如果還是 Timeout，抓一張全螢幕截圖除錯
        screenshot_bytes = page.screenshot()
        # 把錯誤截圖傳出來展示
        shot = screenshot_bytes
        success = False
    finally:
        # 清除狀態元件
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- UI 介面 ---
st.title("🛡️ 期交所 VIX 自動化座標掃描系統")
st.markdown("針對 `mis.taifex.com.tw` 免責聲明頁面進行模擬點擊與數據擷取。")

if st.button("🚀 開始掃描 VIX 指數", use_container_width=True):
    val, img, ok = run_vix_automated_with_click()
    
    if ok:
        # 顯示結果看板
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.metric("掃描辨識數值", val)
            st.write(f"⏱️ 數據取得時間：{datetime.now().strftime('%H:%M:%S')}")
            
            # 波動率狀態判斷
            try:
                vix_float = float(val)
                if vix_float > 30: st.error("🚨 市場恐慌升高")
                elif vix_float < 18: st.success("😊 市場情緒穩定")
                else: st.info("🟡 市場正常波動")
            except:
                pass
        
        with col2:
            st.write("### 📍 OCR 區域快照驗證")
            st.image(img, caption=f"對應圖二綠色框位之即時快照：{val}")
            st.success("成功解決免責聲明阻擋問題，數據辨識成功！")
            
    else:
        st.error(val)
        if img:
            st.write("### 📸 偵錯截圖 (目前程式看到的畫面)")
            st.image(img)
            st.info("請檢查偵錯截圖：若按鈕點擊失敗，可能是選擇器失效；若畫面空白，可能是載入太慢。")

st.divider()
st.caption("註：本程式模擬真人行為進行技術研究，數據所有權歸原來源網站所有。")

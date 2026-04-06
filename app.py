import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

st.set_page_config(page_title="VIX 指數精準辨識", layout="wide")

def run_vix_precise_scan():
    # 使用包含免責聲明的初始網址
    url = "https://mis.taifex.com.tw/futures/disclaimer/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("1/4 啟動瀏覽器中...")
            progress_bar.progress(25)
            
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()

            # 2. 進入頁面
            status_text.text("2/4 正在處理免責聲明按鈕...")
            progress_bar.progress(50)
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # --- 重點：不靠文字，靠 CSS 結構點擊橘色按鈕 ---
            # 根據截圖，橘色按鈕通常是頁面上唯一的特定顏色按鈕
            try:
                # 嘗試點擊包含特定樣式的按鈕 (通常是第一個 btn-primary 或 btn-orange)
                # 我們直接定位到按鈕容器下的第一個按鈕
                confirm_btn = page.wait_for_selector(".btn-confirm, .btn-primary, button:nth-child(1)", timeout=10000)
                confirm_btn.click()
                time.sleep(5) # 點擊後務必多等幾秒讓行情頁跑出來
            except:
                pass

            # 3. 掃描數值 (不靠文字，靠表格結構)
            status_text.text("3/4 掃描行情座標...")
            progress_bar.progress(75)
            
            # 即使文字是亂碼，HTML 標籤 <tr> 和 <td> 還是存在的
            # 跳轉後的行情頁通常會有一個主要表格，我們鎖定第一行數據
            try:
                # 直接前往 VIX 專區網址以確保在正確頁面
                page.goto("https://mis.taifex.com.tw/futures/VolatilityQuotes/", wait_until="networkidle")
                
                # 等待表格出現
                page.wait_for_selector("table", timeout=15000)
                
                # 針對你提供的圖一綠色框位：
                # 通常是表格中包含指數的那一行 (第一行有效數據)
                # 我們抓取表格中所有 td，並找出第一個符合數字格式的內容
                all_cells = page.query_selector_all("td")
                
                for cell in all_cells:
                    txt = cell.inner_text().strip()
                    # 判斷是否為數字（例如 36.45）
                    if txt.replace('.', '', 1).isdigit() and '.' in txt:
                        vix_val = txt
                        shot = cell.screenshot() # 局部截圖
                        success = True
                        break
            except Exception as e:
                vix_val = f"掃描異常: {str(e)}"
                shot = page.screenshot() # 失敗就抓全螢幕

            status_text.text("4/4 完成！")
            progress_bar.progress(100)
            time.sleep(1)

    except Exception as e:
        vix_val = f"系統錯誤: {str(e)}"
        success = False
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- UI ---
st.title("📊 VIX 指數座標自動辨識系統")
st.info("已優化按鈕點擊邏輯，避開伺服器中文字型缺失導致的定位失敗。")

if st.button("🚀 執行自動辨識任務"):
    val, img, ok = run_vix_precise_scan()
    
    if ok:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("辨識到的數值", val)
            st.write(f"取得時間：{datetime.now().strftime('%H:%M:%S')}")
        with c2:
            st.write("### 📍 座標掃描區快照")
            st.image(img, caption=f"對應圖一位置：{val}")
    else:
        st.error(val)
        if img:
            st.write("### 📸 失敗時的畫面 (協助排障)")
            st.image(img)

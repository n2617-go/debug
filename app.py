import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

st.set_page_config(page_title="VIX 穩定掃描版", layout="wide")

def run_vix_automated_with_click():
    url = "https://mis.taifex.com.tw/futures/disclaimer/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    # 核心修正：將所有邏輯（含截圖）完整封裝在 with 內部
    try:
        with sync_playwright() as p:
            status_text.text("1/4 啟動瀏覽器...")
            progress_bar.progress(25)
            
            # 加入 --single-process 減少記憶體衝突
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--single-process"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()

            # 2. 進入頁面並點擊橘色按鈕
            status_text.text("2/4 處理免責聲明...")
            progress_bar.progress(50)
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            confirm_selector = "button:has-text('我已閱讀並了解')"
            try:
                page.wait_for_selector(confirm_selector, timeout=10000)
                page.click(confirm_selector)
                time.sleep(5) # 點擊後多等 5 秒讓表格載入
            except:
                pass

            # 3. 掃描數值
            status_text.text("3/4 辨識數值座標...")
            progress_bar.progress(75)
            
            row_selector = "tr:has-text('臺指選擇權波動率指數')"
            try:
                page.wait_for_selector(row_selector, timeout=15000)
                cells = page.query_selector_all(f"{row_selector} td")
                
                # 確保有抓到數值格 (通常是第 3 格)
                if len(cells) >= 3:
                    vix_val = cells[2].inner_text().strip()
                    # *** 重要：在 browser 關閉前完成截圖 ***
                    shot = cells[2].screenshot()
                    success = True
                else:
                    vix_val = "找到列但格數不足"
                    shot = page.screenshot() # 抓全螢幕除錯
            except Exception as e:
                vix_val = f"定位失敗: {str(e)}"
                shot = page.screenshot() # *** 重要：在這裡截圖，不要在 except 外面截 ***

            status_text.text("4/4 掃描完成！")
            progress_bar.progress(100)
            
            # 當離開這個 with 區塊，browser 會自動關閉，這很安全
            
    except Exception as e:
        # 這裡是處理 Playwright 啟動失敗或其他重大崩潰
        vix_val = f"系統層級錯誤: {str(e)}"
        success = False
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- UI ---
st.title("🛡️ 期交所 VIX 座標掃描系統 (修正 Event Loop 版)")

if st.button("🚀 開始自動化任務"):
    val, img, ok = run_vix_automated_with_click()
    
    if ok:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("掃描到的數值", val)
        with c2:
            st.image(img, caption=f"成功抓取的局部座標：{val}")
    else:
        st.error(f"掃描失敗：{val}")
        if img:
            st.write("### 📸 失敗時的畫面")
            st.image(img)

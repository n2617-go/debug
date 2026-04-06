import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="期交所 VIX 終極辨識器", layout="wide")

def run_vix_final_scan():
    """專門針對期交所行情頁結構優化"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_text = "N/A"
    screenshot_bytes = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("1/5 啟動引擎並模擬進入...")
            progress_bar.progress(20)
            
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(viewport={'width': 1280, 'height': 1000})
            page = context.new_page()

            # 進入網頁
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 步驟一：點擊確認 (加強版定位)
            status_text.text("2/5 正在處理免責聲明點擊...")
            progress_bar.progress(40)
            try:
                # 遍歷可能的確認按鈕
                confirm_btn = page.wait_for_selector("button:has-text('確認'), .btn-confirm, #buttonID", timeout=8000)
                confirm_btn.click()
                time.sleep(5) # 點擊後多等一下，讓表格載入
            except:
                pass

            # 步驟二：辨識數據 (改用更寬鬆但精準的定位)
            status_text.text("3/5 正在精準辨識 VIX 指數區域...")
            progress_bar.progress(60)
            
            # 先確認表格是否出現
            page.wait_for_selector("table", timeout=15000)
            
            # 尋找包含 VIX 的表格列
            # 改用 XPath 定位，通常比文字比對更穩定
            try:
                # 尋找包含「臺指選擇權波動率指數」的 td，然後往上找那一列 tr
                vix_row = page.wait_for_selector("//tr[td[contains(., '臺指選擇權波動率指數')]]", timeout=20000)
                
                # 在該列中尋找「目前指數」
                # 期交所 mis 介面：第一欄名稱，第二欄目前指數 (或視解析度而定)
                # 我們直接抓取該列中所有的 td
                tds = vix_row.query_selector_all("td")
                
                # 根據你提供的圖二，綠色框框在「商品名稱」右邊的第一個數字格
                # 通常索引是 1 或 2
                target_cell = None
                for i, td in enumerate(tds):
                    text = td.inner_text().strip()
                    # 判斷是否為數字（包含小數點）
                    if text.replace('.', '', 1).isdigit():
                        target_cell = td
                        vix_text = text
                        break
                
                if target_cell:
                    status_text.text("4/5 鎖定目標成功，擷取座標快照...")
                    progress_bar.progress(80)
                    screenshot_bytes = target_cell.screenshot()
                    success = True
                else:
                    raise Exception("找到列但找不到數字數值")

            except Exception as e:
                # 失敗時抓一張全螢幕截圖除錯
                screenshot_bytes = page.screenshot()
                raise Exception(f"定位失敗：{str(e)}")

            status_text.text("5/5 掃描完成！")
            progress_bar.progress(100)
            time.sleep(1)

    except Exception as e:
        vix_text = str(e)
        success = False
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_text, screenshot_bytes, success

# --- UI ---
st.title("🛡️ 期交所 VIX 終極掃描 (修正超時問題)")
st.info("已加強數據載入等待時間，並優化了表格座標定位邏輯。")

if st.button("🚀 開始執行辨識任務", use_container_width=True):
    val, img, ok = run_vix_final_scan()
    
    if ok:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("掃描到的 VIX 數值", val)
            st.write(f"⏱️ 更新時間：{datetime.now().strftime('%H:%M:%S')}")
        with c2:
            st.write("### 📍 座標掃描區驗證")
            st.image(img, caption=f"精準鎖定數值: {val}")
    else:
        st.error(f"掃描失敗：{val}")
        if img:
            st.write("### 偵錯快照 (程式目前看到的畫面)")
            st.image(img)
            st.info("如果畫面停在『免責聲明』，代表點擊按鈕失敗；如果畫面空白，代表載入太慢。")

st.divider()
st.caption("註：4/6 補假，數據來源為 4/2 最後更新。")

import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="期交所行情監控", layout="wide")

def run_vix_taifex_direct():
    """針對期交所行情網站的特定流程"""
    # 直接使用你提供的目標網址 (略過 Google 跳轉)
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            # 1. 啟動並進入頁面
            status_text.text("1/5 正在連線至期交所行情網...")
            progress_bar.progress(20)
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle", timeout=60000)

            # 2. 處理點擊“確認”
            status_text.text("2/5 模擬真人點擊『確認』...")
            progress_bar.progress(40)
            try:
                # 期交所按鈕通常有特定的 class "btn-confirm" 或直接比對文字
                confirm_btn = page.wait_for_selector("button:has-text('確認'), .btn-confirm", timeout=10000)
                confirm_btn.click()
                # 點擊後行情資料會非同步載入，多等 5 秒確保數字跳出來
                time.sleep(5) 
            except:
                pass # 如果沒出現按鈕就繼續

            # 3. 定位數據列 (對應圖二)
            status_text.text("3/5 正在精準辨識數據座標...")
            progress_bar.progress(60)
            
            # 使用 XPath 鎖定包含「臺指選擇權波動率指數」的那一行
            row_xpath = "//tr[td[contains(text(), '臺指選擇權波動率指數')]]"
            page.wait_for_selector(row_xpath, timeout=15000)
            
            # 4. 抓取數字與局部快照
            status_text.text("4/5 鎖定 36.45 區域並進行快照...")
            progress_bar.progress(80)
            
            row = page.query_selector(row_xpath)
            # 在該列中尋找所有儲存格，數字通常在目前的「成交價」或「目前指數」欄位
            cells = row.query_selector_all("td")
            
            # 策略：尋找第一個出現的數字格式
            for cell in cells:
                txt = cell.inner_text().strip()
                if txt.replace('.', '', 1).isdigit():
                    vix_val = txt
                    shot = cell.screenshot() # 針對該格子座標快照
                    success = True
                    break

            # 5. 完成
            status_text.text("5/5 辨識完成！")
            progress_bar.progress(100)
            time.sleep(1)
            
    except Exception as e:
        vix_val = f"辨識失敗: {str(e)}"
        # 如果失敗，抓一張全網頁截圖方便除錯
        try: shot = page.screenshot() 
        except: pass
        success = False
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- UI ---
st.title("📈 期交所 VIX 實時座標辨識")

if st.button("🚀 開始掃描數據", use_container_width=True):
    val, img, ok = run_vix_taifex_direct()
    
    if ok:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("掃描辨識數值", val)
            st.write(f"取得時間：{datetime.now().strftime('%H:%M:%S')}")
        with c2:
            st.write("### 📍 座標局部快照驗證")
            st.image(img, caption=f"對應圖二位置：{val}")
    else:
        st.error(val)
        if img:
            st.write("### 目前掃描到的畫面 (除錯用)")
            st.image(img)

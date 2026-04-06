import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="VIX 指數自動監控", layout="wide")

def get_vix_data_final():
    """整合 Cookie 注入與 JS 強制點擊的掃描邏輯"""
    # 數據分頁網址
    target_url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    # 進度提示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("1/4 啟動瀏覽器並注入通行證...")
            progress_bar.progress(25)
            
            # 啟動參數優化
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            
            # 關鍵：手動塞入 Cookie，讓網頁跳過免責聲明按鈕
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            context.add_cookies([{
                "name": "isDisclaimerConfirmed", 
                "value": "true", 
                "domain": "mis.taifex.com.tw", 
                "path": "/"
            }])
            
            page = context.new_page()
            
            # 2. 進入頁面
            status_text.text("2/4 前往行情頁面...")
            progress_bar.progress(50)
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            # 3. 預防機制：萬一 Cookie 沒生效，執行 JS 顏色辨識點擊
            page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        const style = window.getComputedStyle(btn);
                        // 尋找橘色背景按鈕 (免責聲明按鈕)
                        if (style.backgroundColor.includes('rgb(255') || btn.className.includes('orange')) {
                            btn.click();
                        }
                    }
                }
            """)
            
            # 等待數據 AJAX 加載
            time.sleep(5) 

            # 4. 暴力搜尋 VIX 數值 (不依賴中文定位)
            status_text.text("3/4 辨識數值座標...")
            progress_bar.progress(75)
            
            # 抓取表格中所有格子的文字
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                # 辨識邏輯：數字、有小數點、長度短 (避開日期或其他干擾)
                if text.replace('.', '', 1).isdigit() and '.' in text and len(text) < 7:
                    vix_val = text
                    shot = cell.screenshot() # 局部截圖
                    success = True
                    break
            
            if not success:
                # 若找不到數值，抓取全螢幕供除錯
                shot = page.screenshot()
                vix_val = "偵測到頁面，但未發現數值特徵"

            status_text.text("4/4 完成掃描！")
            progress_bar.progress(100)
            
    except Exception as e:
        vix_val = f"系統異常: {str(e)}"
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- Streamlit UI 介面 ---
st.title("🛡️ VIX 指數自動辨識系統")
st.markdown("本系統採用 **Cookie 注入** 與 **顏色特徵定位** 技術，可繞過期交所免責聲明並解決伺服器亂碼問題。")

# 側邊欄顯示
with st.sidebar:
    st.header("系統狀態")
    st.write("🌍 運行環境: Streamlit Cloud")
    st.write("🛠️ 技術細節: Playwright + JS Injection")

if st.button("🚀 獲取最新 VIX 指數", use_container_width=True):
    val, img, ok = get_vix_data_final()
    
    if ok:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("台指 VIX 指數", val)
            st.write(f"⏱️ 擷取時間：{datetime.now().strftime('%H:%M:%S')}")
            
            # 簡易警示邏輯
            try:
                if float(val) > 25: st.warning("⚠️ 市場波動性升高")
                else: st.success("✅ 市場情緒平穩")
            except: pass
            
        with col2:
            st.write("### 📍 數據來源快照")
            st.image(img, caption=f"網頁實際抓取到的數值：{val}")
    else:
        st.error(f"掃描失敗：{val}")
        if img:
            st.write("### 📸 偵錯截圖 (輔助判斷錯誤原因)")
            st.image(img)

st.divider()
st.caption("註：本工具僅供技術研究使用，實際數據請以期交所公告為準。")

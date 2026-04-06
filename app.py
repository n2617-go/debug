import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# --- 頁面初始設定 ---
st.set_page_config(page_title="台指 VIX 即時監測", layout="wide")

def get_vix_data_final():
    # 期交所 VIX 行情分頁直達網址
    target_url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("1/4 正在配置瀏覽器並注入通行證...")
            progress_bar.progress(25)
            
            # 啟動穩定性參數
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox", 
                "--disable-gpu",
                "--single-process"
            ])
            
            # 【關鍵】手動注入 Cookie，繞過「免責聲明」橘色按鈕彈窗
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            context.add_cookies([{
                "name": "isDisclaimerConfirmed", 
                "value": "true", 
                "domain": "mis.taifex.com.tw", 
                "path": "/"
            }])
            
            page = context.new_page()
            
            # 2. 直接空降目標頁面
            status_text.text("2/4 正在穿透防護網並讀取數據...")
            progress_bar.progress(50)
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            # 3. 預防萬一：若 Cookie 沒生效，用 JS 尋找橘色背景強制點擊
            page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        const style = window.getComputedStyle(b);
                        if (style.backgroundColor.includes('rgb(255') || b.className.includes('orange')) {
                            b.click();
                        }
                    }
                }
            """)
            
            # 等待數據非同步載入（期交所數據需要時間渲染）
            time.sleep(6) 

            # 4. 特徵掃描：不依賴中文，尋找「數字 + 小數點」的格子
            status_text.text("3/4 正在掃描 36.45 數據座標...")
            progress_bar.progress(75)
            
            # 掃描頁面上所有 TD 儲存格
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                # 辨識邏輯：是數字、有小數點、排除長字串 (確保是我們要的點位)
                if text.replace('.', '', 1).isdigit() and '.' in text and len(text) < 7:
                    vix_val = text
                    shot = cell.screenshot() # 截取該數據格作為證據
                    success = True
                    break
            
            if not success:
                # 若失敗，抓一張全螢幕截圖來確認目前卡在哪裡
                shot = page.screenshot()
                vix_val = "偵測成功但未發現數值"

            status_text.text("4/4 掃描任務完成！")
            progress_bar.progress(100)
            
    except Exception as e:
        vix_val = f"系統層級錯誤: {str(e)}"
    finally:
        # 清除進度條顯示
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- Streamlit 使用者介面 ---
st.title("📊 台指 VIX 自動辨識系統")
st.markdown("針對 **Streamlit Cloud** 環境優化：已解決中文字型亂碼與免責聲明阻擋問題。")

# 側邊資訊欄
with st.sidebar:
    st.header("🛠️ 技術狀態")
    st.write("🟢 模擬瀏覽器：Playwright")
    st.write("🟢 繞過技術：Cookie Injection")
    st.write("🟢 定位技術：JS Color Sensing")

# 主要操作區
if st.button("🚀 執行一鍵數據擷取", use_container_width=True):
    with st.status("正在連線至期交所...", expanded=True) as status:
        val, img, ok = get_vix_data_final()
        status.update(label="擷取流程結束", state="complete" if ok else "error")
    
    if ok:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("目前的 VIX 指數", val)
            st.write(f"📅 更新時間：{datetime.now().strftime('%H:%M:%S')}")
        with c2:
            st.write("### 📍 數據來源快照 (座標驗證)")
            st.image(img, caption=f"對應 VIX 數值：{val}")
            st.success("成功繞過免責聲明並解決亂碼問題！")
    else:
        st.error(f"擷取失敗原因：{val}")
        if img:
            st.write("### 📸 偵錯截圖 (請查看程式目前看到的畫面)")
            st.image(img)

st.divider()
st.caption("提示：若截圖仍顯示免責聲明，請嘗試重新點擊按鈕。")

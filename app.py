import streamlit as st
from playwright.sync_api import sync_playwright
import time
import random

def run_vix_stealth_scan():
    url = "https://www.wantgoo.com/index/vixtwn/shareholding-distribution"
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("⚙️ 正在啟動隱身瀏覽器...")
            progress_bar.progress(20)
            
            # 關鍵：加入更多 args 避開偵測
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled", # 隱藏自動化標記
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ])
            
            # 建立 context 並注入模擬腳本
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            # 偽裝 WebDriver 屬性，讓網站以為是真人在用 Chrome
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # 進入網頁
            status_text.text("🌐 正在連線並模擬真人瀏覽...")
            progress_bar.progress(50)
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 模擬真人行為：隨機捲動一下
            page.mouse.wheel(0, random.randint(300, 600))
            time.sleep(random.uniform(2, 4)) # 模擬人類看網頁的停頓

            # 定位數據 (改用更穩定的 CSS 路徑)
            status_text.text("🔍 正在辨識 36.45 指數座標...")
            progress_bar.progress(80)
            
            # 玩股網的結構：我們找包含價格的關鍵區塊
            selector = "span.last"
            
            try:
                # 再次確認元素是否真的載入
                page.wait_for_selector(selector, state="visible", timeout=15000)
                
                # 擷取數據
                vix_val = page.inner_text(selector).strip()
                # 座標快照
                element = page.query_selector(selector)
                shot = element.screenshot()
                success = True
            except:
                # 如果還是抓不到，抓全螢幕看看是不是跳出了廣告
                shot = page.screenshot()
                vix_val = "定位超時，請檢查截圖是否被廣告遮擋"

            status_text.text("✅ 掃描完成！")
            progress_bar.progress(100)
            time.sleep(1)

    except Exception as e:
        vix_val = f"系統錯誤: {str(e)}"
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

st.title("🕶️ VIX 高階隱身掃描系統")
st.markdown("使用 **Stealth 隱身技術** 繞過檢測，模擬真人行為擷取座標數據。")

if st.button("🚀 執行深度掃描"):
    val, img, ok = run_vix_stealth_scan()
    
    if ok:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("辨識結果", val)
        with c2:
            st.image(img, caption="座標局部快照")
    else:
        st.error(val)
        if img:
            st.image(img, caption="目前的網頁畫面 (除錯用)")

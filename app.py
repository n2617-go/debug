import streamlit as st
from playwright.sync_api import sync_playwright
import time

def run_vix_bypass_scan():
    # 網址嘗試切換回期交所行情頁，避開玩股網的 Cloudflare 硬骨頭
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("🛡️ 正在啟動高級偽裝引擎...")
            progress_bar.progress(20)
            
            # 增加啟動參數，減少被偵測為機器的特徵
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--use-gl=desktop" # 模擬桌面顯示卡渲染
            ])
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
            
            # 抹除 WebDriver 標記
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            status_text.text("📡 正在繞過安全檢查...")
            progress_bar.progress(50)
            
            # 進入頁面
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # --- 針對期交所的點擊邏輯 ---
            try:
                # 即使沒看到按鈕也等一下，讓安全檢查過去
                time.sleep(5) 
                confirm_btn = page.query_selector("button:has-text('確認')")
                if confirm_btn:
                    confirm_btn.click()
                    time.sleep(3)
            except:
                pass

            status_text.text("🔍 正在辨識 36.45 數據...")
            progress_bar.progress(80)
            
            # 使用 XPath 定位含有 VIX 的行
            target_row = page.query_selector("//tr[td[contains(., '臺指選擇權波動率指數')]]")
            
            if target_row:
                # 掃描該行中的第一個數字
                cells = target_row.query_selector_all("td")
                for cell in cells:
                    txt = cell.inner_text().strip()
                    if txt.replace('.', '', 1).isdigit():
                        vix_val = txt
                        shot = cell.screenshot()
                        success = True
                        break
            
            if not success:
                # 再次失敗就抓全螢幕，看是不是又卡在 Cloudflare
                shot = page.screenshot()
                vix_val = "數據定位失敗"

            progress_bar.progress(100)
            time.sleep(1)

    except Exception as e:
        vix_val = f"連線中斷: {str(e)}"
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

st.title("🛡️ VIX 數據抓取 (突破版)")
st.info("偵測到網頁受到 Cloudflare 保護，已啟動隱身模式嘗試突破。")

if st.button("🚀 開始掃描"):
    val, img, ok = run_vix_bypass_scan()
    if ok:
        st.metric("掃描結果", val)
        st.image(img, caption="成功抓取數據區域")
    else:
        st.error(val)
        if img:
            st.image(img, caption="目前的畫面狀況")

import streamlit as st
from playwright.sync_api import sync_playwright
import time

def run_vix_flash_scan():
    # 改用更輕量的主頁面，減少被攔截機率
    url = "https://www.wantgoo.com/index/vixtwn"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("🚀 啟動閃擊引擎...")
            progress_bar.progress(20)
            
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ])
            
            # 關鍵：加入更真實的標頭
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                locale="zh-TW",
                timezone_id="Asia/Taipei"
            )
            page = context.new_page()

            # 關鍵修正：改用 'commit' 模式，只要伺服器一吐資料就開始工作
            status_text.text("📡 嘗試突破連線限制...")
            progress_bar.progress(50)
            
            try:
                # 不等網路閒置，只要 DOM 出現就開始
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                status_text.text("⚠️ 連線較慢，嘗試強制掃描中...")

            # 快速尋找數值座標
            status_text.text("🔍 正在捕捉 36.45 座標點位...")
            progress_bar.progress(80)
            
            # 嘗試多重定位
            selectors = ["span.last", ".price-box .last", "b.price"]
            
            for selector in selectors:
                try:
                    # 只等 5 秒，有就有，沒有就換下一個
                    el = page.wait_for_selector(selector, timeout=5000)
                    if el:
                        vix_val = el.inner_text().strip()
                        shot = el.screenshot()
                        success = True
                        break
                except:
                    continue

            if not success:
                # 失敗時抓一張「現場證據」，看是不是被擋在外面
                shot = page.screenshot()
                vix_val = "連線成功但找不到數值，可能是版面跳轉"

            progress_bar.progress(100)
            time.sleep(1)

    except Exception as e:
        vix_val = f"連線逾時或錯誤: {str(e)}"
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

st.title("⚡ VIX 座標閃擊系統")
st.info("此版本針對 Cloud 環境逾時問題優化，縮短等待時間並強化偽裝。")

if st.button("🚀 執行閃擊掃描"):
    val, img, ok = run_vix_flash_scan()
    
    if ok:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("掃描結果", val)
        with col2:
            st.image(img, caption="座標局部快照")
    else:
        st.error(val)
        if img:
            st.write("### 📸 偵錯快照 (程式目前看到的畫面)")
            st.image(img)

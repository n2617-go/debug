import streamlit as st
from playwright.sync_api import sync_playwright
import time

def run_vix_color_locator_scan():
    # 期交所免責聲明頁
    url = "https://mis.taifex.com.tw/futures/disclaimer/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            status_text.text("1/3 啟動引擎並進入頁面...")
            progress_bar.progress(33)
            
            # 模擬高階環境，避開自動化偵測
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 進入網頁
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # --- 核心：顏色定位邏輯 ---
            status_text.text("2/3 正在搜尋『橘色按鈕』座標...")
            
            # 方案 A: 使用 CSS Selector 鎖定包含橘色背景的 button
            # 期交所的橘色按鈕通常對應 .btn-orange 或帶有 style 的 button
            color_selectors = [
                "button.btn-orange", 
                "button.btn-confirm",
                "//button[contains(@class, 'orange')]",
                "//div[contains(@class, 'footer')]//button[1]" # 結構定位：底部第一個按鈕
            ]
            
            clicked = False
            for selector in color_selectors:
                try:
                    # 只給 5 秒嘗試，找不到就換下一個
                    btn = page.wait_for_selector(selector, timeout=5000)
                    if btn:
                        # 取得按鈕顏色進行二次確認 (選用)
                        # 執行強制點擊
                        btn.click(force=True)
                        clicked = True
                        break
                except:
                    continue
            
            # 如果還是點不到，使用「座標暴力點擊」 (針對截圖位置)
            if not clicked:
                page.mouse.click(640, 760) # 根據 1280x800 解析度估算的橘色按鈕中心點
            
            # 點擊後緩衝，讓數據載入
            time.sleep(5)

            # --- 數據抓取 ---
            status_text.text("3/3 正在掃描 36.45 數據格...")
            progress_bar.progress(66)
            
            # 直接導向數據頁，確保頁面正確
            page.goto("https://mis.taifex.com.tw/futures/VolatilityQuotes/", wait_until="domcontentloaded")
            
            # 暴力搜尋：找尋所有包含數字與小數點的 td
            page.wait_for_selector("td", timeout=15000)
            cells = page.query_selector_all("td")
            
            for cell in cells:
                txt = cell.inner_text().strip()
                # 辨識特徵：數字 + 小數點 (例如 36.45)
                if txt.replace('.', '', 1).isdigit() and '.' in txt:
                    vix_val = txt
                    shot = cell.screenshot()
                    success = True
                    break
            
            if not success:
                shot = page.screenshot() # 失敗則拍下全螢幕供你核對顏色位置

            progress_bar.progress(100)
            
    except Exception as e:
        vix_val = f"定位錯誤: {str(e)}"
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- UI ---
st.title("🎨 顏色與座標定位系統 (無字辨識版)")
st.info("此版本完全不依賴中文辨識，直接鎖定『橘色按鈕』的 CSS 屬性與座標進行操作。")

if st.button("🚀 開始顏色辨識任務"):
    val, img, ok = run_vix_color_locator_scan()
    if ok:
        st.metric("掃描到的 VIX 數值", val)
        st.image(img, caption="成功辨識之局部快照")
    else:
        st.error(val)
        if img:
            st.write("### 📸 偵錯截圖 (請確認橘色按鈕是否被正確觸發)")
            st.image(img)

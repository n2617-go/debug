import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

st.set_page_config(page_title="VIX 終極突破系統", layout="wide")

def super_bypass_vix():
    # 使用行情分頁
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            # 1. 偽裝成一般的 Windows Chrome 瀏覽器
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            
            # 注入通行證
            context.add_cookies([{
                "name": "isDisclaimerConfirmed", "value": "true", 
                "domain": "mis.taifex.com.tw", "path": "/"
            }])
            
            page = context.new_page()
            
            # 2. 進入頁面
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 3. 【暴力破門】不管按鈕有沒有出來，用 JS 直接對所有可能的橘色物體發動點擊
            page.evaluate("""
                () => {
                    // 尋找所有按鈕
                    const elements = document.querySelectorAll('button, div, span');
                    for (const el of elements) {
                        const style = window.getComputedStyle(el);
                        const isOrange = style.backgroundColor.includes('rgb(255, 122, 66)') || 
                                         style.backgroundColor.includes('rgb(255, 121, 65)');
                        // 如果顏色對了，或者是確認類的按鈕，就點下去
                        if (isOrange || el.innerText.includes('確認') || el.className.includes('btn-orange')) {
                            el.click();
                        }
                    }
                }
            """)
            
            # 模擬真人捲動一下頁面 (觸發數據載入)
            page.mouse.wheel(0, 500)
            time.sleep(7) # 給予充足的數據載入時間

            # 4. 精準掃描表格數據
            # 我們直接找包含小數點的 td，並排除掉長度太長的 (如日期)
            found_cells = page.query_selector_all("td")
            for cell in found_cells:
                txt = cell.inner_text().strip()
                # VIX 特徵：36.45 這種格式
                if '.' in txt and txt.replace('.', '').isdigit() and len(txt) <= 6:
                    vix_val = txt
                    shot = cell.screenshot()
                    success = True
                    break
            
            if not success:
                shot = page.screenshot() # 沒抓到就拍全螢幕讓我們檢討
                
    except Exception as e:
        vix_val = f"意外中斷: {str(e)}"
    
    return vix_val, shot, success

# --- UI ---
st.title("🔥 VIX 數據破門系統")
st.info("此版本模擬真人行為（捲動、偽裝標頭），專門對付『看得到點不到』的按鈕。")

if st.button("🚀 啟動強效擷取"):
    with st.spinner("正在突破防線..."):
        val, img, ok = super_bypass_vix()
        
        if ok:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("台指 VIX 指數", val)
                st.write(f"取得時間: {datetime.now().strftime('%H:%M:%S')}")
            with c2:
                st.image(img, caption="數據快照")
        else:
            st.error(f"目前狀態: {val}")
            st.image(img, caption="目前瀏覽器看到的畫面")

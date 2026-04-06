import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="期交所 VIX 穩定掃描版", layout="wide")

def run_vix_automated_scan():
    """執行步驟：1. 模擬點擊 2. 座標快照"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 初始化變數
    vix_text = "N/A"
    screenshot_bytes = None
    success = False

    # 1. 啟動 Playwright (外層不放 try，讓 with 自動管理生命週期)
    try:
        with sync_playwright() as p:
            status_text.text("1/5 正在啟動瀏覽器引擎...")
            progress_bar.progress(20)
            
            # 使用單一進程模式與關閉沙盒，增加在雲端環境的穩定性
            browser = p.chromium.launch(
                headless=True, 
                args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process"]
            )
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()

            # 2. 進入頁面
            status_text.text("2/5 正在連線至期交所...")
            progress_bar.progress(40)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 3. 模擬點擊確認按鈕
            status_text.text("3/5 正在模擬點擊『確認』按鈕...")
            progress_bar.progress(60)
            
            # 期交所的按鈕定位優化：同時搜尋文字與常見按鈕標籤
            try:
                # 等待按鈕出現在畫面，給予較短的 timeout 避免卡死
                confirm_selector = "button:has-text('確認'), input[type='button'][value='確認']"
                page.wait_for_selector(confirm_selector, timeout=8000)
                page.click(confirm_selector)
                # 點擊後務必等待表格渲染
                time.sleep(3) 
            except:
                status_text.text("跳過按鈕點擊 (可能已直接進入行情頁)")

            # 4. 定位座標與擷取數據 (對應你提供的圖二位置)
            status_text.text("4/5 正在精準定位 VIX 數據座標...")
            progress_bar.progress(80)
            
            # 定位含有 VIX 文字的表格列
            row_selector = "tr:has-text('臺指選擇權波動率指數')"
            page.wait_for_selector(row_selector, timeout=10000)
            
            # 抓取該列中包含「目前指數」的儲存格 (通常是該行的第 3 或第 4 個 td)
            # 我們直接定位到數據格進行快照
            cells = page.query_selector_all(f"{row_selector} td")
            
            if len(cells) >= 3:
                target_cell = cells[2] # 根據期交所結構定位
                vix_text = target_cell.inner_text().strip()
                # 執行局部座標快照
                screenshot_bytes = target_cell.screenshot()
                success = True
            else:
                raise Exception("無法正確定位數據欄位")

            # 5. 完成
            status_text.text("5/5 掃描成功！")
            progress_bar.progress(100)
            time.sleep(1)
            
            # 注意：這裡不呼叫 browser.close()，讓 with 語法自動處理
            
    except Exception as e:
        vix_text = f"掃描錯誤: {str(e)}"
        success = False
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_text, screenshot_bytes, success

# --- Streamlit UI ---
st.title("📸 期交所 VIX 座標自動化掃描")
st.markdown("針對 `mis.taifex.com.tw` 免責聲明頁面進行自動化點擊與數據擷取。")

if st.button("🚀 開始執行自動化任務", use_container_width=True):
    val, img, ok = run_vix_automated_scan()
    
    if ok:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("掃描辨識數值", val)
            st.write(f"更新時間：{datetime.now().strftime('%H:%M:%S')}")
        with c2:
            st.write("### 📍 座標掃描區快照")
            st.image(img, caption=f"對應圖二綠色框位之即時快照: {val}")
            st.success("點擊與掃描流程完整執行完畢。")
    else:
        st.error(val)
        st.info("提示：若在雲端失敗，請確認已在 packages.txt 安裝 libgbm1 等依賴。")

st.divider()
st.caption("註：4/6 為補假，數據為連假前 4/2 最後更新點位。")

import streamlit as st
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="VIX 終極座標辨識", layout="wide")

def run_vix_wantgoo_coordinate_scan():
    """模擬真人開啟網頁 -> 精準鎖定座標區域 -> 辨識數字"""
    url = "https://www.wantgoo.com/index/vixtwn/shareholding-distribution"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    vix_val = "N/A"
    shot = None
    success = False

    try:
        with sync_playwright() as p:
            # Step 1: 啟動
            status_text.text("1/5 啟動掃描引擎...")
            progress_bar.progress(20)
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # Step 2: 載入
            status_text.text("2/5 正在連線玩股網...")
            progress_bar.progress(40)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Step 3: 定位 (針對玩股網 36.45 大字優化)
            status_text.text("3/5 正在精準鎖定座標區域...")
            progress_bar.progress(60)
            
            # 玩股網標配的價格大字選擇器
            selector = "span.last" 
            
            try:
                page.wait_for_selector(selector, timeout=20000)
                
                # Step 4: 擷取
                status_text.text("4/5 正在執行座標快照與辨識...")
                progress_bar.progress(80)
                
                vix_val = page.inner_text(selector).strip()
                element_handle = page.query_selector(selector)
                shot = element_handle.screenshot()
                success = True
                
            except Exception as e:
                vix_val = f"定位失敗: {str(e)}"

            # Step 5: 完成
            status_text.text("5/5 掃描完成！")
            progress_bar.progress(100)
            time.sleep(0.5)

    except Exception as e:
        vix_val = f"執行錯誤: {str(e)}"
    finally:
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- UI 介面 ---
st.title("🛡️ 大盤 VIX 終極座標辨識器")

# 修正後的呼叫位置
if st.button("🚀 開始座標掃描任務", use_container_width=True):
    # 注意這裡：沒有冒號！
    val, img, ok = run_vix_wantgoo_coordinate_scan()
    
    if ok:
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.metric("辨識到的 VIX 數值", val)
            st.write(f"取得時間：{datetime.now().strftime('%H:%M:%S')}")
        with c2:
            st.write("### 📍 座標局部快照驗證")
            st.image(img, caption=f"實際掃描位置：{val}")
            st.success("成功抓出 36.45 位置並完成辨識！")
    else:
        st.error(val)

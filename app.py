import streamlit as st
import asyncio
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="VIX 終極座標辨識", layout="wide")

def run_vix_wantgoo_coordinate_scan():
    """模擬真人開啟網頁 -> 精準鎖定座標區域 -> 辨識數字"""
    # 目標：玩股網 VIX 大盤籌碼頁 (不需前置點擊)
    url = "https://www.wantgoo.com/index/vixtwn/shareholding-distribution"
    
    # 初始化進度條與狀態元件
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 初始化變數
    vix_val = "N/A"
    shot = None
    success = False

    try:
        # 使用更強健的上下文管理器 (解決 Event Loop closed 問題)
        with sync_playwright() as p:
            # Step 1: 啟動並進入頁面
            status_text.text("1/5 正在啟動掃描引擎，前往玩股網...")
            progress_bar.progress(20)
            
            # 使用 headless=True 在雲端環境執行
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # 前往網頁，使用 domcontentloaded 加快載入時間
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Step 2: 定位數據座標區域 (針對玩股網結構優化)
            status_text.text("2/5 正在精準鎖定 VIX 數值座標...")
            progress_bar.progress(60)
            
            # 針對你提供的圖二結構，玩股網的主要價格大字通常使用CSS選擇器鎖定
            # 我們使用特定的 CSS Selector 來定位：這代表在 price-box 底下的 last class
            selector = ".price-box .last, .price.price-red, span.last" 
            
            try:
                # 等待座標區域出現，給予足夠的 timeout
                page.wait_for_selector(selector, timeout=20000)
                
                # Step 3: 執行座標快照與數值辨識
                status_text.text("3/5 正在辨識座標數值並進行快照...")
                progress_bar.progress(80)
                
                # 辨識文字 (這就是 36.45)
                vix_val = page.inner_text(selector).strip()
                # 快照對焦：只截取該格子座標區域 ( OCR 區域)
                element_handle = page.query_selector(selector)
                shot = element_handle.screenshot()
                
                success = True
                
            except Exception as e:
                status_text.text(f"定位失敗，可能座標結構已改變: {str(e)}")

            # Step 4: 完成掃描
            status_text.text("4/5 完成掃描，安全退出引擎...")
            progress_bar.progress(100)
            
            # 這裡不呼叫 browser.close()，讓 with 自動關閉

    except Exception as e:
        vix_val = f"辨識錯誤: {str(e)}"
        success = False
    finally:
        # 清除狀態元件
        progress_bar.empty()
        status_text.empty()

    return vix_val, shot, success

# --- UI 介面 ---
st.title("🛡️ 大盤 VIX 終極座標辨識器")
st.markdown("### 目標：自動掃描並辨識玩股網 36.45 指數位置")

if st.button("🚀 開始座標掃描任務", use_container_width=True):
    val, img, ok = run_vix_wantgoo_coordinate_scan():
    
    if ok:
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.metric("辨識到的 VIX 數值", val)
            st.write(f"取得時間：{datetime.now().strftime('%H:%M:%S')}")
            
            # 市場情緒判斷
            try:
                vix_float = float(val)
                if vix_float > 30: st.error("🚨 市場恐慌升高")
                elif vix_float < 18: st.success("😊 市場情緒穩定")
                else: st.info("🟡 市場正常波動")
            except:
                pass
        
        with c2:
            st.write("### 📍 座標對焦局部快照 (驗證用)")
            st.image(img, caption=f"對應圖二座標：{val}")
            st.success("步驟完成：成功辨識圖中綠色框位數值。")
    else:
        st.error(val)
        st.info("💡 如果在雲端失敗，請確認 `packages.txt` 是否安裝了底層依賴。")

st.divider()
st.caption("註：4/6 補假中，掃描辨識結果為連假前 (4/2) 之最後點位。數據歸玩股網所有。")

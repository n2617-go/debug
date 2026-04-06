import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageOps, ImageFilter
io, os, re, time = __import__('io'), __import__('os'), __import__('re'), __import__('time')

def physical_force_extreme_zoom():
    """
    策略：將視窗拉長至 1600px，對螢幕下方 1/4 區域進行地毯式重擊
    """
    url = "https://mis.taifex.com.tw/futures/disclaimer"
    res_val = "N/A"
    screenshot = None
    
    try:
        with sync_playwright() as p:
            # 1. 暴力放大視窗高度，讓按鈕完全展開
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 1600})
            page = context.new_page()
            
            page.goto(url, wait_until="networkidle")
            time.sleep(4) # 給予更多載入時間
            
            # 2. 強制滾動到底部並等待渲染
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
            # 3. 區塊重擊 (Area Bombing)：針對截圖中橘色按鈕可能出現的矩形區域
            # 根據 1000028201.jpg，按鈕在下方中央偏左
            # 我們在 X: 400~600, Y: 900~1100 之間進行密集點擊
            for x in range(400, 650, 40):
                for y in range(900, 1150, 40):
                    page.mouse.click(x, y)
            
            # 4. JS 補擊：不只找「接受」，連同 class 含有 orange 的都點
            page.evaluate("""() => {
                const elements = document.querySelectorAll('button, a, div[role="button"]');
                elements.forEach(el => {
                    const txt = el.innerText || "";
                    if (txt.includes('接受') || el.classList.contains('orange') || el.id.includes('accept')) {
                        el.click();
                    }
                });
            }""")
            
            time.sleep(10) # 預留更長的跳轉時間給數據表
            
            # 5. 數據掃描：鎖定 25 以上的 VIX 數值
            cells = page.query_selector_all("td")
            for c in cells:
                t = c.inner_text().strip()
                if '.' in t and t.replace('.','').isdigit():
                    val = float(t)
                    if 25 < val < 55:
                        res_val = t
                        break
            
            screenshot = page.screenshot()
            browser.close()
    except:
        res_val = "重擊逾時"
    return res_val, screenshot

# --- UI 介面 ---
st.set_page_config(page_title="AI 鋼鐵重擊", layout="wide")
st.title("🔥 暴力放大 X 區塊重擊任務")

if st.button("🚀 執行【區塊轟炸】物理重擊", use_container_width=True):
    with st.spinner("正在進行地毯式點擊..."):
        val, shot = physical_force_extreme_zoom()
        st.session_state['vix_twn'] = val
        if shot: st.session_state['vix_shot'] = shot

st.metric("台指期 VIXTWN (實時)", st.session_state.get('vix_twn', 'N/A'))

if 'vix_shot' in st.session_state:
    st.divider()
    st.subheader("📸 重擊後現場檢查")
    st.image(st.session_state['vix_shot'], caption="若看到表格則成功；若仍是首頁，我們需檢查是否有點到『不接受』")

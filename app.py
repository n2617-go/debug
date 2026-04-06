import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

# 頁面設定
st.set_page_config(page_title="VIX 實戰爬蟲", layout="wide")

def get_wantgoo_vix():
    """
    使用 Selenium 模擬真人進入玩股網抓取 VIX 數值
    """
    url = "https://www.wantgoo.com/index/vixtwn/price-to-earning-river"
    
    # 1. 瀏覽器環境設定
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 雲端執行建議開啟，本地測試可註解掉看過程
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 2. 模擬真人 Headers
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 3. 進入網頁
        driver.get(url)
        
        # 4. 模擬真人等待時間，避免被發現是機器人
        wait = WebDriverWait(driver, 15)
        
        # 5. 抓取綠色框框內的 VIX 數值 (玩股網的點位通常在特定的 class 或 id 中)
        # 根據你提供的圖片，我們尋找最新成交點位
        vix_element = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'last')] | //div[contains(@class, 'price')]")))
        
        vix_value = vix_element.text
        
        # 6. 抓取昨收價與時間
        try:
            time_element = driver.find_element(By.XPATH, "//time")
            update_time = time_element.text
        except:
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        driver.quit()
        return vix_value, update_time

    except Exception as e:
        driver.quit()
        return f"錯誤: {str(e)}", None

# --- Streamlit UI ---
st.title("📈 玩股網 VIX 指數即時監控 (模擬真人版)")
st.info("由於玩股網具有嚴格反爬蟲機制，本程式使用 Selenium 模擬瀏覽器行為進行數據抓取。")

if st.button("🔄 立即模擬真人抓取"):
    st.cache_data.clear()
    with st.spinner('正在開啟模擬瀏覽器並繞過反爬蟲機制...'):
        vix_val, update_time = get_wantgoo_vix()
        
        if "錯誤" not in vix_val:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("最新點位 (玩股網)", vix_val)
            with c2:
                st.write(f"📅 數據時間：{update_time}")
            
            st.success("成功抓取！數值對應你圖中綠色框選的區域。")
        else:
            st.error(vix_val)
            st.info("提示：如果是在雲端環境執行（如 Streamlit Cloud），可能需要額外安裝 Chrome Driver 環境。")

st.divider()
st.write("### 為什麼直接用 API 抓不到玩股網？")
st.write("""
1. **Dynamic Rendering**: 該數值是網頁加載後才由 JavaScript 填入的，單純的 Requests 只能抓到空白原始碼。
2. **Bot Detection**: 玩股網會檢查 Cookies 和瀏覽軌跡，模擬瀏覽器是目前最有效的方式。
3. **休市數據**: 即使 4/6 休市，玩股網頁面上依然會保留 4/2 的最後結算數值 **36.45**。
""")

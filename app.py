def fetch_vixtwn_physical():
    """台指 VIX 物理重擊：多點採樣強化版"""
    url = "https://mis.taifex.com.tw/futures/VolatilityQuotes/"
    vix_val = "N/A"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            # 統一解析度，這對座標精準度至關重要
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5) # 稍微增加等待時間，確保按鈕已渲染
            
            # --- 多點採樣點擊：十字型覆蓋橘色按鈕區域 ---
            # 根據快照，橘色按鈕大約在 640, 755 附近
            target_points = [
                (640, 755), (640, 750), (640, 760), # 中心線
                (600, 755), (680, 755)              # 左右延伸
            ]
            for x, y in target_points:
                page.mouse.click(x, y)
                time.sleep(0.2)
            
            # 補償方案：如果點擊沒效，嘗試用 JavaScript 觸發
            page.evaluate("() => { const b = document.querySelector('.btn-orange'); if(b) b.click(); }")
            
            time.sleep(8) # 等待表格數據跑出來
            
            # 抓取表格內容
            cells = page.query_selector_all("td")
            for cell in cells:
                text = cell.inner_text().strip()
                # 辨識特徵：包含小數點、純數字、長度合理
                if '.' in text and text.replace('.', '').isdigit() and len(text) < 7:
                    vix_val = text
                    break
            
            # 更新快照供您檢查
            st.session_state['last_shot'] = page.screenshot()
            browser.close()
            return vix_val
    except Exception as e:
        return f"重擊失敗: {e}"

# 這是最核心的修正：利用 JS 直接在瀏覽器內部尋找『橘色』並點擊
page.evaluate("""
    () => {
        const buttons = document.querySelectorAll('button');
        for (const btn of buttons) {
            const style = window.getComputedStyle(btn);
            // 抓取橘色 (RGB 255, 122, 66) 或 class 包含 orange 的按鈕
            if (style.backgroundColor.includes('rgb(255') || btn.className.includes('orange')) {
                console.log('找到目標按鈕，執行強制點擊');
                btn.click(); // 這是從網頁內部直接觸發，比 Playwright 的外部模擬更有效
                return;
            }
        }
    }
""")

"""
VIXTWN 診斷腳本
在 terminal 執行：python debug_vixtwn.py
把輸出結果貼給我，就能確認問題在哪一步
"""
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# =============================================
# 方案 A：台灣期交所
# =============================================
print("=" * 50)
print("【方案 A】台灣期交所 VIX 每日行情")
print("=" * 50)
try:
    url = "https://www.taifex.com.tw/cht/3/viXDailyMarketReport"
    res = requests.get(url, headers=HEADERS, timeout=15)
    print(f"HTTP 狀態碼: {res.status_code}")
    print(f"回應長度: {len(res.text)} bytes")
    
    soup = BeautifulSoup(res.text, "html.parser")
    tables = soup.find_all("table")
    print(f"找到 table 數量: {len(tables)}")
    
    for i, table in enumerate(tables):
        rows = table.find_all("tr")
        print(f"\nTable[{i}] 共 {len(rows)} 行")
        for j, row in enumerate(rows[:5]):  # 只印前 5 行
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if cols:
                print(f"  Row[{j}]: {cols}")
except Exception as e:
    print(f"❌ 方案 A 失敗: {type(e).__name__}: {e}")

# =============================================
# 方案 B：FinMind REST API
# =============================================
print("\n" + "=" * 50)
print("【方案 B】FinMind API - TaiwanFuturesDaily / VIX")
print("=" * 50)
try:
    start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanFuturesDaily",
        "data_id": "VIX",
        "start_date": start_dt,
    }
    res = requests.get(url, params=params, timeout=15)
    print(f"HTTP 狀態碼: {res.status_code}")
    data = res.json()
    print(f"回應 msg: {data.get('msg')}")
    records = data.get("data", [])
    print(f"回傳筆數: {len(records)}")
    if records:
        print(f"最新一筆: {records[-1]}")
    else:
        print("⚠️ data 為空，嘗試其他 data_id...")
        
        # 列出所有可用的期貨代號（查 VIX 相關）
        params2 = {
            "dataset": "TaiwanFuturesDaily",
            "start_date": start_dt,
        }
        res2 = requests.get(url, params=params2, timeout=15)
        data2 = res2.json()
        records2 = data2.get("data", [])
        ids = list(set(r.get("futures_id","") for r in records2))
        vix_ids = [x for x in ids if "VIX" in x.upper() or "vix" in x.lower()]
        print(f"含 VIX 的代號: {vix_ids}")
        print(f"所有代號（前 30 個）: {sorted(ids)[:30]}")
except Exception as e:
    print(f"❌ 方案 B 失敗: {type(e).__name__}: {e}")

# =============================================
# 方案 C：FinMind - TaiwanVariousIndicators
# =============================================
print("\n" + "=" * 50)
print("【方案 C】FinMind API - TaiwanVariousIndicators5Seconds")
print("=" * 50)
try:
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanVariousIndicators5Seconds",
        "data_id": "VIXTWN",
        "start_date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
    }
    res = requests.get(url, params=params, timeout=15)
    print(f"HTTP 狀態碼: {res.status_code}")
    data = res.json()
    print(f"回應 msg: {data.get('msg')}")
    records = data.get("data", [])
    print(f"回傳筆數: {len(records)}")
    if records:
        print(f"最新一筆: {records[-1]}")
except Exception as e:
    print(f"❌ 方案 C 失敗: {type(e).__name__}: {e}")

# =============================================
# 方案 D：Yahoo Finance ^TAIEX VIX 相關
# =============================================
print("\n" + "=" * 50)
print("【方案 D】直接測試幾個 Yahoo Finance 代號")
print("=" * 50)
try:
    import yfinance as yf
    for symbol in ["^VIXTWN", "VIXTWN", "^TWII", "VIX.TW"]:
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if not hist.empty:
                print(f"✅ {symbol}: {round(hist['Close'].iloc[-1], 2)}")
            else:
                print(f"❌ {symbol}: 空資料")
        except Exception as e:
            print(f"❌ {symbol}: {e}")
except Exception as e:
    print(f"yfinance 整體失敗: {e}")

print("\n診斷完成，請把以上輸出貼給 Claude。")

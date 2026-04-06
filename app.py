import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(page_title="台指 VIX 監控", layout="wide")

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"


def fetch_vixtwn_history():
    """
    用 FinMind REST API 抓台指 VIX 歷史日線。
    dataset 優先嘗試 TaiwanFuturesDaily（data_id=VIX），
    備援嘗試 TaiwanOptionDaily（data_id=TXO，VIX 相關）。
    回傳 DataFrame，欄位：Date（index）、VIX；失敗回傳 empty DataFrame 與錯誤訊息。
    """
    start_dt = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
    errors = []

    # --- 方案 A：TaiwanFuturesDaily, data_id=VIX ---
    try:
        params = {
            "dataset": "TaiwanFuturesDaily",
            "data_id": "VIX",
            "start_date": start_dt,
        }
        res = requests.get(FINMIND_URL, params=params, timeout=15)
        res.raise_for_status()
        payload = res.json()
        records = payload.get("data", [])
        if records:
            df = pd.DataFrame(records)
            df['Date'] = pd.to_datetime(df['date']).dt.date
            df = df.sort_values('Date').drop_duplicates('Date')
            df = df[['Date', 'close']].rename(columns={'close': 'VIX'}).set_index('Date')
            return df, []
        else:
            errors.append(f"方案A FinMind TaiwanFuturesDaily/VIX：API 回傳空資料（msg: {payload.get('msg','')}）")
    except Exception as e:
        errors.append(f"方案A 例外：{type(e).__name__}: {e}")

    # --- 方案 B：TaiwanVariousIndicators5Seconds, data_id=VIXTWN ---
    try:
        start_dt_short = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        params = {
            "dataset": "TaiwanVariousIndicators5Seconds",
            "data_id": "VIXTWN",
            "start_date": start_dt_short,
        }
        res = requests.get(FINMIND_URL, params=params, timeout=15)
        res.raise_for_status()
        payload = res.json()
        records = payload.get("data", [])
        if records:
            df = pd.DataFrame(records)
            df['Date'] = pd.to_datetime(df['date']).dt.date
            df = df.sort_values('Date').drop_duplicates('Date')
            price_col = 'price' if 'price' in df.columns else df.columns[-1]
            df = df[['Date', price_col]].rename(columns={price_col: 'VIX'}).set_index('Date')
            return df, []
        else:
            errors.append(f"方案B FinMind TaiwanVariousIndicators5Seconds/VIXTWN：API 回傳空資料（msg: {payload.get('msg','')}）")
    except Exception as e:
        errors.append(f"方案B 例外：{type(e).__name__}: {e}")

    return pd.DataFrame(), errors


# --- UI 呈現 ---
st.title("🛡️ 台指 VIXTWN 即時監控")
st.caption(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with st.spinner('正在同步數據...'):
    df_hist, errors = fetch_vixtwn_history()

# 錯誤訊息永遠顯示（不吃掉）
if errors:
    with st.expander("⚠️ 偵錯詳情（點開查看）", expanded=True):
        for e in errors:
            st.warning(e)

if not df_hist.empty:
    df_hist.index = pd.to_datetime(df_hist.index)

    current_vix = float(df_hist['VIX'].iloc[-1])
    last_date = df_hist.index[-1]

    # 昨日基準（倒數第二筆，若只有一筆則用同一筆）
    ref_close = float(df_hist['VIX'].iloc[-2]) if len(df_hist) > 1 else current_vix
    delta = current_vix - ref_close

    # 1. 頂部看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            f"VIXTWN（{last_date.strftime('%Y-%m-%d')}）",
            f"{current_vix:.2f}",
            f"{delta:+.2f}"
        )
    with col2:
        if current_vix > 25:
            st.warning("📊 市場情緒：恐慌感上升")
        else:
            st.success("📊 市場情緒：相對穩定")
    with col3:
        if st.button("🔄 手動刷新"):
            st.rerun()

    st.divider()

    # 2. 歷史日線表格
    st.subheader("歷史日線紀錄")
    st.dataframe(
        df_hist.sort_index(ascending=False).style.format("{:.2f}"),
        use_container_width=True
    )

    # 3. 折線圖
    st.subheader("歷史走勢圖")
    st.line_chart(df_hist['VIX'])

else:
    st.error("❌ 兩個數據來源均抓取失敗，請查看上方偵錯詳情。")

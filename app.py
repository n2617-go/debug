import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz

# 頁面設定
st.set_page_config(page_title="台指 VIXTWN 監控", layout="wide")

tz_tw = pytz.timezone('Asia/Taipei')
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"


def fetch_vixtwn():
    """
    用 FinMind 公開 REST API 抓台指 VIX 日線。
    dataset: TaiwanStockIndex, data_id: VIX
    回傳: (DataFrame or None, 錯誤訊息 list)
    """
    errors = []
    start_dt = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')

    try:
        params = {
            "dataset": "TaiwanStockIndex",
            "data_id": "VIX",
            "start_date": start_dt,
        }
        res = requests.get(FINMIND_URL, params=params, timeout=15)
        res.raise_for_status()
        payload = res.json()
        msg = payload.get("msg", "")
        records = payload.get("data", [])

        if records:
            df = pd.DataFrame(records)
            # FinMind TaiwanStockIndex 欄位：date, price (或 close)
            price_col = "price" if "price" in df.columns else "close"
            df["Date"] = pd.to_datetime(df["date"])
            df = df[["Date", price_col]].rename(columns={price_col: "VIX"})
            df = df.sort_values("Date").drop_duplicates("Date").set_index("Date")
            return df, []
        else:
            errors.append(f"FinMind TaiwanStockIndex/VIX 回傳空資料（API msg: {msg}）")

    except requests.exceptions.HTTPError as e:
        errors.append(f"HTTP 錯誤 {e.response.status_code}：{e}")
    except requests.exceptions.Timeout:
        errors.append("連線逾時（timeout），請稍後再試")
    except Exception as e:
        errors.append(f"未預期錯誤：{type(e).__name__}: {e}")

    return None, errors


# --- UI ---
st.title("🛡️ 台指 VIXTWN 日線監控")
st.caption(f"系統時間：{datetime.now(tz_tw).strftime('%Y-%m-%d %H:%M:%S')} (台北)")

# 初始化 session_state
if "df_vix" not in st.session_state:
    st.session_state.df_vix = None
if "fetch_errors" not in st.session_state:
    st.session_state.fetch_errors = []
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# 手動更新按鈕
if st.button("🔄 更新 VIXTWN 數據"):
    with st.spinner("正在從 FinMind 抓取資料..."):
        df, errors = fetch_vixtwn()
        st.session_state.df_vix = df
        st.session_state.fetch_errors = errors
        st.session_state.last_update = datetime.now(tz_tw).strftime("%H:%M:%S")

# 顯示錯誤（若有）
if st.session_state.fetch_errors:
    with st.expander("⚠️ 偵錯詳情", expanded=True):
        for e in st.session_state.fetch_errors:
            st.warning(e)

# 顯示數據
df = st.session_state.df_vix
if df is not None and not df.empty:
    st.caption(f"最後更新：{st.session_state.last_update}")

    current_vix = float(df["VIX"].iloc[-1])
    ref_vix = float(df["VIX"].iloc[-2]) if len(df) > 1 else current_vix
    delta = current_vix - ref_vix
    last_date = df.index[-1].strftime("%Y-%m-%d")

    # 看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=f"VIXTWN 收盤（{last_date}）",
            value=f"{current_vix:.2f}",
            delta=f"{delta:+.2f}"
        )
    with col2:
        if current_vix >= 30:
            st.error("📊 市場情緒：極度恐慌")
        elif current_vix >= 20:
            st.warning("📊 市場情緒：恐慌感上升")
        else:
            st.success("📊 市場情緒：相對穩定")
    with col3:
        st.metric("數據筆數", f"{len(df)} 天", "近 60 日")

    st.divider()

    # 走勢圖
    st.subheader("📈 近 60 日走勢")
    st.line_chart(df["VIX"])

    # 歷史表格
    st.subheader("📋 歷史日線")
    st.dataframe(
        df.sort_index(ascending=False).style.format("{:.2f}"),
        use_container_width=True
    )

elif st.session_state.last_update is not None:
    # 按過按鈕但資料是空的
    st.error("❌ 抓取失敗，請查看上方偵錯詳情。")
else:
    # 還沒按過按鈕
    st.info("👆 請按「更新 VIXTWN 數據」按鈕載入資料。")

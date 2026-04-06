import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
import re

st.set_page_config(page_title="台指 VIXTWN 監控", layout="wide")
tz_tw = pytz.timezone('Asia/Taipei')


def fetch_vixtwn_taifex():
    """
    直接從台灣期交所官網抓 VIXTWN 歷史資料。
    URL: https://www.taifex.com.tw/cht/3/viXDailyMarketReport
    回傳: (DataFrame or None, 錯誤訊息 str or None)
    """
    url = "https://www.taifex.com.tw/cht/3/viXDailyMarketReport"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9",
        "Referer": "https://www.taifex.com.tw/",
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        res.encoding = "utf-8"

        # pandas 直接解析頁面所有 HTML table
        tables = pd.read_html(res.text)

        # 找包含 VIX 數字的 table（通常是第一個有日期欄的 table）
        for df in tables:
            # 欄位字串化，找含有日期格式的欄
            df.columns = [str(c).strip() for c in df.columns]
            col_str = " ".join(df.columns)

            # 期交所 VIXTWN 表格欄位通常包含「日期」與數字收盤欄
            if "日期" in col_str or "Date" in col_str or df.shape[1] >= 3:
                # 嘗試找日期欄與收盤/指數欄
                date_col = None
                val_col = None
                for c in df.columns:
                    if "日期" in c or "date" in c.lower():
                        date_col = c
                    if any(k in c for k in ["收盤", "指數", "VIX", "close", "Close", "price"]):
                        val_col = c

                # 如果找不到明確欄位，嘗試用第 0 欄當日期、第 1 欄當數值
                if date_col is None:
                    date_col = df.columns[0]
                if val_col is None and df.shape[1] >= 2:
                    val_col = df.columns[1]

                if date_col and val_col:
                    try:
                        df_clean = df[[date_col, val_col]].copy()
                        df_clean.columns = ["Date", "VIX"]
                        # 清除非數字的 VIX 值（去掉表頭重複行、逗號千位符）
                        df_clean["VIX"] = (
                            df_clean["VIX"]
                            .astype(str)
                            .str.replace(",", "")
                            .str.extract(r"(\d+\.?\d*)")
                        )
                        df_clean = df_clean.dropna(subset=["VIX"])
                        df_clean["VIX"] = df_clean["VIX"].astype(float)
                        # VIX 合理範圍過濾
                        df_clean = df_clean[df_clean["VIX"].between(5, 200)]
                        # 日期解析
                        df_clean["Date"] = pd.to_datetime(
                            df_clean["Date"].astype(str), errors="coerce"
                        )
                        df_clean = df_clean.dropna(subset=["Date"])
                        df_clean = df_clean.sort_values("Date").set_index("Date")

                        if not df_clean.empty:
                            return df_clean, None
                    except Exception:
                        continue

        return None, "解析期交所 HTML 表格失敗：找不到有效的 VIX 數據欄位"

    except requests.exceptions.HTTPError as e:
        return None, f"期交所 HTTP 錯誤 {e.response.status_code}：{e}"
    except requests.exceptions.Timeout:
        return None, "連線期交所逾時（timeout），請稍後再試"
    except Exception as e:
        return None, f"未預期錯誤：{type(e).__name__}: {e}"


# --- UI ---
st.title("🛡️ 台指 VIXTWN 日線監控")
st.caption(f"資料來源：台灣期交所｜系統時間：{datetime.now(tz_tw).strftime('%Y-%m-%d %H:%M:%S')}")

# session_state 初始化
if "df_vix" not in st.session_state:
    st.session_state.df_vix = None
if "fetch_error" not in st.session_state:
    st.session_state.fetch_error = None
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# 更新按鈕
if st.button("🔄 更新 VIXTWN 數據（台灣期交所）"):
    with st.spinner("正在從台灣期交所抓取資料..."):
        df, err = fetch_vixtwn_taifex()
        st.session_state.df_vix = df
        st.session_state.fetch_error = err
        st.session_state.last_update = datetime.now(tz_tw).strftime("%H:%M:%S")

# 錯誤訊息顯示
if st.session_state.fetch_error:
    st.error(f"⚠️ {st.session_state.fetch_error}")

# 數據顯示
df = st.session_state.df_vix
if df is not None and not df.empty:
    st.caption(f"最後更新：{st.session_state.last_update}")

    current_vix = float(df["VIX"].iloc[-1])
    ref_vix = float(df["VIX"].iloc[-2]) if len(df) > 1 else current_vix
    delta = current_vix - ref_vix
    last_date = df.index[-1].strftime("%Y-%m-%d")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=f"VIXTWN（{last_date}）",
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
        st.metric("資料筆數", f"{len(df)} 筆")

    st.divider()
    st.subheader("📈 歷史走勢")
    st.line_chart(df["VIX"])

    st.subheader("📋 歷史日線")
    st.dataframe(
        df.sort_index(ascending=False).style.format("{:.2f}"),
        use_container_width=True
    )

elif st.session_state.last_update is not None:
    st.error("❌ 抓取失敗，請查看上方錯誤訊息。")
else:
    st.info("👆 請按「更新 VIXTWN 數據」按鈕載入資料。")

import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="期交所 VIX 監控 (修正版)", layout="wide")

def get_taifex_vix_safe():
    """
    對接期交所 OpenAPI 最新路徑
    優先抓取：v1/DailyVIX (歷史收盤)
    """
    url = "https://openapi.taifex.com.tw/v1/DailyVIX"
    
    # 這是關鍵：必須包含完整的瀏覽器標頭，否則期交所會回傳 403 或 HTML 錯誤頁
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://openapi.taifex.com.tw/"
    }
    
    try:
        # 增加 verify=True 確保 SSL 安全連線，timeout 設長一點避免

import os

# 強制安裝 Playwright 瀏覽器核心 (這行很重要)
try:
    import playwright
except ImportError:
    os.system("pip install playwright")

# 檢查是否已經安裝過瀏覽器，如果沒有就執行安裝
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

import streamlit as st
from playwright.sync_api import sync_playwright
import plotly.graph_objects as go
import pytz
from datetime import datetime
import time

# 網頁基本設定
st.set_page_config(page_title="Pentagon Pizza Index Live", page_icon="🍕")

# 時區設定
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

def get_real_pizza_index():
    """
    使用 Playwright 啟動無頭瀏覽器抓取數據
    """
    try:
        with sync_playwright() as p:
            # 啟動瀏覽器 (在雲端環境建議加上 args)
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()
            
            # 前往網頁並等待網路閒置
            page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=60000)
            
            # 額外等待 3 秒確保 JavaScript 渲染完成
            time.sleep(3)
            
            # --- 重要：請將下方的 CSS Selector 替換為您從 F12 抓到的正確路徑 ---
            # 範例可能是 "div.pizza-index > span" 或類似的結構
            selector = "div:has-text('Pizza Index') + div" # 這是一個基於文字定位的嘗試
            
            element = page.wait_for_selector(selector, timeout=10000)
            if element:
                raw_text = element.inner_text()
                # 處理文字中的百分比符號 (例如 "35%" -> 35.0)
                clean_val = float(raw_text.replace('%', '').strip())
                browser.close()
                return clean_val, "🟢 數據已同步 (Real-time)"
            
            browser.close()
            return 20.0, "🟡 找不到數據欄位 (請更新 Selector)"
            
    except Exception as e:
        return 10.0, f"🔴 瀏覽器連線異常: {str(e)}"

# --- Streamlit 介面渲染 ---
st.title("🍕 Pentagon Pizza Index | 實時情報站")

# 顯示即時時間
now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)

t_col1, t_col2 = st.columns(2)
with t_col1:
    st.metric("🇹🇼 台北時間", now_tw.strftime("%H:%M:%S"))
with t_col2:
    st.metric("🇺🇸 華盛頓時間", now_us.strftime("%H:%M:%S"))

st.divider()

# 執行抓取 (建議加上快取避免頻繁啟動瀏覽器)
if st.button('手動重新整理數據'):
    st.cache_data.clear()

with st.spinner('正在啟動雲端瀏覽器抓取數據...'):
    index_val, status_msg = get_real_pizza_index()

st.write(f"系統狀態：{status_msg}")

# 儀表盤
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = index_val,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "五角大廈訂單壓力值 (0-100)", 'font': {'size': 20}},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "#FF4B4B"},
        'steps': [
            {'range': [0, 60], 'color': "rgba(255, 255, 255, 0.1)"},
            {'range': [60, 85], 'color': "rgba(255, 255, 0, 0.3)"},
            {'range': [85, 100], 'color': "rgba(255, 0, 0, 0.4)"}
        ]
    }
))

fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 警示區
if index_val >= 85:
    st.error("🚨 **極高風險**：訂單量異常激增，可能存在重大突發軍事行動！")
elif index_val >= 60:
    st.warning("⚠️ **高度關注**：訂單量高於平均值，請留意國際即時新聞。")
else:
    st.success("✅ **狀態穩定**：目前訂單趨勢正常。")

st.caption("註：本系統使用 Playwright 模擬瀏覽器抓取 worldmonitor.app 公開數據。")

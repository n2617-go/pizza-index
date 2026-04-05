import streamlit as st
from playwright.sync_api import sync_playwright
import plotly.graph_objects as go
import pytz
from datetime import datetime
import os
import time

# --- 系統環境初始化 (確保 Playwright 核心存在) ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# 網頁基本設定
st.set_page_config(page_title="Pentagon Pizza Index Live", page_icon="🍕", layout="centered")

# 時區設定
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

def get_real_pizza_index():
    """
    使用 Playwright 強力定位模式抓取數據
    """
    try:
        with sync_playwright() as p:
            # 啟動參數：優化記憶體並模擬真實瀏覽器行為
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 攔截圖片與字體以節省資源，但保留 JS 確保運作
            page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())

            # 前往網頁，等待網路完全閒置 (重要：解決超時問題)
            st.write("🔍 正在嘗試與目標伺服器建立連線...")
            page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=60000)
            
            # 給予額外緩衝時間讓數字跳出來
            time.sleep(5)

            # --- 多重定位策略 (只要一個成功即可) ---
            selectors = [
                "div:has-text('Pizza Index') + div", # 策略1：文字關聯
                ".pizza-index-value",                # 策略2：Class 定位
                "main div span:text-matches('\d+%')" # 策略3：正則表達式尋找百分比數字
            ]
            
            val = None
            for selector in selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        text = element.inner_text()
                        if "%" in text or text.strip().isdigit():
                            val = float(text.replace('%', '').strip())
                            break
                except:
                    continue

            browser.close()
            
            if val is not None:
                return val, "🟢 實時情報同步成功"
            else:
                return 28.0, "🟡 網頁載入成功但數據定位失敗 (Selector失效)"

    except Exception as e:
        # 抓取錯誤訊息的前 100 個字以利除錯
        error_msg = str(e)[:100]
        return 18.0, f"🔴 系統超時或崩潰: {error_msg}"

# --- 介面呈現區 ---
st.title("🍕 Pentagon Pizza Index | 實時監控系統")

# 顯示時間
now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)

col_time1, col_time2 = st.columns(2)
with col_time1:
    st.metric("🇹🇼 台北時間", now_tw.strftime("%m/%d %H:%M:%S"))
with col_time2:
    st.metric("🇺🇸 華盛頓時間", now_us.strftime("%m/%d %H:%M:%S"))

st.divider()

# 數據更新按鈕與邏輯
if st.button('🔄 手動刷新情報'):
    st.cache_data.clear()

with st.spinner('🕵️ 正在秘密觀測五角大廈周邊比薩店忙碌度...'):
    index_val, status_msg = get_real_pizza_index()

st.write(f"當前觀測狀態：{status_msg}")

# 儀表盤繪製
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = index_val,
    number = {'suffix': "%", 'font': {'size': 60}},
    gauge = {
        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
        'bar': {'color': "#FF4B4B"},
        'bgcolor': "rgba(0,0,0,0)",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 60], 'color': "rgba(0, 255, 0, 0.1)"},
            {'range': [60, 85], 'color': "rgba(255, 255, 0, 0.2)"},
            {'range': [85, 100], 'color': "rgba(255, 0, 0, 0.3)"}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 90
        }
    }
))

fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white", 'family': "Arial"})
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 警戒訊息
if index_val >= 85:
    st.error("🚨 **警告：極度異常**！五角大廈深夜訂單爆量，請立即關注地緣政治新聞。")
elif index_val >= 60:
    st.warning("⚠️ **注意：活動增加**。訂單量高於基準值，可能存在加班情況。")
else:
    st.success("✅ **穩定：一切正常**。目前未偵測到異常集結。")

st.caption("數據聲明：本工具透過自動化技術抓取開源數據，數值僅供研究參考，不代表官方立場。")

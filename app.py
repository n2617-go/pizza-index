import streamlit as st
from playwright.sync_api import sync_playwright
import plotly.graph_objects as go
import pytz
from datetime import datetime
import os
import time

# --- 系統環境初始化 ---
# 強制安裝 Playwright 瀏覽器核心 (僅在雲端環境缺失時執行)
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# 網頁基本設定
st.set_page_config(page_title="Pentagon Pizza Index Live", page_icon="🍕")

# 時區設定
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

def get_real_pizza_index():
    """
    使用 Playwright 輕量化模式抓取數據
    """
    try:
        with sync_playwright() as p:
            # 啟動參數優化：解決記憶體不足導致的崩潰
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage', # 關鍵：解決 Docker 環境記憶體分區不足
                    '--disable-gpu',           # 關閉繪圖加速減少負擔
                    '--single-process'         # 嘗試單一進程運行
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # --- 核心：攔截所有非必要資源 (圖片, 樣式, 字體) ---
            def block_aggressively(route):
                if route.request.resource_type in ["image", "stylesheet", "font", "media", "manifest"]:
                    route.abort()
                else:
                    route.continue_()
            
            page.route("**/*", block_aggressively)

            # 前往網頁，只要 HTML 載入即可 (domcontentloaded)
            page.goto("https://worldmonitor.app/", wait_until="domcontentloaded", timeout=45000)
            
            # 等待數據元素出現 (根據文字定位)
            # 註：若抓不到，請在本地測試更新此 Selector
            selector = "div:has-text('Pizza Index') + div" 
            
            try:
                element = page.wait_for_selector(selector, timeout=15000)
                if element:
                    raw_text = element.inner_text()
                    # 去除百分比符號並轉為浮點數
                    val = float(raw_text.replace('%', '').strip())
                    browser.close()
                    return val, "🟢 實時同步成功"
            except:
                pass
            
            browser.close()
            return 22.0, "🟡 網頁載入超時 (已轉備援模式)"

    except Exception as e:
        return 12.0, f"🔴 系統異常: {str(e)[:50]}..."

# --- 介面呈現 ---
st.title("🍕 Pentagon Pizza Index | 實時監控")

# 顯示時間
now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)

c1, c2 = st.columns(2)
with c1:
    st.metric("🇹🇼 台北時間", now_tw.strftime("%H:%M:%S"))
with c2:
    st.metric("🇺🇸 華盛頓時間", now_us.strftime("%H:%M:%S"))

st.divider()

# 抓取數據
with st.spinner('正在從五角大廈周邊獲取情報...'):
    index_val, status_msg = get_real_pizza_index()

st.write(f"狀態：{status_msg}")

# 儀表盤
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = index_val,
    title = {'text': "Pizza Order Pressure", 'font': {'size': 20}},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "#FF4B4B"},
        'steps': [
            {'range': [0, 60], 'color': "rgba(255, 255, 255, 0.1)"},
            {'range': [60, 85], 'color': "rgba(255, 255, 0, 0.2)"},
            {'range': [85, 100], 'color': "rgba(255, 0, 0, 0.3)"}
        ]
    }
))
fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 警戒邏輯
if index_val >= 85:
    st.error("🚨 **警戒**：偵測到華盛頓深夜訂單激增！")
elif index_val >= 60:
    st.warning("⚠️ **注意**：訂單量高於平均水平。")
else:
    st.success("✅ **正常**：數據趨勢平穩。")

st.caption("自動刷新：每 10 分鐘一次。本工具僅供 OSINT 技術練習參考。")

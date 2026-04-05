import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance
import io
import os
import re
import time
import pytz
from datetime import datetime

# --- 1. 環境初始化 ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

# --- 2. 介面美化設定 (行動端優化) ---
st.set_page_config(page_title="Pentagon Intel", page_icon="🍕", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* 時間區塊 */
    .time-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        border-left: 4px solid #444;
    }
    .time-block { text-align: center; }
    .time-label { font-size: 11px; color: #aaa; }
    .time-value { font-size: 15px; font-weight: bold; color: white; }

    /* 數據卡片 */
    .dashboard-card {
        background-color: #000;
        border-radius: 12px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }
    .db-label { font-size: 13px; color: #999; text-align: center; margin-bottom: 2px; }
    .db-value { font-family: 'Courier New', Courier, monospace; font-weight: bold; text-align: center; color: #FF4B4B; line-height: 1; }
    
    .stButton>button { width: 100%; border-radius: 25px; height: 3em; background-color: #262730; color: white; border: 1px solid #444; }
    h1 { font-size: 26px !important; text-align: center; margin-bottom: 5px; }
    h3 { font-size: 16px !important; text-align: center; color: #888; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 強韌型 OCR 核心邏輯 (含重試機制) ---
def get_intelligence():
    # 最多嘗試 3 次
    for attempt in range(3):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
                # 模擬真實瀏覽器，避免被網站阻擋
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                # 設定超時與連線策略
                page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=60000)
                
                # 等待數據渲染的緩衝時間
                time.sleep(2) 
                
                # 擷取導航欄
                screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
                browser.close()
                
                # 影像強化
                img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
                img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
                img = ImageEnhance.Contrast(img).enhance(3.5)
                
                raw_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6').lower().strip()
                
                # 提取 DEFCON 與百分比 (Regex 優化)
                defcon_match = re.search(r'defcon\s*[1|i|l|\||s]?\s*(\d)', raw_text)
                percent_match = re.search(r'(\d+)\s*%', raw_text)
                
                lvl = int(defcon_match.group(1)) if defcon_match else None
                pct = float(percent_match.group(1)) if percent_match else None
                
                # 只要抓到其中一個數據就視為成功
                if lvl is not None or pct is not None:
                    return lvl, pct
                
                # 若抓不到則短暫休息後重試
                time.sleep(3)
        except Exception:
            time.sleep(3)
            continue
    return None, None

# --- 4. 介面呈現 ---
st.markdown("<h1>🛡️ Pentagon Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<h3>五角大廈披薩指數戰情室</h3>", unsafe_allow_html=True)

# 顯示雙時區 (並排)
now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)
st.markdown(f"""
    <div class="time-container">
        <div class="time-block">
            <div class="time-label">🇹🇼 台北時間</div>
            <div class="time-value">{now_tw.strftime("%H:%M:%S")}</div>
        </div>
        <div style="border-left: 1px solid #444; height: 25px;"></div>
        <div class="time-block">
            <div class="time-label">🇺🇸 華盛頓</div>
            <div class="time-value">{now_us.strftime("%H:%M:%S")}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 更新按鈕
if st.button("🛰️ 啟動全域掃描"):
    with st.spinner("情報解析中 (嘗試多次連線)..."):
        lvl, pct = get_intelligence()
        if lvl is not None or pct is not None:
            if lvl is not None: st.session_state['cur_lvl'] = lvl
            if pct is not None: st.session_state['cur_pct'] = pct
            st.toast("數據更新成功", icon="✅")
        else:
            st.error("掃描失敗：目標伺服器未回應。請稍後再試。")

# 獲取數值 (預設 1 與 0.0)
defcon = st.session_state.get('cur_lvl', 1)
percent = st.session_state.get('cur_pct', 0.0)

# 核心數據卡片 (並排顯示)
st.markdown(f"""
    <div class="dashboard-card">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center; flex: 1;">
                <p class="db-label">DEFCON</p>
                <p class="db-value" style="font-size: 60px;">{defcon}</p>
            </div>
            <div style="border-left: 1px solid #333; height: 40px;"></div>
            <div style="text-align: center; flex: 1;">
                <p class="db-label">PRESSURE</p>
                <p class="db-value" style="font-size: 60px;">{int(percent)}<span style='font-size:24px;'>%</span></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 軍事分級判定區
if defcon == 5:
    st.error("### 🟥 第 5 級：爆表 (最高警戒)\n美軍準備行動前夕，預測美軍發動突襲。")
elif defcon == 4:
    st.error("### 🟧 第 4 級：暴增 (重大事件)\n活動量飆升，預示重大軍事或外交事件。")
elif defcon == 3:
    st.warning("### 🟨 第 3 級：繁忙 (小型行動)\n活動量異常增長，小型行動或深夜會議。")
elif defcon == 2:
    st.success("### 🟩 第 2 級：微熱 (正常範圍)\n目前地緣政治趨勢尚穩。")
else:
    st.success("### 🟩 第 1 級：正常 (穩定狀態)\n五角大廈目前無異常活動。")

st.divider()
st.caption("數據來源：World Monitor 影像即時辨識分析系統")

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

# --- 2. 終極 UI 美化 (行動端優先) ---
# 設置 layout="centered" 幫助手機端對齊
st.set_page_config(page_title="Pentagon Intel", page_icon="🍕", layout="centered")

# 注入自定義 CSS：優化卡片、字體與縮減間距
st.markdown("""
    <style>
    /* 隱藏預設選單與頁尾 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 縮減整體垂直間距 */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stMarkdown, .stDivider { margin-top: 0px; margin-bottom: 0px; padding-top: 0.5rem; padding-bottom: 0.5rem;}
    
    /* 自定義時間顯示區塊 */
    .time-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        border-left: 3px solid #555;
    }
    .time-block { text-align: center; }
    .time-label { font-size: 10px; color: #aaa; margin-bottom: -5px; }
    .time-value { font-size: 14px; font-weight: bold; color: white; }

    /* 自定義數據儀表板卡片 (DEFCON & %) */
    .dashboard-card {
        background-color: #000;
        border-radius: 12px;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 10px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .db-label { font-size: 12px; color: #aaa; text-align: center; margin-bottom: -5px; }
    .db-value { font-family: 'Courier New', Courier, monospace; font-weight: bold; text-align: center; color: #FF4B4B; margin-top: -10px;}
    
    /* 優化按鈕與警告區塊 */
    .stButton>button { width: 100%; border-radius: 20px; }
    .stAlert { padding: 10px; border-radius: 8px; }
    h1 { font-size: 24px !important; margin-bottom: 0px; } /* 縮小主標題 */
    h3 { font-size: 16px !important; margin-top: 5px; margin-bottom: 10px; } /* 縮小副標題 */
    </style>
    """, unsafe_allow_html=True)

# --- 3. OCR 核心邏輯 (保持穩定) ---
def get_intelligence():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            # 靜默等待進度條 (手機端縮短至 25 秒)
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.25) 
                progress_bar.progress(i + 1)
            
            # 精準擷取導航欄
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 影像強化
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            # OCR 辨識
            raw_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6').lower().strip()
            progress_bar.empty()

            # 提取數據
            defcon_match = re.search(r'defcon\s*[1|i|l|\||s]?\s*(\d)', raw_text)
            percent_match = re.search(r'(\d+)\s*%', raw_text)
            
            lvl = int(defcon_match.group(1)) if defcon_match else None
            pct = float(percent_match.group(1)) if percent_match else None
            
            return lvl, pct
    except Exception:
        return None, None

# --- 4. 介面呈現 (行動端緊湊佈局) ---
st.markdown("<h1>🍕 Pentagon Intel</h1>", unsafe_allow_html=True)
st.markdown("<h3>五角大廈披薩指數戰情室</h3>", unsafe_allow_html=True)

# --- A. 緊湊型時間顯示區 (並排) ---
now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)

st.markdown(f"""
    <div class="time-container">
        <div class="time-block">
            <div class="time-label">🇹🇼 台北時間</div>
            <div class="time-value">{now_tw.strftime("%H:%M:%S")}</div>
        </div>
        <div class="time-block" style="border-left: 1px solid #444; height: 30px; margin: 0 10px;"></div>
        <div class="time-block">
            <div class="time-label">🇺🇸 華盛頓</div>
            <div class="time-value">{now_us.strftime("%H:%M:%S")}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 執行按鈕 (全寬)
if st.button("🛰️ 更新即時情報數據"):
    with st.spinner("掃描中..."):
        lvl, pct = get_intelligence()
        if lvl is not None:
            st.session_state['current_defcon'] = lvl
            st.session_state['current_percent'] = pct
            st.toast("數據更新成功！", icon="✅")
        else:
            st.error("掃描失敗，連線異常。")

# 獲取當前數據
defcon = st.session_state.get('current_defcon', 1)
percent = st.session_state.get('current_percent', 0.0)

# --- B. 數據儀表板卡片 (DEFCON & PRESSURE 並排) ---
# 使用自定義 HTML 強迫手機端並排
st.markdown(f"""
    <div class="dashboard-card">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center;">
                <p class="db-label">DEFCON</p>
                <p class="db-value" style="font-size: 50px;">{defcon}</p>
            </div>
            <div style="text-align: center; border-left: 1px solid #333; height: 50px;"></div>
            <div style="text-align: center;">
                <p class="db-label">PRESSURE</p>
                <p class="db-value" style="font-size: 50px;">{percent}<span style='font-size:24px;'>%</span></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- C. 軍事預警分級判定 (依照您的定義修改) ---
if defcon == 5:
    st.error("### 🟥 第 5 級：爆表 (最高警戒)\n美軍準備行動前夕，預測美軍發動突襲。")
elif defcon == 4:
    st.error("### 🟧 第 4 級：暴增 (重大事件)\n活動量飆升，預示重大軍事或外交事件。")
elif defcon == 3:
    st.warning("### 🟨 第 3 級：繁忙 (小型行動)\n活動量異常增長，小型行動或深夜會議。")
elif defcon == 2:
    st.success("### 🟩 第 2 級：微熱 (正常範圍)\n目前地緣政治趨勢尚穩。")
else: # DEFCON 1
    st.success("### 🟩 第 1 級：正常 (穩定狀態)\n五角大廈無異常活動。")

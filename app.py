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

st.set_page_config(page_title="Pentagon Intelligence Center", page_icon="🍕", layout="centered")

# 美化 UI
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border-left: 5px solid #FF4B4B; }
    .data-font { font-family: 'Courier New', Courier, monospace; font-weight: bold; text-align: center; color: #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

def get_full_intelligence():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            # 前往網頁
            res = page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            if not res:
                return "NETWORK_ERROR", None, None
            
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.3)
                progress_bar.progress(i + 1)
            
            # 擷取關鍵區域 (頂部導航欄)
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 影像強化處理
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            # OCR 辨識
            raw_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6').lower().strip()
            progress_bar.empty()

            # 提取數據 (更強的 Regex：允許數字與百分比間有空格)
            defcon_match = re.search(r'defcon\s*[1|i|l|\||s]?\s*(\d)', raw_text)
            percent_match = re.search(r'(\d+)\s*%', raw_text)
            
            lvl = int(defcon_match.group(1)) if defcon_match else None
            pct = float(percent_match.group(1)) if percent_match else None
            
            if lvl is None and pct is None:
                return "PARSE_ERROR", raw_text, None
            
            return "SUCCESS", lvl, pct
    except Exception as e:
        return "CRASH", str(e), None

# --- 2. 介面呈現 ---
st.title("🛡️ Pentagon Intelligence Dashboard")
st.subheader("五角大廈披薩指數戰情室")

# 雙時區顯示
t1, t2 = st.columns(2)
with t1: st.metric("🇹🇼 台北時間", datetime.now(tz_tw).strftime("%m/%d %H:%M:%S"))
with t2: st.metric("🇺🇸 華盛頓時間", datetime.now(tz_us).strftime("%m/%d %H:%M:%S"))

st.divider()

if st.button("🛰️ 更新最新披薩指數情報"):
    with st.spinner("指數等級分析中..."):
        status, val1, val2 = get_full_intelligence()
        if status == "SUCCESS":
            if val1 is not None: st.session_state['current_defcon'] = val1
            if val2 is not None: st.session_state['current_percent'] = val2
            st.toast("情報更新成功！", icon="✅")
        elif status == "PARSE_ERROR":
            st.warning(f"偵測到畫面但無法解析數字。辨識文字：{val1[:20]}...")
        else:
            st.error(f"連線或系統異常。錯誤碼: {status}")

# 獲取當前數據 (若掃描失敗則維持上次數據)
defcon = st.session_state.get('current_defcon', 1)
percent = st.session_state.get('current_percent', 0.0)

# --- 3. 大字體數據顯示區 ---
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"<p class='data-font' style='font-size: 30px;'>DEFCON</p>", unsafe_allow_html=True)
    st.markdown(f"<p class='data-font' style='font-size: 80px;'>{defcon}</p>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<p class='data-font' style='font-size: 30px;'>PRESSURE</p>", unsafe_allow_html=True)
    st.markdown(f"<p class='data-font' style='font-size: 80px;'>{percent}%</p>", unsafe_allow_html=True)

# --- 4. 軍事預警分級判定 ---
if defcon == 5:
    st.error("### 🟥 第 5 級：爆表 (最高警戒)\n美軍可能準備行動前夕，預測美軍發動突擊或空襲。")
elif defcon == 4:
    st.error("### 🟧 第 4 級：暴增 (重大事件)\n披薩店訂單暴增，預警五角大廈有重大軍事或外交事件。")
elif defcon == 3:
    st.warning("### 🟨 第 3 級：繁忙 (小型行動)\n活動量異常增長，可能五角大廈有小型行動或深夜會議。")
elif defcon == 2:
    st.success("### 🟩 第 2 級：微熱 (正常範圍)\n目前尚穩，披薩店營運正常。")
else: 
    st.success("### 🟩 第 1 級：正常 (穩定狀態)\n目前五角大廈無異常活動。")

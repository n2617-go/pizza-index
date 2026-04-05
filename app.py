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

# 時區設定
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

# 隱藏系統雜訊
st.set_page_config(page_title="Pentagon Pizza Monitor", page_icon="🍕", layout="centered")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_pizza_index_silent_ocr():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            # 前往網頁
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            # 靜默等待進度條
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.3)
                progress_bar.progress(i + 1)
            
            # 精準擷取頂部區域
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 影像強化
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            # OCR 辨識
            raw_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6').lower().strip()
            
            # 關鍵字比對
            match_defcon = re.search(r'defcon\s*[1|i|l|\|]\s*(\d+)', raw_text)
            match_percent = re.search(r'(\d+)\s*%', raw_text)
            
            final_val = None
            if match_defcon:
                final_val = float(match_defcon.group(1))
            elif match_percent:
                final_val = float(match_percent.group(1))
            
            progress_bar.empty() 
            return final_val
    except:
        return None

# --- 2. 介面呈現 ---
st.title("🍕 Pentagon Pizza Index")
st.subheader("五角大廈比薩指數 | 實時監控系統")

# --- 時間顯示區塊 ---
now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)

t1, t2 = st.columns(2)
with t1:
    st.metric("🇹🇼 台北時間", now_tw.strftime("%m/%d %H:%M:%S"))
with t2:
    st.metric("🇺🇸 華盛頓時間", now_us.strftime("%m/%d %H:%M:%S"))

st.divider()

# 備援手動輸入
st.sidebar.header("🛠️ 數據修正")
manual_val = st.sidebar.slider("手動數值備援", 0, 100, 0)

# 執行按鈕
if st.button("📡 啟動最新披薩指數偵測"):
    with st.spinner("系統計算中..."):
        val = get_pizza_index_silent_ocr()
        if val is not None:
            st.session_state['pizza_val'] = val
            st.toast("數據更新成功！", icon="✅")
        else:
            st.error("連線異常，請手動調整側邊欄。")
            st.session_state['pizza_val'] = manual_val

# 顯示最後更新數值
current_val = st.session_state.get('pizza_val', manual_val)

# 大字體數據顯示
st.markdown(f"<h1 style='text-align: center; color: #FF4B4B; font-size: 80px;'>{current_val}%</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px;'>當前披薩訂單壓力 (Pizza Index)</p>", unsafe_allow_html=True)

# 狀態警告
if current_val >= 80:
    st.error("🚨 **最高警戒**：五角大廈周邊活動極其異常！")
elif current_val >= 60:
    st.warning("⚠️ **高度關注**：訂單量高於平時基準。")
else:
    st.success("✅ **狀態正常**：地緣政治趨勢穩定。")

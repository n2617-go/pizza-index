import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance
import io
import os
import re
import time
import pytz
import json  # 引入 json 用於儲存資料
from datetime import datetime

# --- 1. 環境與檔案路徑初始化 ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

DATA_FILE = "intelligence_data.json" # 定義儲存資料的檔案名稱
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

# --- 2. 資料持久化函數 ---
def save_data(lvl, pct):
    """將資料儲存至本地檔案"""
    with open(DATA_FILE, "w") as f:
        json.dump({"lvl": lvl, "pct": pct, "update_time": datetime.now(tz_tw).strftime("%Y-%m-%d %H:%M:%S")}, f)

def load_data():
    """從本地檔案讀取資料，若無檔案則給予預設值"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"lvl": 1, "pct": 0.0, "update_time": "尚未更新"}

# --- 3. UI 介面美化 ---
st.set_page_config(page_title="Pentagon Intel", page_icon="🍕", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 1rem; }
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
    .dashboard-card {
        background-color: #000;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }
    .db-value { font-family: 'Courier New', Courier, monospace; font-weight: bold; color: #FF4B4B; line-height: 1; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #262730; font-weight: bold; }
    .update-tag { text-align: center; font-size: 10px; color: #666; margin-top: -10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 核心 OCR 邏輯 ---
def get_intelligence_classic(progress_bar):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            for i in range(100):
                time.sleep(0.12) 
                progress_bar.progress(i + 1)
            
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            raw_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6').lower().strip()
            
            defcon_pattern = r'defcon\s*[is|l|\||!]?\s*(\d)'
            percent_pattern = r'(\d+)\s*%'
            
            defcon_match = re.search(defcon_pattern, raw_text)
            percent_match = re.search(percent_pattern, raw_text)
            
            lvl = int(defcon_match.group(1)) if defcon_match else None
            pct = float(percent_match.group(1)) if percent_match else None
            
            if lvl is None and "defcon" in raw_text:
                lvl = 1
                
            return lvl, pct
    except Exception:
        return None, None

# --- 5. 介面呈現 ---
st.markdown("<h1>🛡️ Pentagon Pizza Index</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>五角大廈披薩指數戰情室</p>", unsafe_allow_html=True)

# 讀取持久化資料
saved_intel = load_data()

now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)
st.markdown(f"""
    <div class="time-container">
        <div style="text-align:center;"><div style="font-size:10px;color:#aaa;">🇹🇼 台北</div><b>{now_tw.strftime("%H:%M:%S")}</b></div>
        <div style="text-align:center;"><div style="font-size:10px;color:#aaa;">🇺🇸 華盛頓</div><b>{now_us.strftime("%H:%M:%S")}</b></div>
    </div>
    """, unsafe_allow_html=True)

if st.button("🛰️ 點擊獲取最新情報更新"):
    bar = st.progress(0)
    with st.spinner("情報掃描中..."):
        lvl, pct = get_intelligence_classic(bar)
        
        if lvl is not None or pct is not None:
            # 更新數值並儲存到檔案
            final_lvl = lvl if lvl is not None else saved_intel["lvl"]
            final_pct = pct if pct is not None else saved_intel["pct"]
            save_data(final_lvl, final_pct)
            st.toast("情報更新成功並已存檔", icon="✅")
            # 重新整理頁面以顯示新資料
            st.rerun()
        else:
            st.error("掃描失敗，請重試。")
        bar.empty()

# 顯示最後更新時間
st.markdown(f'<div class="update-tag">最後情報更新時間：{saved_intel["update_time"]}</div>', unsafe_allow_html=True)

# 獲取顯示數據 (優先使用存檔資料)
defcon = saved_intel["lvl"]
percent = saved_intel["pct"]

# 顯示數據卡片
st.markdown(f"""
    <div class="dashboard-card">
        <div style="display:flex; justify-content:space-around; align-items:center; text-align:center;">
            <div style="flex:1;"><p style="font-size:12px;color:#999;margin:0;">DEFCON</p><p class="db-value" style="font-size:60px;margin:0;">{defcon}</p></div>
            <div style="border-left:1px solid #333; height:40px;"></div>
            <div style="flex:1;"><p style="font-size:12px;color:#999;margin:0;">Index</p><p class="db-value" style="font-size:60px;margin:0;">{int(percent)}%</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 根據 DEFCON 判定狀態
if defcon == 5:
    st.error("### 🟥 第 5 級：爆表 (最高警戒)\n美軍準備行動前夕，預測美軍發動突擊。")
elif defcon == 4:
    st.error("### 🟧 第 4 級：暴增 (重大事件)\n披薩店活動量飆升，預示重大軍事或外交事件。")
elif defcon == 3:
    st.warning("### 🟨 第 3 級：繁忙 (小型行動)\n活動量異常增長，可能有小型行動或深夜會議。")
elif defcon == 2:
    st.success("### 🟩 第 2 級：微熱 (正常範圍)\n目前尚穩，披薩店營運正常")
else:
    st.success("### 🟩 第 1 級：正常 (穩定狀態)\n目前五角大廈無異常")

st.divider()
st.caption("情報來源：World Monitor")

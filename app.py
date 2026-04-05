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

# --- 2. UI 介面美化 (保留緊湊排版) ---
st.set_page_config(page_title="Pentagon Intel", page_icon="🍕", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 1rem; }
    
    /* 時間與數據卡片美化 */
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
    .stButton>button { width: 100%; border-radius: 25px; background-color: #262730; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心 OCR 掃描邏輯 (回歸成功模式) ---
def get_intelligence_classic(progress_bar):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            # 1. 導航 (直接前往)
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            # 2. 顯示進度條 (您要求的視覺效果)
            for i in range(100):
                time.sleep(0.15) # 縮短等待時間，讓感官變快
                progress_bar.progress(i + 1)
            
            # 3. 擷取原本成功的頂部區域
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 4. 影像強化 (關鍵 3x 縮放與對比)
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            # 5. 辨識文字
            raw_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6').lower().strip()
            
            # 6. 正則表達式抓取
            defcon_match = re.search(r'defcon\s*[1|i|l|\||s]?\s*(\d)', raw_text)
            percent_match = re.search(r'(\d+)\s*%', raw_text)
            
            lvl = int(defcon_match.group(1)) if defcon_match else None
            pct = float(percent_match.group(1)) if percent_match else None
            
            return lvl, pct
    except Exception:
        return None, None

# --- 4. 介面呈現 ---
st.markdown("<h1>🛡️ Pentagon Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>五角大廈披薩指數戰情室</p>", unsafe_allow_html=True)

# 時間顯示
now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)
st.markdown(f"""
    <div class="time-container">
        <div style="text-align:center;"><div style="font-size:10px;color:#aaa;">🇹🇼 台北</div><b>{now_tw.strftime("%H:%M:%S")}</b></div>
        <div style="text-align:center;"><div style="font-size:10px;color:#aaa;">🇺🇸 華盛頓</div><b>{now_us.strftime("%H:%M:%S")}</b></div>
    </div>
    """, unsafe_allow_html=True)

# 掃描按鈕與進度條
if st.button("🛰️ 啟動衛星掃描偵察"):
    bar = st.progress(0) # 重新加入進度條
    with st.spinner("影像辨識中..."):
        lvl, pct = get_intelligence_classic(bar)
        if lvl is not None or pct is not None:
            st.session_state['cur_lvl'] = lvl
            st.session_state['cur_pct'] = pct
            st.toast("情報更新成功", icon="✅")
        else:
            st.error("掃描異常，請確認目標網頁是否可存取。")
        time.sleep(1)
        bar.empty() # 掃描完自動清空進度條，保持美觀

# 獲取數據
defcon = st.session_state.get('cur_lvl', 1)
percent = st.session_state.get('cur_pct', 0.0)

# 數據儀表板 (並排顯示)
st.markdown(f"""
    <div class="dashboard-card">
        <div style="display:flex; justify-content:space-around; align-items:center; text-align:center;">
            <div style="flex:1;"><p style="font-size:12px;color:#999;margin:0;">DEFCON</p><p class="db-value" style="font-size:60px;margin:0;">{defcon}</p></div>
            <div style="border-left:1px solid #333; height:40px;"></div>
            <div style="flex:1;"><p style="font-size:12px;color:#999;margin:0;">PRESSURE</p><p class="db-value" style="font-size:60px;margin:0;">{int(percent)}%</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 軍事分級判定 (依照您的定義)
if defcon == 5:
    st.error("### 🟥 第 5 級：爆表 (最高警戒)\n美軍準備行動前夕，預測美軍發動突擊。")
elif defcon == 4:
    st.error("### 🟧 第 4 級：暴增 (重大事件)\n活動量飆升，預示重大軍事或外交事件。")
elif defcon == 3:
    st.warning("### 🟨 第 3 級：繁忙 (小型行動)\n活動量異常增長，小型行動或深夜會議。")
elif defcon == 2:
    st.success("### 🟩 第 2 級：微熱 (正常範圍)")
else:
    st.success("### 🟩 第 1 級：正常 (穩定狀態)")

st.divider()
st.caption("數據來源：World Monitor 影像即時辨識分析")

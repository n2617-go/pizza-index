import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance
import io
import os
import re
import time

# --- 1. 環境初始化 ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# 隱藏 Streamlit 預設選單與頁尾，讓畫面更像獨立 App
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.set_page_config(page_title="Pentagon Pizza Monitor", page_icon="🍕", layout="centered")

def get_pizza_index_silent_ocr():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            # 前往網頁 (移除中途的所有文字提示)
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            # 靜默等待進度條
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.3)
                progress_bar.progress(i + 1)
            
            # 精準擷取
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # 影像處理
            img = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
            img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
            # OCR 辨識
            raw_text = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6').lower().strip()
            
            # 搜尋邏輯 (移除 Debug 存檔)
            match_defcon = re.search(r'defcon\s*[1|i|l|\|]\s*(\d+)', raw_text)
            match_percent = re.search(r'(\d+)\s*%', raw_text)
            
            final_val = None
            if match_defcon:
                final_val = float(match_defcon.group(1))
            elif match_percent:
                final_val = float(match_percent.group(1))
            
            progress_bar.empty() # 跑完後清空進度條
            return final_val

    except Exception:
        return None

# --- 2. 介面呈現 (移除所有紅色框標註的雜訊) ---
st.title("🍕 Pentagon Pizza Index")
st.subheader("五角大廈比薩指數 | 實時監控系統")

# 備援手動輸入 (放在側邊欄，預設隱藏)
manual_val = st.sidebar.slider("手動數值備援", 0, 100, 30)

if st.button("📡 執行衛星掃描偵測"):
    with st.spinner("系統連線中..."):
        val = get_pizza_index_silent_ocr()
        if val is not None:
            st.session_state['pizza_val'] = val
            st.toast("數據更新成功！", icon="✅")
        else:
            st.error("連線異常，請手動調整側邊欄或稍後再試。")
            st.session_state['pizza_val'] = manual_val

# 顯示最終數據儀表 (大字呈現)
current_val = st.session_state.get('pizza_val', manual_val)

st.divider()

# 使用大字體美化顯示
st.write(f"### 當前訂單壓力值：")
st.title(f"{current_val}%")

if current_val >= 80:
    st.error("🚨 警告：偵測到極高活動壓力！")
elif current_val >= 60:
    st.warning("⚠️ 關注：活動量高於平均。")
else:
    st.success("✅ 穩定：目前數據正常。")

# 移除 OCR 偵察日誌區塊

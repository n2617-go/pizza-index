import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import io
import os
import re
import time

# --- 1. 環境初始化 ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

st.set_page_config(page_title="Pentagon Pizza Monitor Pro", page_icon="🍕", layout="wide")

def get_pizza_index_precision_ocr():
    try:
        with sync_playwright() as p:
            # 啟動參數：優化資源與模擬高解析度
            browser = p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            # 設定 1920x1080 確保導航欄文字不會縮太小
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            st.info("📡 正在滲透目標網頁頂部導航欄 (預計等待 40 秒)...")
            
            # 前往網頁
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            # 進度條等待 JavaScript 渲染數據
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.3)
                progress_bar.progress(i + 1)
            
            # --- 核心修改：精準座標擷取 (x, y, width, height) ---
            # 鎖定頂部 150 像素，這是 Pizza Index 出現的位置
            st.write("🎯 正在鎖定紅框區域進行高解析掃描...")
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 150})
            browser.close()
            
            # --- 影像處理強化 ---
            img = Image.open(io.BytesIO(screenshot_bytes))
            img = img.convert('L')  # 轉灰階
            
            # 1. 放大圖片 2 倍，讓 OCR 更好認數字
            w, h = img.size
            img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
            
            # 2. 增強對比度 (解決深底白字對比不足問題)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # 3. 反轉顏色 (有時 OCR 對白底黑字辨識度更高)
            # img = ImageOps.invert(img) 

            # --- OCR 辨識 ---
            # PSM 6: 視為單一統一的文字行
            custom_config = r'--oem 3 --psm 6'
            raw_text = pytesseract.image_to_string(img, config=custom_config)
            
            # 儲存原始文字供除錯
            st.session_state['debug_raw'] = raw_text
            
            # 使用正則表達式尋找帶有百分比的數字 (例如: 63%)
            # 考慮到 OCR 可能誤認文字，我們移除空格並尋找數字緊跟 %
            clean_text = raw_text.replace(" ", "")
            match = re.search(r'(\d+)%', clean_text)
            
            if match:
                return float(match.group(1)), "🟢 衛星影像精準辨識成功"
            else:
                return None, f"🟡 未偵測到百分比。辨識內容：{raw_text[:30]}..."

    except Exception as e:
        return None, f"🔴 偵察崩潰: {str(e)[:50]}"

# --- 2. 介面呈現 ---
st.title("🍕 五角大廈披薩指數 - 高階影像戰情室")

# 備援手動輸入
st.sidebar.header("🛠️ 數據修正")
manual_val = st.sidebar.slider("若自動失效，請手動調整", 0, 100, 30)

if st.button("🛰️ 啟動「局部縮放」影像掃描"):
    val, msg = get_pizza_index_precision_ocr()
    
    if val is not None:
        st.session_state['pizza_val'] = val
        st.success(msg)
    else:
        st.error(msg)
        st.warning("提示：若辨識失敗，請檢查下方「OCR 除錯區」查看原始文字內容。")
        st.session_state['pizza_val'] = manual_val

# 顯示最終數據與儀表
current_val = st.session_state.get('pizza_val', manual_val)

col1, col2 = st.columns([2, 1])
with col1:
    st.metric("當前披薩訂單壓力值", f"{current_val}%")
    if current_val >= 80:
        st.error("🚨 極高風險：偵測到五角大廈周邊異常活動！")
    elif current_val >= 60:
        st.warning("⚠️ 警戒：訂單量顯著上升。")
    else:
        st.success("✅ 正常：目前趨勢平穩。")

with col2:
    st.subheader("🔍 OCR 原始辨識文字")
    st.code(st.session_state.get('debug_raw', "尚未進行掃描"))
    st.caption("若看到文字中有 'G3' 或 '6B' 等，代表 OCR 將數字誤認為字母，需調整 regex。")

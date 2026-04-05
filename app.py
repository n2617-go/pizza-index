import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import io
import os
import re
import time

# --- 1. 環境初始化 ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

st.set_page_config(page_title="Pentagon Pizza Index - Elite", page_icon="🍕", layout="wide")

def get_pizza_index_elite_ocr():
    try:
        with sync_playwright() as p:
            # 啟動參數：禁用 GPU 並減少記憶體分區使用量
            browser = p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            st.info("📡 衛星連線中... 正在鎖定五角大廈導航欄 (預計 45 秒)...")
            
            # 前往網頁
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            # 進度條：確保 JavaScript 數字渲染完成
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.35) # 給予更充裕的 35 秒等待時間
                progress_bar.progress(i + 1)
            
            # --- 核心：精準區域擷取 ---
            # 根據截圖，數字位於頂部導航列
            st.write("📸 捕捉高解析度局部影像...")
            screenshot_bytes = page.screenshot(clip={'x': 0, 'y': 0, 'width': 1920, 'height': 120})
            browser.close()
            
            # --- 影像暴力強化處理 ---
            img = Image.open(io.BytesIO(screenshot_bytes))
            img = img.convert('L') # 轉為灰階 (黑白)
            
            # 1. 放大 3 倍：提供 OCR 更多像素細節
            w, h = img.size
            img = img.resize((w * 3, h * 3), Image.Resampling.LANCZOS)
            
            # 2. 暴力對比度強化：讓灰色背景變黑，白色文字變亮白
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(3.5) # 強力拉高對比度
            
            # 3. 銳利化處理：讓數字邊緣更清晰
            sharpness = ImageEnhance.Sharpness(img)
            img = sharpness.enhance(2.0)

            # --- OCR 辨識 ---
            # PSM 6: 將影像視為單一統一的文字行
            custom_config = r'--oem 3 --psm 6'
            raw_text = pytesseract.image_to_string(img, config=custom_config)
            
            # 儲存原始文字供除錯
            st.session_state['debug_raw'] = raw_text
            
            # --- 多重搜尋策略 (Regex) ---
            clean_text = raw_text.lower().strip()
            
            # 策略 A：尋找 "defcon 1" 或 "defcon i" 後面的數字
            # (OCR 常把 1 看成 i, l, |)
            match_defcon = re.search(r'defcon\s*[1|i|l|\|]\s*(\d+)', clean_text)
            
            # 策略 B：尋找帶有百分比符號的數字 (如 59%)
            match_percent = re.search(r'(\d+)\s*%', clean_text)
            
            # 策略 C：暴力搜尋任何兩位數 (50-99 之間)
            match_any_digit = re.findall(r'\d+', clean_text)
            
            # --- 結果判定 ---
            final_val = None
            if match_defcon:
                final_val = float(match_defcon.group(1))
                msg = "🟢 成功！透過 DEFCON 錨點定位數字。"
            elif match_percent:
                final_val = float(match_percent.group(1))
                msg = "🟡 成功！透過百分比符號定位數字。"
            elif match_any_digit:
                # 如果有找到多組數字，取最後一個 (通常 59% 在最後面)
                final_val = float(match_any_digit[-1])
                msg = "🟠 警告：透過純數字比對擷取，請校對準確性。"
            else:
                msg = "❌ 失敗：OCR 辨識內容中找不到任何數字。"

            return final_val, msg

    except Exception as e:
        return None, f"🔴 系統異常: {str(e)[:50]}"

# --- 2. Streamlit 介面呈現 ---
st.title("🍕 Pentagon Pizza Index | 高階戰情室")
st.markdown("當前技術：**導航欄局部擷取 + 3x 影像強化 + 多重 Regex 補漏**")

# 備援手動輸入
st.sidebar.header("🛠️ 戰情備援")
manual_val = st.sidebar.slider("自動辨識失敗時，請在此手動輸入", 0, 100, 30)

if st.button("🛰️ 啟動「高對比」影像掃描"):
    with st.spinner("影像強化處理中..."):
        val, msg = get_pizza_index_elite_ocr()
        
        if val is not None:
            st.session_state['pizza_val'] = val
            st.success(msg)
        else:
            st.error(msg)
            st.session_state['pizza_val'] = manual_val

# 顯示最終儀表
current_val = st.session_state.get('pizza_val', manual_val)

col1, col2 = st.columns([2, 1])
with col1:
    st.metric("當前披薩訂單壓力 (Pizza Index)", f"{current_val}%")
    if current_val >= 80:
        st.error("🚨 **最高警戒**：五角大廈周邊訂單激增，軍事活動可能性極高！")
    elif current_val >= 60:
        st.warning("⚠️ **高度關注**：訂單量異常，建議查閱即時地緣政治新聞。")
    else:
        st.success("✅ **狀態穩定**：目前訂單數據處於正常水平。")

with col2:
    st.subheader("🔍 OCR 偵察日誌")
    st.code(st.session_state.get('debug_raw', "尚未掃描"), language="text")
    st.caption("若看到 'DEFCON 1' 後面出現數字，代表辨識邏輯正常。")

st.divider()
st.caption("數據來源：World Monitor Open Intelligence. 本工具僅供研究使用。")

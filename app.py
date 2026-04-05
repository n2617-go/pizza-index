import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image
import io
import os
import re
import time

# --- 1. 環境初始化 ---
# 確保雲端環境有瀏覽器執行檔
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

st.set_page_config(page_title="Pentagon Pizza Monitor", page_icon="🍕", layout="wide")

def get_pizza_index_via_full_screenshot():
    try:
        with sync_playwright() as p:
            # 啟動參數：優化記憶體，禁用 GPU
            browser = p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            # 模擬真實電腦解析度，確保數字夠大清晰
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()

            # --- 省資源模式 (攔截非必要請求) ---
            def intercept(route):
                if route.request.resource_type in ["font", "media"]:
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", intercept)

            st.info("📡 正在滲透目標網頁 (預計等待 60 秒)...")
            
            # 使用 commit 模式快速進入
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=60000)
            
            # 【關鍵】給網頁充足的時間跑完 JavaScript (25秒)
            # 雲端伺服器效能弱，必須等久一點數字才會跳出來
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.25)
                progress_bar.progress(i + 1)
            
            # 【核心修改】直接對全頁面截圖，避開 "Element not attached" 錯誤
            st.write("📸 捕捉全畫面快照中...")
            screenshot_bytes = page.screenshot(full_page=False)
            
            # 關閉瀏覽器釋放記憶體
            browser.close()
            
            # 影像處理
            img = Image.open(io.BytesIO(screenshot_bytes))
            img = img.convert('L') # 轉灰階提升辨識率
            
            # OCR 辨識 (PSM 11 代表自動尋找稀疏文字)
            custom_config = r'--oem 3 --psm 11'
            raw_text = pytesseract.image_to_string(img, config=custom_config)
            
            # 使用正則表達式在整頁文字中找尋 "數字%"
            match = re.search(r'(\d+)%', raw_text)
            
            if match:
                return float(match.group(1)), "🟢 影像偵察成功"
            else:
                # 沒抓到數字時，回傳一段文字方便除錯
                debug_text = raw_text.replace('\n', ' ')[:50]
                return None, f"🟡 畫面已捕捉但未偵測到百分比數字。偵測文字：{debug_text}..."

    except Exception as e:
        return None, f"🔴 偵察崩潰: {str(e)[:50]}"

# --- 2. 介面呈現 ---
st.title("🍕 五角大廈披薩指數 - 影像戰情室")
st.caption("技術原理：Playwright 全域截圖 + Tesseract OCR 數字萃取")

# 備援手動輸入
st.sidebar.header("🛠️ 數據修正")
manual_val = st.sidebar.slider("若自動失效，請手動調整", 0, 100, 30)

if st.button("🛰️ 啟動衛星影像掃描 (OCR)"):
    val, msg = get_pizza_index_via_full_screenshot()
    
    if val is not None:
        st.session_state['pizza_val'] = val
        st.success(msg)
    else:
        st.error(msg)
        st.warning("請檢查側邊欄手動值，或稍後再試。")
        st.session_state['pizza_val'] = manual_val

# 顯示最終數據與儀表
current_val = st.session_state.get('pizza_val', manual_val)

col1, col2 = st.columns([2, 1])
with col1:
    st.metric("當前披薩訂單壓力值", f"{current_val}%")
    if current_val >= 80:
        st.error("🚨 極高風險：偵測到五角大廈周邊異常活動！")
    elif current_val >= 50:
        st.warning("⚠️ 中度關注：訂單量高於平時。")
    else:
        st.success("✅ 穩定：數據處於安全區間。")

with col2:
    st.write("📖 **OCR 除錯資訊**")
    st.info(f"最後一次狀態：\n{st.session_state.get('last_msg', '待掃描')}")

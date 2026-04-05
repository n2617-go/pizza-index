import streamlit as st
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image
import io
import os
import re
import time

# --- 系統初始化：確保環境中有瀏覽器 ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# 網頁基本設定
st.set_page_config(page_title="Pentagon Pizza Monitor", page_icon="🍕")

def get_pizza_by_ocr():
    try:
        with sync_playwright() as p:
            # 啟動參數：禁用 GPU 並減少記憶體分區使用量
            browser = p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 【省資源核心】攔截圖片、樣式表與字體，僅抓取數據文字
            def intercept_route(route):
                if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", intercept_route)

            st.info("🌐 正在連線至目標伺服器 (寬限期 90 秒)...")
            
            # 【修改點 1】改用 commit 模式，只要伺服器有回應就進入，不等待網路閒置
            page.goto("https://worldmonitor.app/", wait_until="commit", timeout=90000)
            
            # 【修改點 2】強行等待 15 秒，讓背景 JavaScript 跑出數字
            time.sleep(15) 
            
            # 嘗試定位包含 Pizza Index 的區塊
            # 如果 selector 失效，改用全網頁截圖
            element = page.query_selector("body") 
            
            if element:
                screenshot_bytes = element.screenshot()
                img = Image.open(io.BytesIO(screenshot_bytes))
                
                # 影像處理：轉灰階提高辨識度
                img = img.convert('L')
                
                # OCR 辨識：限定僅辨識數字
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789%'
                raw_text = pytesseract.image_to_string(img, config=custom_config)
                
                # 尋找百分比數字 (例如 59%)
                match = re.search(r'(\d+)%', raw_text)
                
                browser.close()
                
                if match:
                    return float(match.group(1)), "🟢 OCR 影像辨識成功"
                else:
                    # 如果沒抓到百分比，回傳原始文字供除錯
                    return None, f"🟡 抓到文字但格式不符: {raw_text[:20]}"
            
            browser.close()
            return None, "❌ 無法定位網頁內容"

    except Exception as e:
        return None, f"🔴 系統超時或崩潰: {str(e)[:50]}"

# --- Streamlit 介面 ---
st.title("🍕 Pentagon Pizza Index 戰情室")
st.markdown("本系統採用 **Playwright 截圖 + Tesseract OCR** 技術進行自動化觀測。")

# 側邊欄備援輸入 (以防自動化失敗)
st.sidebar.header("🛠️ 備援操作")
manual_val = st.sidebar.number_input("手動修正數值", 0, 100, 30)

if st.button("📡 啟動即時影像偵查"):
    with st.spinner("瀏覽器執行中，請稍候..."):
        val, msg = get_pizza_by_ocr()
        
        if val is not None:
            st.session_state['pizza_val'] = val
            st.success(msg)
        else:
            st.error(msg)
            st.warning("自動抓取失敗，目前顯示側邊欄的手動數值。")
            st.session_state['pizza_val'] = manual_val

# 顯示結果
current_val = st.session_state.get('pizza_val', manual_val)
st.metric("當前五角大廈訂單壓力值", f"{current_val}%")

if current_val >= 80:
    st.error("🚨 警告：偵測到訂單異常激增，可能存在軍事行動預兆！")

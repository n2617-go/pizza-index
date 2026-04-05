import streamlit as st
import pytesseract
from PIL import Image
from playwright.sync_api import sync_playwright
import io
import os
import re

# --- 配置設定 ---
# 若要在本機執行，請安裝 tesseract 並設定路徑
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

st.set_page_config(page_title="Pentagon Pizza OCR", page_icon="🍕")

def get_pizza_by_ocr():
    try:
        with sync_playwright() as p:
            # 啟動輕量化瀏覽器
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
            page = browser.new_page()
            
            # 前往網頁
            page.goto("https://worldmonitor.app/", wait_until="networkidle", timeout=45000)
            
            # 定位數字區域 (假設該元素 ID 為 .pizza-index 或類似結構)
            # 在這裡請用 F12 找到正確的 selector
            element = page.query_selector("div.pizza-index") 
            
            if element:
                # 截圖並轉為 PIL 圖片
                screenshot = element.screenshot()
                img = Image.open(io.BytesIO(screenshot))
                
                # 影像增強處理 (轉灰階以提升 OCR 準確度)
                img = img.convert('L')
                
                # OCR 辨識
                text = pytesseract.image_to_string(img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
                
                browser.close()
                return text.strip(), "✅ 辨識成功"
            
            browser.close()
            return None, "❌ 找不到目標區域"
            
    except Exception as e:
        return None, f"⚠️ 系統錯誤: {str(e)[:30]}"

st.title("🍕 披薩指數影像辨識器")

if st.button("開始掃描影像"):
    with st.spinner("正在進行 OCR 辨識..."):
        val, status = get_pizza_by_ocr()
        if val:
            st.success(f"辨識結果：{val}%")
            st.metric("當前披薩指數", f"{val}%")
        else:
            st.error(status)

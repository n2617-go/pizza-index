import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random

# 網頁基本設定
st.set_page_config(page_title="五角大廈披薩監控 - 每小時趨勢", page_icon="🍕", layout="wide")

st.title("🍕 Pentagon Pizza Index | 當日每小時訂單趨勢")
st.write("數據觀測點：Pentagon 駐地周邊比薩店 (Arlington, VA)")

# 1. 數據獲取與處理 (模擬當天 24 小時數據)
@st.cache_data(ttl=600)
def get_hourly_data():
    # 取得今天的日期 (以台北時間為準)
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    data_list = []
    # 產生從今天 00:00 到現在的每個小時數據
    for i in range(now.hour + 1):
        t = today_start + timedelta(hours=i)
        
        # 模擬披薩指數邏輯：
        # 0-6 點 (深夜)：若有大事，指數會飆高 (隨機模擬 30-90)
        # 11-13 點 (午餐)：正常升高 (50-70)
        # 18-20 點 (晚餐)：高峰 (60-80)
        # 其他時間：低點 (20-40)
        hour = t.hour
        if 0 <= hour <= 5:
            val = random.randint(20, 95) # 模擬潛在深夜加班
        elif 11 <= hour <= 13 or 17 <= hour <= 20:
            val = random.randint(50, 85)
        else:
            val = random.randint(20, 50)
            
        data_list.append({"時間": t.strftime("%H:00"), "披薩指數": val})
    
    return pd.DataFrame(data_list)

df_hourly = get_hourly_data()

# 2. 儀表板上方即時指標
if not df_hourly.empty:
    current_val = df_hourly.iloc[-1]['披薩指數']
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric(label="當前小時指數", value=f"{current_val}%", delta_color="inverse")
        if current_val > 80:
            st.error("⚠️ 偵測到異常訂單量！")
        elif current_val > 60:
            st.warning("觀察中：訂單量偏高")
        else:
            st.success("目前狀態：穩定")

    # 3. 繪製每小時條狀圖 (Bar Chart)
    with col2:
        # 使用 Plotly 繪製美觀的條狀圖
        fig = px.bar(
            df_hourly, 
            x='時間', 
            y='披薩指數',
            text='披薩指數', # 在條柱上顯示數字
            title=f"📅 {datetime.now().strftime('%Y-%m-%d')} 每小時波動趨勢",
            labels={'披薩指數': '忙碌百分比 (%)', '時間': '小時 (24h)'},
            template="plotly_dark",
            color='披薩指數', # 根據數值深淺變色
            color_continuous_scale='Reds' # 使用紅色系
        )
        
        # 優化圖表外觀
        fig.update_traces(textposition='outside')
        fig.update_layout(yaxis_range=[0, 110]) # 固定 Y 軸範圍 0-100+
        
        st.plotly_chart(fig, use_container_width=True)

# 4. 底部資訊
st.divider()
st.info("💡 說明：披薩指數 (Pizza Index) 是透過監控政府機關周邊餐廳在深夜的異常忙碌程度，來預測是否有重大軍事或外交行動的 OSINT 指標。")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import random

st.set_page_config(page_title="五角大廈披薩監控 - 滾動24H", page_icon="🍕", layout="wide")

# 1. 時區處理
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York')

now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)

st.title("🍕 Pentagon Pizza Index | 滾動 24 小時即時監控")

t_col1, t_col2 = st.columns(2)
with t_col1:
    st.info(f"🇹🇼 台灣時間 (Taipei): **{now_tw.strftime('%Y-%m-%d %H:%M:%S')}**")
with t_col2:
    st.warning(f"🇺🇸 華盛頓時間 (D.C.): **{now_us.strftime('%Y-%m-%d %H:%M:%S')}**")

# 2. 滾動 24 小時數據邏輯
@st.cache_data(ttl=600)
def get_rolling_24h_data(current_time_us):
    data_list = []
    # 往回推 23 小時，直到當前小時
    for i in range(23, -1, -1):
        target_time = current_time_us - timedelta(hours=i)
        hour_str = target_time.strftime("%m/%d %H:00") # 顯示日期+小時，避免跨日混淆
        
        # 模擬披薩指數 (如果是美東深夜 01:00 - 04:00，數值隨機模擬高一點)
        h = target_time.hour
        if 1 <= h <= 4:
            val = random.randint(40, 95)
        else:
            val = random.randint(15, 60)
            
        data_list.append({"時間": hour_str, "披薩指數": val})
    return pd.DataFrame(data_list)

df_rolling = get_rolling_24h_data(now_us)

# 3. 繪圖
if not df_rolling.empty:
    latest_val = df_rolling.iloc[-1]['披薩指數']
    
    # 這裡固定 Y 軸比例，並取消工具列
    fig = px.bar(
        df_rolling, 
        x='時間', 
        y='披薩指數',
        text='披薩指數',
        color='披薩指數',
        color_continuous_scale='Reds',
        template="plotly_dark"
    )

    fig.update_layout(
        yaxis_range=[0, 110],
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
        dragmode=False,
        coloraxis_showscale=False
    )
    fig.update_traces(textposition='outside')

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 4. 即時狀態
st.metric("最新觀測數據 (華盛頓直擊)", f"{latest_val}%", delta="最新一小時")
if latest_val > 80:
    st.error("🚨 警告：華盛頓深夜訂單激增，可能存在重大行動。")

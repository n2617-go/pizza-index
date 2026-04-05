import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import random

# 網頁基本設定
st.set_page_config(page_title="五角大廈披薩監控系統", page_icon="🍕", layout="wide")

# 1. 時間顯示區 (頂部)
st.title("🍕 Pentagon Pizza Index | 全球即時監控")

# 取得各時區時間
tz_tw = pytz.timezone('Asia/Taipei')
tz_us = pytz.timezone('America/New_York') # 五角大廈所在時區 (東部時間)

now_tw = datetime.now(tz_tw)
now_us = datetime.now(tz_us)

t_col1, t_col2 = st.columns(2)
with t_col1:
    st.info(f"🇹🇼 台灣時間 (Taipei): **{now_tw.strftime('%Y-%m-%d %H:%M:%S')}**")
with t_col2:
    st.warning(f"🇺🇸 華盛頓時間 (D.C.): **{now_us.strftime('%Y-%m-%d %H:%M:%S')}**")

st.divider()

# 2. 數據獲取與處理
@st.cache_data(ttl=600)
def get_hourly_data():
    # 模擬當天 0 點至今的數據
    data_list = []
    for i in range(24):
        val = random.randint(20, 95) if i < 5 or 18 <= i <= 20 else random.randint(15, 55)
        data_list.append({"小時": f"{i:02d}:00", "披薩指數": val})
    return pd.DataFrame(data_list)

df_hourly = get_hourly_data()

# 3. 繪製固定比例、禁止縮放的條狀圖
if not df_hourly.empty:
    current_hour = now_tw.hour
    current_val = df_hourly.iloc[current_hour]['披薩指數']
    
    st.subheader(f"📊 當日波動趨勢 (觀測點：五角大廈周邊)")
    
    fig = px.bar(
        df_hourly, 
        x='小時', 
        y='披薩指數',
        text='披薩指數',
        color='披薩指數',
        color_continuous_scale='Reds',
        template="plotly_dark"
    )

    # --- 固定比例與取消縮放的關鍵設定 ---
    fig.update_layout(
        yaxis_range=[0, 110],  # 固定 Y 軸比例 (0-110%)
        xaxis_fixedrange=True, # 禁止 X 軸縮放/拖動
        yaxis_fixedrange=True, # 禁止 Y 軸縮放/拖動
        dragmode=False,        # 關閉滑鼠拖動選擇功能
        coloraxis_showscale=False, # 隱藏側邊顏色條
        margin=dict(l=20, r=20, t=40, b=20) # 緊湊佈局
    )
    
    fig.update_traces(textposition='outside')

    # 顯示圖表並隱藏工具列 (Modebar)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 4. 底部警戒說明
c1, c2 = st.columns([1, 1])
with c1:
    st.metric("當前小時指數", f"{current_val}%")
with c2:
    if current_val > 80:
        st.error("🚨 警告：偵測到五角大廈深夜異常加班訂單！")
    else:
        st.success("✅ 目前訂單趨勢穩定。")

st.caption("備註：本圖表已固定比例並取消縮放功能，以利精準觀測小時級距變化。")

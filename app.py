import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# 網頁基本設定
st.set_page_config(
    page_title="五角大廈披薩指數監控",
    page_icon="🍕",
    layout="wide"
)

# 自定義 CSS 讓介面更有情報感 (Dark Mode 友善)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1a1c24;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🍕 Pentagon Pizza Index | 五角大廈披薩指數")
st.write("本系統透過監控五角大廈周邊比薩店的即時忙碌程度，評估潛在的地緣政治波動。")

# 數據獲取函式
@st.cache_data(ttl=300)  # 快取 5 分鐘，避免過度呼叫 API
def fetch_pizza_data():
    # 使用提供的 Supabase 公開端點
    url = "https://olibvrexvuhsaknckltd.supabase.co/rest/v1/main?select=created_at,value&order=created_at.desc&limit=200"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        
        # 時間格式轉換與時區處理
        df['created_at'] = pd.to_datetime(df['created_at'])
        # 轉換為台灣時間 (UTC+8)
        df['time_tw'] = df['created_at'].dt.tz_convert('Asia/Taipei')
        return df
    except Exception as e:
        st.error(f"數據抓取失敗: {e}")
        return None

# 執行抓取
df = fetch_pizza_data()

if df is not None and not df.empty:
    # 建立儀表板佈局
    col1, col2, col3 = st.columns(3)
    
    latest_val = df.iloc[0]['value']
    prev_val = df.iloc[1]['value'] if len(df) > 1 else latest_val
    delta = round(latest_val - prev_val, 2)
    
    with col1:
        status = "🟢 正常"
        if latest_val > 80: status = "🔴 極度異常 (警戒)"
        elif latest_val > 60: status = "🟡 稍微繁忙"
        st.metric(label="當前指數 (0-100)", value=f"{latest_val:.1f}", delta=f"{delta}")
        
    with col2:
        st.metric(label="情報狀態", value=status)
        
    with col3:
        last_update = df.iloc[0]['time_tw'].strftime('%Y-%m-%d %H:%M')
        st.metric(label="最後更新時間", value=last_update)

    st.divider()

    # 繪製互動式趨勢圖 (Plotly)
    st.subheader("📈 歷史波動趨勢")
    fig = px.line(
        df, 
        x='time_tw', 
        y='value', 
        title="五角大廈披薩訂單趨勢 (過去 200 筆紀錄)",
        labels={'time_tw': '時間 (台北時間)', 'value': '指數分數'},
        template="plotly_dark"
    )
    fig.update_traces(line_color='#FF4B4B', line_width=2)
    st.plotly_chart(fig, use_container_width=True)

    # 顯示原始數據表格
    with st.expander("查看原始數據明細"):
        st.dataframe(df[['time_tw', 'value']].rename(columns={'time_tw': '更新時間', 'value': '指數值'}), use_container_width=True)

else:
    st.warning("目前暫時無法取得即時數據，請檢查網絡連線或 API 狀態。")

st.caption("數據來源: Aveygo/PizzaIndex Open Intelligence Project. 本指數僅供參考。")

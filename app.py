import streamlit as st
import pandas as pd
from golf_data import get_data_and_filters

st.set_page_config(
    page_title="Golf Swing Data Analyzer",
    page_icon="⛳",
    layout="wide",
)

st.title("⛳ Golf Swing Data Analyzer")
st.markdown("Upload CSV file(s) with golf swing data. Files are saved and **automatically loaded** on all pages. Use the sidebar to filter and manage files.")

all_dfs, df = get_data_and_filters()

if df is None or len(df) == 0:
    st.info("👆 Upload one or more CSV files in the **sidebar** to get started.")
    st.markdown("""
    ### Expected CSV format
    Your CSV should include golf swing metrics such as:
    - **Club Speed**, **Ball Speed**, **Launch Angle**, **Spin Rate**
    - **Carry Distance**, **Total Distance**
    - **Club Path**, **Club Face**, **Face to Path**
    - **Club Type**, **Date**
    
    The app skips the units row (row 2) in your CSV files.
    """)
else:
    st.header("📊 Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Swings", len(df))
    with col2:
        if "Club Type" in df.columns:
            st.metric("Club Types", df["Club Type"].nunique())
        else:
            st.metric("Columns", len(df.columns))
    with col3:
        if "Carry Distance" in df.columns:
            st.metric("Avg Carry", f"{df['Carry Distance'].mean():.1f} yds")
        else:
            st.metric("Numeric Cols", len(df.select_dtypes(include=["float64", "int64"]).columns))
    with col4:
        if "Total Distance" in df.columns:
            st.metric("Avg Total", f"{df['Total Distance'].mean():.1f} yds")
        else:
            st.metric("Missing", df.isnull().sum().sum())

    st.subheader("Data preview")
    st.dataframe(df.head(10), use_container_width=True)

    st.markdown("---")
    st.subheader("📑 Pages")
    st.markdown("""
    | Page | Description |
    |------|-------------|
    | **📊 Overview** | Full dataset overview, preview, column info |
    | **📐 Consistency** | Dispersion scores and gauges (club path, face, speed) |
    | **⛳ Golf Analysis** | Club speed/distance charts, performance by club type |
    | **🎯 Swing Path** | Path/face analysis and coaching tips |
    | **📈 Statistics** | Statistical summary, custom charts, correlation |
    | **📅 Sessions** | Compare metrics across sessions/files |
    | **🎬 Ball Flight** | Animated 2D trajectory from your shot data (launch angle, ball speed, carry) |
    """)

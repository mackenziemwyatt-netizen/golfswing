import streamlit as st
import pandas as pd
from golf_data import get_data_and_filters, render_session_banner

all_dfs, df = get_data_and_filters()
render_session_banner()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see the overview.")
    st.stop()

st.header("📊 Dataset Overview")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Swings", len(df))
with col2:
    if "Club Type" in df.columns:
        st.metric("Club Types", df["Club Type"].nunique())
    else:
        st.metric("Total Columns", len(df.columns))
with col3:
    if "Carry Distance" in df.columns:
        st.metric("Avg Carry Distance", f"{df['Carry Distance'].mean():.1f} yds")
    else:
        st.metric("Numeric Columns", len(df.select_dtypes(include=["float64", "int64"]).columns))
with col4:
    if "Total Distance" in df.columns:
        st.metric("Avg Total Distance", f"{df['Total Distance'].mean():.1f} yds")
    else:
        st.metric("Missing Values", df.isnull().sum().sum())

st.subheader("Preview Data")
st.dataframe(df.head(10), use_container_width=True)

st.header("📋 Column Information")
col_info = pd.DataFrame({
    "Column Name": df.columns,
    "Data Type": df.dtypes.astype(str),
    "Non-Null Count": df.count().values,
    "Null Count": df.isnull().sum().values,
})
st.dataframe(col_info, use_container_width=True, hide_index=True)

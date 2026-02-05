import streamlit as st
import pandas as pd
import plotly.express as px
from golf_data import get_data_and_filters

all_dfs, df = get_data_and_filters()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see statistics.")
    st.stop()

numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
if not numeric_cols:
    st.warning("No numeric columns in this dataset.")
    st.stop()

st.header("📈 Statistical Summary")
st.subheader("Numeric Column Statistics")
st.dataframe(df[numeric_cols].describe(), use_container_width=True)

st.header("📊 Custom Visualizations")
col1, col2 = st.columns(2)
with col1:
    selected_col = st.selectbox("Select a column for analysis", numeric_cols, help="Choose a numeric column to visualize")
with col2:
    chart_type = st.selectbox("Select chart type", ["Histogram", "Box Plot", "Line Chart", "Scatter Plot"], help="Choose the type of visualization")

if selected_col:
    if chart_type == "Histogram":
        fig = px.histogram(df, x=selected_col, nbins=30, title=f"Distribution of {selected_col}", labels={selected_col: selected_col})
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Box Plot":
        fig = px.box(df, y=selected_col, title=f"Box Plot of {selected_col}", labels={selected_col: selected_col})
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Line Chart":
        fig = px.line(df, y=selected_col, title=f"Line Chart of {selected_col}", labels={selected_col: selected_col, "index": "Record Number"})
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Scatter Plot":
        if len(numeric_cols) > 1:
            x_col = st.selectbox("Select X-axis column", [c for c in numeric_cols if c != selected_col], key="scatter_x")
            fig = px.scatter(df, x=x_col, y=selected_col, title=f"Scatter Plot: {x_col} vs {selected_col}", labels={x_col: x_col, selected_col: selected_col})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Need at least 2 numeric columns for scatter plot.")

if len(numeric_cols) > 1:
    st.subheader("Correlation Matrix")
    corr_matrix = df[numeric_cols].corr()
    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", title="Correlation Between Numeric Variables", color_continuous_scale="RdBu")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Detailed Statistics")
for col in numeric_cols:
    with st.expander(f"Statistics for {col}"):
        col_stats = {
            "Mean": df[col].mean(),
            "Median": df[col].median(),
            "Standard Deviation": df[col].std(),
            "Min": df[col].min(),
            "Max": df[col].max(),
            "25th Percentile": df[col].quantile(0.25),
            "75th Percentile": df[col].quantile(0.75),
            "Skewness": df[col].skew(),
            "Kurtosis": df[col].kurtosis(),
        }
        stats_display = pd.DataFrame([col_stats]).T
        stats_display.columns = ["Value"]
        st.dataframe(stats_display, use_container_width=True, hide_index=True)

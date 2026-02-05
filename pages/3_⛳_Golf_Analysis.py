import streamlit as st
import pandas as pd
import plotly.express as px
from golf_data import get_data_and_filters

all_dfs, df = get_data_and_filters()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see golf analysis.")
    st.stop()

st.header("⛳ Golf-Specific Analysis")

numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
if not numeric_cols:
    st.warning("No numeric columns in this dataset.")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    if "Club Speed" in df.columns and "Carry Distance" in df.columns:
        fig = px.scatter(
            df,
            x="Club Speed",
            y="Carry Distance",
            color="Club Type" if "Club Type" in df.columns else None,
            title="Club Speed vs Carry Distance",
            labels={"Club Speed": "Club Speed (mph)", "Carry Distance": "Carry Distance (yards)"},
            hover_data=["Ball Speed"] if "Ball Speed" in df.columns else None,
        )
        st.plotly_chart(fig, use_container_width=True)
    if "Launch Angle" in df.columns and "Total Distance" in df.columns:
        fig = px.scatter(
            df,
            x="Launch Angle",
            y="Total Distance",
            color="Club Type" if "Club Type" in df.columns else None,
            title="Launch Angle vs Total Distance",
            labels={"Launch Angle": "Launch Angle (degrees)", "Total Distance": "Total Distance (yards)"},
            hover_data=["Ball Speed"] if "Ball Speed" in df.columns else None,
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "Ball Speed" in df.columns and "Carry Distance" in df.columns:
        fig = px.scatter(
            df,
            x="Ball Speed",
            y="Carry Distance",
            color="Club Type" if "Club Type" in df.columns else None,
            title="Ball Speed vs Carry Distance",
            labels={"Ball Speed": "Ball Speed (mph)", "Carry Distance": "Carry Distance (yards)"},
            hover_data=["Smash Factor"] if "Smash Factor" in df.columns else None,
        )
        st.plotly_chart(fig, use_container_width=True)
    if "Spin Rate" in df.columns and "Total Distance" in df.columns:
        fig = px.scatter(
            df,
            x="Spin Rate",
            y="Total Distance",
            color="Club Type" if "Club Type" in df.columns else None,
            title="Spin Rate vs Total Distance",
            labels={"Spin Rate": "Spin Rate (rpm)", "Total Distance": "Total Distance (yards)"},
            hover_data=["Launch Angle"] if "Launch Angle" in df.columns else None,
        )
        st.plotly_chart(fig, use_container_width=True)

if "Club Type" in df.columns:
    st.subheader("Performance by Club Type")
    club_metrics = ["Carry Distance", "Total Distance", "Club Speed", "Ball Speed"]
    available_metrics = [m for m in club_metrics if m in df.columns]
    if available_metrics:
        metric = st.selectbox("Select Metric", available_metrics, key="club_metric")
        club_stats = df.groupby("Club Type")[metric].agg(["mean", "std", "count"]).reset_index()
        club_stats.columns = ["Club Type", "Mean", "Std Dev", "Count"]
        fig = px.bar(
            club_stats,
            x="Club Type",
            y="Mean",
            error_y="Std Dev",
            title=f"Average {metric} by Club Type",
            labels={"Mean": f"Average {metric}", "Club Type": "Club Type"},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(club_stats, use_container_width=True, hide_index=True)

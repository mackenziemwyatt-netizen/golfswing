import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from golf_data import get_data_and_filters, render_session_banner

all_dfs, df = get_data_and_filters()
render_session_banner()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see session comparison.")
    st.stop()

if len(all_dfs) <= 1 or "Source File" not in df.columns:
    st.info("Upload **multiple** CSV files (or have multiple saved files) to compare sessions.")
    st.stop()

st.header("📅 Session Comparison")
agg_dict = {}
for metric in ["Carry Distance", "Total Distance", "Club Speed", "Ball Speed", "Smash Factor"]:
    if metric in df.columns:
        agg_dict[metric] = "mean"
if not agg_dict:
    st.warning("No session metrics available in this dataset.")
    st.stop()

session_stats = df.groupby("Source File").agg(agg_dict).reset_index()
st.subheader("Average Metrics by Session")
st.dataframe(session_stats, use_container_width=True, hide_index=True)

if len(session_stats) > 1:
    metrics_to_plot = [c for c in session_stats.columns if c != "Source File"]
    if metrics_to_plot:
        fig = go.Figure()
        for metric in metrics_to_plot[:4]:
            fig.add_trace(
                go.Scatter(
                    x=session_stats["Source File"],
                    y=session_stats[metric],
                    mode="lines+markers",
                    name=metric,
                )
            )
        fig.update_layout(title="Session Comparison", xaxis_title="Session", yaxis_title="Value", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

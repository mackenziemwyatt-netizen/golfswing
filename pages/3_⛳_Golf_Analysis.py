import streamlit as st
import pandas as pd
import plotly.express as px
from golf_data import get_data_and_filters, render_session_banner
from pga_tour_data import (
    PGA_TABLE_CSS,
    build_comparison_by_club,
    build_pga_comparison_table_html,
    build_pga_reference_only_html,
    gap_analysis_ordered,
    PGA_METRIC_COLUMNS,
)

all_dfs, df = get_data_and_filters()
render_session_banner()
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

# PGA Tour averages comparison (orange/white TrackMan-style)
st.markdown("---")
st.subheader("🏆 PGA Tour Averages Comparison")
st.caption("TrackMan PGA Tour averages (yards). **Green** = within 10% of tour · **Yellow** = 10–25% off · **Red** = >25% off.")
st.markdown(PGA_TABLE_CSS, unsafe_allow_html=True)
if "Club Type" in df.columns:
    pga_metrics_in_df = [m[1] for m in PGA_METRIC_COLUMNS if m[1] in df.columns]
    if pga_metrics_in_df:
        comparison_list = build_comparison_by_club(df)
        metrics_to_show = [m[0] for m in PGA_METRIC_COLUMNS if m[1] in df.columns]
        if comparison_list and metrics_to_show:
            st.markdown("**My stats vs PGA Tour (by club)**")
            st.markdown(build_pga_comparison_table_html(comparison_list, metrics_to_show), unsafe_allow_html=True)
            closest, need_work = gap_analysis_ordered(comparison_list)
            st.markdown("**Gap analysis**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("*Closest to tour level*")
                for c in closest:
                    st.markdown(f'<span class="pga-gap-box pga-gap-closest">{c["club_type"]} (avg {c["avg_gap_pct"]:.1f}% off)</span>', unsafe_allow_html=True)
            with col_b:
                st.markdown("*Need the most work*")
                for c in need_work:
                    st.markdown(f'<span class="pga-gap-box pga-gap-work">{c["club_type"]} (avg {c["avg_gap_pct"]:.1f}% off)</span>', unsafe_allow_html=True)
st.markdown("**PGA Tour reference (TrackMan averages)**")
st.markdown(build_pga_reference_only_html(), unsafe_allow_html=True)

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

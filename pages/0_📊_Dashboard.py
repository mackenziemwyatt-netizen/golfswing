"""
TrackMan-style Dashboard: key metrics in large cards with shot selector.
"""
import streamlit as st
import pandas as pd
from golf_data import get_data_and_filters, render_session_banner
from pga_tour_data import (
    PGA_TABLE_CSS,
    build_comparison_by_club,
    build_pga_comparison_table_html,
    gap_analysis_ordered,
    PGA_METRIC_COLUMNS,
)

# Metric config: (display label, column name, unit, icon/indicator)
DASHBOARD_METRICS = [
    ("Club Speed", "Club Speed", "mph", "🏌️"),
    ("Ball Speed", "Ball Speed", "mph", "⚡"),
    ("Launch Angle", "Launch Angle", "°", "📐"),
    ("Spin Rate", "Spin Rate", "rpm", "🌀"),
    ("Carry Distance", "Carry Distance", "yds", "📏"),
    ("Total Distance", "Total Distance", "yds", "📏"),
    ("Club Path", "Club Path", "°", "↗️"),
    ("Face Angle", "Club Face", "°", "🎯"),
    ("Attack Angle", "Attack Angle", "°", "📉"),
    ("Smash Factor", "Smash Factor", "", "💥"),
]

# TrackMan-style card CSS: clean, professional, data-focused
DASHBOARD_CSS = """
<style>
.dashboard-card {
    background: linear-gradient(145deg, #f8f9fa 0%, #ffffff 100%);
    border: 1px solid #e0e4e8;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    min-height: 100px;
}
.dashboard-card .metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #5c6370;
    margin-bottom: 0.25rem;
}
.dashboard-card .metric-value {
    font-size: 2.4rem;
    font-weight: 700;
    color: #1a1d21;
    line-height: 1.2;
    letter-spacing: -0.02em;
}
.dashboard-card .metric-unit {
    font-size: 0.8rem;
    color: #6b7280;
    margin-top: 0.15rem;
}
.dashboard-card .metric-icon {
    font-size: 1.1rem;
    opacity: 0.85;
}
</style>
"""


def _format_value(val):
    """Format numeric value for display; handle NaN."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    if isinstance(val, (int, float)):
        if abs(val) >= 1000:
            return f"{val:,.0f}"
        if abs(val) >= 1 or val == 0:
            return f"{val:.1f}"
        return f"{val:.2f}"
    return str(val)


def _shot_label(row, idx, df):
    """Build a short label for a shot (e.g. Shot 3 — Pitching Wedge — 2/4/26 3:07 PM)."""
    parts = [f"Shot {idx + 1}"]
    if "Club Type" in df.columns and pd.notna(row.get("Club Type")):
        parts.append(str(row["Club Type"]))
    if "Date" in df.columns and pd.notna(row.get("Date")):
        try:
            dt = pd.to_datetime(row["Date"])
            parts.append(dt.strftime("%m/%d/%y %I:%M %p") if hasattr(dt, "strftime") else str(dt)[:16])
        except Exception:
            pass
    return " — ".join(parts)


def render_metric_card(label, value_str, unit, icon):
    """Render one TrackMan-style metric card as HTML."""
    unit_html = f'<div class="metric-unit">{unit}</div>' if unit else ""
    st.markdown(
        f'<div class="dashboard-card">'
        f'<div class="metric-label"><span class="metric-icon">{icon}</span> {label}</div>'
        f'<div class="metric-value">{value_str}</div>'
        f'{unit_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


all_dfs, df = get_data_and_filters()
render_session_banner()

if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see the dashboard.")
    st.stop()

st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
st.header("📊 Launch Monitor Dashboard")
st.caption("TrackMan-style view of your key swing and ball flight metrics. Select *Session average* or a specific shot below.")

# Shot selector: Session average or individual shots
view_options = ["Session average"]
for i in range(len(df)):
    view_options.append(_shot_label(df.iloc[i], i, df))
selected_view = st.selectbox(
    "View",
    range(len(view_options)),
    format_func=lambda i: view_options[i],
    key="dashboard_shot_select",
    help="Show session averages or a single shot's metrics.",
)

if selected_view == 0:
    metric_cols = [m[1] for m in DASHBOARD_METRICS if m[1] in df.columns]
    row = df[metric_cols].mean().to_dict() if metric_cols else {}
    subtitle = "Averages across all selected data"
else:
    row = df.iloc[selected_view - 1].to_dict()
    subtitle = view_options[selected_view]

st.caption(subtitle)
st.markdown("---")

# Build list of (label, col, unit, icon) for metrics that exist in data
available = [(label, col, unit, icon) for label, col, unit, icon in DASHBOARD_METRICS if col in df.columns]
if not available:
    st.warning("No dashboard metrics found in this dataset. Expected columns: Club Speed, Ball Speed, Launch Angle, etc.")
    st.stop()

# Grid: 4 cards per row
for start in range(0, len(available), 4):
    chunk = available[start : start + 4]
    cols = st.columns(4)
    for i, (label, col, unit, icon) in enumerate(chunk):
        val = row.get(col)
        value_str = _format_value(val)
        with cols[i]:
            render_metric_card(label, value_str, unit, icon)

st.markdown("---")
st.caption("Units: mph = miles per hour, ° = degrees, rpm = revolutions per minute, yds = yards. Smash Factor is dimensionless.")

if selected_view == 0 and len(df) > 1:
    st.caption(f"*Session average computed from {len(df)} shots.*")

# PGA Tour comparison (session average only, when Club Type and PGA metrics exist)
if selected_view == 0 and "Club Type" in df.columns:
    pga_metrics_in_df = [m[1] for m in PGA_METRIC_COLUMNS if m[1] in df.columns]
    if pga_metrics_in_df:
        st.markdown("---")
        st.subheader("🏆 My Stats vs PGA Tour Averages")
        st.caption("TrackMan PGA Tour averages. **Green** = within 10% of tour · **Yellow** = 10–25% off · **Red** = >25% off.")
        st.markdown(PGA_TABLE_CSS, unsafe_allow_html=True)
        comparison_list = build_comparison_by_club(df)
        metrics_to_show = [m[0] for m in PGA_METRIC_COLUMNS if m[1] in df.columns]
        if comparison_list and metrics_to_show:
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
        else:
            st.caption("No club-type breakdown available for PGA comparison.")

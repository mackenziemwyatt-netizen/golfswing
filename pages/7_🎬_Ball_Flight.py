"""
Ball flight visualization: 2D side-view trajectory from impact to landing.
Uses launch angle, ball speed, carry distance (and optional spin) for physics-based arc.
"""
import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from golf_data import get_data_and_filters, render_session_banner

# Constants
G = 9.81  # m/s^2
MPH_TO_MPS = 0.44704
M_TO_YD = 1.09361


def trajectory_2d(launch_angle_deg, ball_speed_mph, carry_distance_yd, spin_rate_rpm=None, n_points=80):
    """
    Compute 2D trajectory (side view) from impact to landing.
    Uses projectile motion; scales horizontal axis so landing = carry_distance_yd.
    Returns (x_yd, y_yd, t_arr) arrays in yards and seconds.
    """
    theta = np.radians(launch_angle_deg)
    v0 = ball_speed_mph * MPH_TO_MPS  # m/s

    # Time of flight (no air resistance)
    t_flight = 2 * v0 * np.sin(theta) / G
    if t_flight <= 0:
        t_flight = 1.0

    # Range in meters, then yards
    range_m = (v0 ** 2) * np.sin(2 * theta) / G
    range_yd = range_m * M_TO_YD
    if range_yd <= 0:
        range_yd = carry_distance_yd

    # Scale so landing = actual carry distance (accounts for air resistance / spin in real shot)
    scale = carry_distance_yd / range_yd if range_yd else 1.0

    # Optional: spin extends hang time slightly (simple lift effect)
    if spin_rate_rpm is not None and not np.isnan(spin_rate_rpm) and spin_rate_rpm > 0:
        spin_factor = 1 + 0.08 * min(spin_rate_rpm / 5000, 1.5)
        t_flight *= spin_factor

    t_arr = np.linspace(0, t_flight, n_points)
    x_m = v0 * np.cos(theta) * t_arr
    y_m = v0 * np.sin(theta) * t_arr - 0.5 * G * t_arr ** 2
    y_m = np.maximum(y_m, 0)  # ground level

    x_yd = x_m * M_TO_YD * scale
    y_yd = y_m * M_TO_YD

    return x_yd, y_yd, t_arr


all_dfs, df = get_data_and_filters()
render_session_banner()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see ball flight.")
    st.stop()

required = ["Launch Angle", "Ball Speed", "Carry Distance"]
if not all(c in df.columns for c in required):
    st.warning("Dataset must contain Launch Angle, Ball Speed, and Carry Distance for ball flight.")
    st.stop()

# Rows with valid trajectory data
opt_cols = [c for c in ["Launch Direction", "Spin Rate", "Club Type", "Date", "Total Distance"] if c in df.columns]
flight_df = df[required + opt_cols].copy()
flight_df = flight_df.dropna(subset=required)
flight_df = flight_df[
    (flight_df["Ball Speed"] > 0) & (flight_df["Carry Distance"] > 0) & (flight_df["Launch Angle"].between(-90, 90))
]

if len(flight_df) == 0:
    st.warning("No shots with valid launch angle, ball speed, and carry distance.")
    st.stop()

# Build shot labels for selector
def shot_label(row, i):
    parts = [f"Shot {i+1}"]
    if "Date" in row.index and pd.notna(row.get("Date")):
        try:
            d = row["Date"]
            parts.append(str(d)[:16] if hasattr(d, "__str__") else str(d))
        except Exception:
            pass
    if "Club Type" in row.index and pd.notna(row.get("Club Type")):
        parts.append(str(row["Club Type"]))
    carry = row["Carry Distance"]
    parts.append(f"{carry:.0f} yds carry")
    return " · ".join(parts)

options = list(range(len(flight_df)))
labels = [shot_label(flight_df.iloc[i], i) for i in options]

st.header("🎬 Ball Flight Visualization")
st.markdown("2D side view of the ball trajectory from impact to landing using **launch angle**, **ball speed**, **carry distance**, and **spin rate**.")

selected_idx = st.selectbox("Select a shot to animate", options, format_func=lambda i: labels[i], key="ballflight_shot")
row = flight_df.iloc[selected_idx]

launch_angle = float(row["Launch Angle"])
ball_speed = float(row["Ball Speed"])
carry_distance = float(row["Carry Distance"])
spin_rate = float(row["Spin Rate"]) if "Spin Rate" in row.index and pd.notna(row.get("Spin Rate")) else None

# Compute trajectory first (needed for apex and plot)
x_yd, y_yd, t_arr = trajectory_2d(launch_angle, ball_speed, carry_distance, spin_rate, n_points=80)
apex_yd = float(np.max(y_yd))

# Shot summary
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Launch Angle", f"{launch_angle:.1f}°")
with c2:
    st.metric("Ball Speed", f"{ball_speed:.1f} mph")
with c3:
    st.metric("Carry Distance", f"{carry_distance:.1f} yd")
with c4:
    st.metric("Spin Rate", f"{spin_rate:.0f} rpm" if spin_rate is not None else "—")
with c5:
    if "Launch Direction" in row.index and pd.notna(row.get("Launch Direction")):
        st.metric("Launch Dir", f"{float(row['Launch Direction']):.1f}°")
    elif "Total Distance" in row.index and pd.notna(row.get("Total Distance")):
        st.metric("Total Distance", f"{float(row['Total Distance']):.1f} yd")
    else:
        st.metric("Apex (est.)", f"{apex_yd:.1f} yd")

# Build animated figure: full trajectory line + moving ball
n_frames = len(x_yd)
fig = go.Figure()

# Full trajectory line (gray)
fig.add_trace(
    go.Scatter(
        x=x_yd,
        y=y_yd,
        mode="lines",
        name="Trajectory",
        line=dict(color="rgba(100,100,100,0.6)", width=2),
    )
)

# Ball marker (starts at origin; will move in frames)
fig.add_trace(
    go.Scatter(
        x=[x_yd[0]],
        y=[y_yd[0]],
        mode="markers",
        name="Ball",
        marker=dict(symbol="circle", size=14, color="orange", line=dict(color="darkorange", width=2)),
    )
)

# Frames for animation
frames = []
for k in range(n_frames):
    frames.append(
        go.Frame(
            data=[
                go.Scatter(x=x_yd, y=y_yd, mode="lines", line=dict(color="rgba(100,100,100,0.6)", width=2)),
                go.Scatter(
                    x=[x_yd[k]],
                    y=[y_yd[k]],
                    mode="markers",
                    marker=dict(symbol="circle", size=14, color="orange", line=dict(color="darkorange", width=2)),
                ),
            ],
            name=str(k),
        )
    )

fig.frames = frames

# Slider and play button
fig.update_layout(
    title="Ball trajectory (side view) — use slider or Play to animate",
    xaxis_title="Distance (yards)",
    yaxis_title="Height (yards)",
    xaxis=dict(range=[-5, max(x_yd) * 1.02], zeroline=True, zerolinewidth=1, zerolinecolor="lightgray"),
    yaxis=dict(range=[-2, max(y_yd) * 1.15], zeroline=True, zerolinewidth=1, zerolinecolor="lightgray"),
    showlegend=False,
    height=500,
    margin=dict(l=60, r=40, t=50, b=50),
    updatemenus=[
        dict(
            type="buttons",
            showactive=False,
            x=0.1,
            y=0,
            xanchor="left",
            buttons=[
                dict(label="▶ Play", method="animate", args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode="immediate")]),
                dict(label="⏸ Pause", method="animate", args=[[None], dict(mode="immediate")]),
            ],
        )
    ],
    sliders=[
        dict(
            active=0,
            xanchor="left",
            x=0.1,
            len=0.9,
            y=0,
            pad=dict(b=10, t=30),
            currentvalue=dict(visible=True, prefix="Time: ", suffix=" s", xanchor="center"),
            steps=[dict(args=[[str(k)], dict(frame=dict(duration=0, redraw=True), mode="immediate")], label=f"{t_arr[k]:.2f}s", method="animate") for k in range(0, n_frames, max(1, n_frames // 15))],
        )
    ],
)

# Start at first frame
fig.layout.sliders[0].active = 0
st.plotly_chart(fig, use_container_width=True)

st.caption("Trajectory uses projectile motion; horizontal scale is adjusted so landing matches your actual carry distance. Spin is used to slightly extend hang time.")

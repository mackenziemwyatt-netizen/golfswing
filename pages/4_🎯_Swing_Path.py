import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from golf_data import get_data_and_filters, render_session_banner

# Viktor Hovland approximate metrics (TrackMan-style). Pro data is approximate from publicly
# available Tour/TrackMan and reported stats; Hovland is longer than tour average.
HOVLAND_METRICS = {
    "Driver": {"Club Path": 0.0, "Club Face": 0.0, "Attack Angle": 3.5, "Club Speed": 120, "Ball Speed": 180},
    "3 Wood": {"Club Path": -0.5, "Club Face": 0.0, "Attack Angle": -1.0, "Club Speed": 107, "Ball Speed": 158},
    "5 Wood": {"Club Path": -0.5, "Club Face": 0.0, "Attack Angle": -2.0, "Club Speed": 102, "Ball Speed": 150},
    "3 Iron": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -3.0, "Club Speed": 98, "Ball Speed": 132},
    "4 Iron": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -3.5, "Club Speed": 95, "Ball Speed": 126},
    "5 Iron": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -4.0, "Club Speed": 92, "Ball Speed": 120},
    "6 Iron": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -4.0, "Club Speed": 90, "Ball Speed": 118},
    "7 Iron": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -4.5, "Club Speed": 86, "Ball Speed": 113},
    "8 Iron": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -5.0, "Club Speed": 82, "Ball Speed": 108},
    "9 Iron": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -5.0, "Club Speed": 78, "Ball Speed": 102},
    "Pitching Wedge": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -5.0, "Club Speed": 76, "Ball Speed": 98},
    "PW": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -5.0, "Club Speed": 76, "Ball Speed": 98},
    "Gap Wedge": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -5.0, "Club Speed": 74, "Ball Speed": 95},
    "Sand Wedge": {"Club Path": -0.5, "Club Face": -0.5, "Attack Angle": -5.0, "Club Speed": 72, "Ball Speed": 90},
}

def _closest_hovland_club(club_type: str) -> str:
    """Map user club type to closest Hovland key."""
    ct = str(club_type).strip()
    if ct in HOVLAND_METRICS:
        return ct
    ct_lower = ct.lower()
    for key in ["Driver", "3 Wood", "5 Wood", "3 Iron", "4 Iron", "5 Iron", "6 Iron", "7 Iron", "8 Iron", "9 Iron", "Pitching Wedge", "PW", "Gap Wedge", "Sand Wedge"]:
        if key.lower() in ct_lower or ct_lower in key.lower():
            return key
    if "driver" in ct_lower or "1 wood" in ct_lower:
        return "Driver"
    if "wedge" in ct_lower and "pitch" in ct_lower:
        return "Pitching Wedge"
    if "wedge" in ct_lower and "gap" in ct_lower:
        return "Gap Wedge"
    if "wedge" in ct_lower and "sand" in ct_lower:
        return "Sand Wedge"
    for n in range(3, 10):
        if f"{n} iron" in ct_lower or f"{n}-iron" in ct_lower:
            return f"{n} Iron"
    return "Driver"  # fallback

all_dfs, df = get_data_and_filters()
render_session_banner()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see swing path analysis.")
    st.stop()

swing_path_cols = ["Club Path", "Club Face", "Face to Path"]
if not all(col in df.columns for col in swing_path_cols):
    st.warning("This dataset does not contain Club Path, Club Face, and Face to Path columns.")
    st.stop()

st.header("🎯 Swing Path Analysis & Coaching")
st.markdown("Analyze your swing path, face angle, and face-to-path relationship. **We target an out-to-in swing path** as the ideal—positive club path numbers indicate out-to-in (good); negative numbers indicate in-to-out (needs work).")

swing_df = df[swing_path_cols + (["Club Type"] if "Club Type" in df.columns else [])].dropna(subset=swing_path_cols)
if len(swing_df) == 0:
    st.warning("Not enough swing path data available.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    avg_path = swing_df["Club Path"].mean()
    st.metric("Avg Club Path", f"{avg_path:.1f}°", delta="Out-to-In ✓" if avg_path > 0 else "In-to-Out (needs work)" if avg_path < 0 else "Neutral")
with col2:
    avg_face = swing_df["Club Face"].mean()
    st.metric("Avg Face Angle", f"{avg_face:.1f}°", delta="Closed" if avg_face < 0 else "Open" if avg_face > 0 else "Square")
with col3:
    avg_ftp = swing_df["Face to Path"].mean()
    st.metric("Avg Face-to-Path", f"{avg_ftp:.1f}°", delta="Draw Bias" if avg_ftp > 0 else "Fade Bias" if avg_ftp < 0 else "Straight")
with col4:
    out_to_in_pct = (swing_df["Club Path"] > 0).sum() / len(swing_df) * 100
    st.metric("Out-to-In Swings (target)", f"{out_to_in_pct:.1f}%", delta=f"{out_to_in_pct:.0f}% of swings")

col1, col2 = st.columns(2)
with col1:
    fig = px.histogram(swing_df, x="Club Path", nbins=30, title="Club Path Distribution", labels={"Club Path": "Club Path (degrees)", "count": "Frequency"}, color_discrete_sequence=["#2E86AB"])
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Neutral Path", annotation_position="top")
    fig.add_vline(x=2, line_dash="dot", line_color="green", annotation_text="Ideal Out-to-In (target)", annotation_position="top")
    st.plotly_chart(fig, use_container_width=True)
    fig = px.scatter(swing_df, x="Club Path", y="Face to Path", color="Club Type" if "Club Type" in swing_df.columns else None, title="Face-to-Path vs Club Path", labels={"Club Path": "Club Path (degrees)", "Face to Path": "Face-to-Path (degrees)"}, hover_data=["Club Face"] if "Club Face" in swing_df.columns else None)
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.add_shape(type="rect", x0=0.5, y0=-3, x1=5, y1=0, fillcolor="lightgreen", opacity=0.2, layer="below", line_width=0)
    fig.add_annotation(x=2.5, y=-1.5, text="Ideal zone: out-to-in path + controlled fade", showarrow=False, font=dict(size=10))
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.histogram(swing_df, x="Club Face", nbins=30, title="Face Angle Distribution", labels={"Club Face": "Face Angle (degrees)", "count": "Frequency"}, color_discrete_sequence=["#A23B72"])
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Square Face", annotation_position="top")
    st.plotly_chart(fig, use_container_width=True)
    fig = px.histogram(swing_df, x="Face to Path", nbins=30, title="Face-to-Path Distribution", labels={"Face to Path": "Face-to-Path (degrees)", "count": "Frequency"}, color_discrete_sequence=["#F18F01"])
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Straight", annotation_position="top")
    fig.add_vline(x=-2, line_dash="dot", line_color="green", annotation_text="Ideal Fade (with out-to-in path)", annotation_position="top")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("💡 Personalized Coaching Tips")
avg_club_path = swing_df["Club Path"].mean()
avg_face_to_path = swing_df["Face to Path"].mean()
consistency_path = swing_df["Club Path"].std()
consistency_ftp = swing_df["Face to Path"].std()
tips = []
if avg_club_path <= -3:
    tips.append({"Priority": "🔴 HIGH", "Issue": "In-to-Out Swing Path (needs work)", "Current": f"Your average club path is {avg_club_path:.1f}° (in-to-out)", "Impact": "We want out-to-in; your path is too far inside-out.", "Tips": ["Feel the club exiting left of target (right-handed): 'swing to left field'.", "Lead with the hands slightly in the downswing to avoid dropping the club too far inside.", "Try the 'wall drill' on your lead side: stand with a wall just left of your hands to limit how far inside you can take the club.", "Check setup: lead shoulder slightly lower can encourage a path that works more left.", "Practice down-the-line: feel the clubhead moving left through impact."]})
elif avg_club_path < 0:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Slightly In-to-Out Path", "Current": f"Your average club path is {avg_club_path:.1f}°", "Impact": "Moving toward out-to-in; a bit more left through impact would hit our target.", "Tips": ["Emphasize 'exiting left' after impact—feel the club going left of target.", "Avoid over-rotating the hips early; let the arms work slightly more in front.", "Use an alignment stick outside the ball line to encourage path working left."]})
elif avg_club_path < 2:
    tips.append({"Priority": "🟢 GOOD", "Issue": "Neutral to Slightly Out-to-In Path", "Current": f"Your average club path is {avg_club_path:.1f}°", "Impact": "Good foundation; close to our out-to-in target.", "Tips": ["Maintain this path.", "Focus on consistency and face-to-path for your desired ball flight (e.g. controlled fade with slight open face to path)."]})
else:
    tips.append({"Priority": "✅ EXCELLENT", "Issue": "Strong Out-to-In Path", "Current": f"Your average club path is {avg_club_path:.1f}° (out-to-in)", "Impact": "Excellent—you're achieving our target out-to-in path.", "Tips": ["Maintain this path.", "Focus on face control so face-to-path matches your target (e.g. slight fade with face slightly open to path)."]})
if abs(avg_face_to_path) > 5:
    tips.append({"Priority": "🔴 HIGH", "Issue": "Extreme Face-to-Path", "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°", "Impact": f"Causes severe {'hooks' if avg_face_to_path > 0 else 'slices'}", "Tips": ["Work on face angle control.", "Practice with impact tape; try the 'gate drill' with two tees.", "Check grip and wrist position at impact."]})
elif avg_face_to_path < -2:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Face Open to Path (Fade Bias)", "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°", "Impact": "With an out-to-in path, slightly open face to path gives a controlled fade; too open causes slices.", "Tips": ["If you want a controlled fade, this can work with your out-to-in path—just avoid going too open.", "Check grip; focus on rotating forearms through impact if the ball is slicing too much."]})
elif avg_face_to_path > 2:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Face Closed to Path (Draw Bias)", "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°", "Impact": "With an out-to-in path, closed face to path can cause pulls or hooks.", "Tips": ["Open the face slightly relative to path for a straighter or gentle fade ball flight.", "Check grip and release; avoid over-closing through impact."]})
if consistency_path > 5:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Inconsistent Club Path", "Current": f"Your path varies by {consistency_path:.1f}° on average", "Impact": "Inconsistent ball flight; harder to lock in a consistent out-to-in path.", "Tips": ["Focus on tempo and alignment aids.", "Work on consistent setup; slow down to focus on path control toward out-to-in."]})
if consistency_ftp > 4:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Inconsistent Face-to-Path", "Current": f"Your face-to-path varies by {consistency_ftp:.1f}° on average", "Impact": "Inconsistent ball flight patterns", "Tips": ["Work on grip and impact position consistency.", "Check wrist angles at impact."]})
for i, tip in enumerate(tips, 1):
    with st.expander(f"{tip['Priority']} - {tip['Issue']}", expanded=(i == 1)):
        st.write(f"**Current Performance:** {tip['Current']}")
        if "Impact" in tip:
            st.write(f"**Impact:** {tip['Impact']}")
        st.write("**Recommendations:**")
        for j, rec in enumerate(tip["Tips"], 1):
            st.write(f"{j}. {rec}")

# --- Tour Pro Comparison (Viktor Hovland) ---
comparison_metrics = ["Club Path", "Club Face", "Attack Angle", "Club Speed", "Ball Speed"]
comparison_available = [m for m in comparison_metrics if m in df.columns]
if "Club Type" in df.columns and len(comparison_available) >= 2:
    st.subheader("🏆 Tour Pro Comparison: Viktor Hovland")
    st.info("**Note:** Viktor Hovland's metrics are approximate, based on publicly available TrackMan/launch monitor and PGA Tour data. Use for general comparison and motivation only—not as precise targets.")
    comparison_df = df[["Club Type"] + comparison_available].dropna(subset=comparison_available)
    if len(comparison_df) > 0:
        club_types = comparison_df["Club Type"].dropna().unique().tolist()
        rows = []
        for club in club_types:
            sub = comparison_df[comparison_df["Club Type"] == club]
            hovland_key = _closest_hovland_club(club)
            hovland = HOVLAND_METRICS.get(hovland_key, HOVLAND_METRICS["Driver"])
            for metric in comparison_available:
                my_avg = sub[metric].mean()
                pro_val = hovland.get(metric)
                if pro_val is None:
                    continue
                diff = my_avg - pro_val
                rows.append({"Club Type": club, "Metric": metric, "My Avg": round(my_avg, 2), "Viktor Hovland": pro_val, "Difference": round(diff, 2)})
        if rows:
            comp_table = pd.DataFrame(rows)
            pivot_diff = comp_table.pivot(index="Club Type", columns="Metric", values="Difference").reset_index()
            st.markdown("**Comparison table (My average vs Viktor Hovland)**")
            st.dataframe(comp_table, use_container_width=True, hide_index=True)
            st.markdown("**Gap by metric (My Avg − Hovland)**")
            st.dataframe(pivot_diff.set_index("Club Type"), use_container_width=True, hide_index=True)
            # Side-by-side charts: swing path first, then speed metrics
            club_order = sorted(club_types, key=lambda c: (0 if "Driver" in str(c) else 1 if "Wood" in str(c) else 2, str(c)))
            chart_metrics = [m for m in ["Club Path", "Attack Angle", "Club Speed", "Ball Speed", "Club Face"] if m in comparison_available]
            for metric in chart_metrics:
                sub = comp_table[comp_table["Metric"] == metric]
                order_in_data = [c for c in club_order if c in sub["Club Type"].values]
                my_vals = [sub[sub["Club Type"] == c]["My Avg"].iloc[0] for c in order_in_data]
                pro_vals = [sub[sub["Club Type"] == c]["Viktor Hovland"].iloc[0] for c in order_in_data]
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Me", x=order_in_data, y=my_vals, marker_color="#2E86AB"))
                fig.add_trace(go.Bar(name="Viktor Hovland", x=order_in_data, y=pro_vals, marker_color="#F18F01"))
                units = "°" if metric in ["Club Path", "Club Face", "Attack Angle", "Face to Path"] else " mph"
                fig.update_layout(title=f"{metric} by club: Me vs Viktor Hovland", barmode="group", xaxis_title="Club Type", yaxis_title=metric + units)
                st.plotly_chart(fig, use_container_width=True)
            # Insights: which metrics are close vs need work
            st.markdown("**Insights**")
            gaps = comp_table.copy()
            gaps["AbsDiff"] = gaps["Difference"].abs()
            # For path/face/attack (degrees), "close" = within ~2–3°; for speed (mph), within ~10–15%
            def is_close(row):
                v = row["Metric"]
                d = row["AbsDiff"]
                if v in ["Club Speed", "Ball Speed"]:
                    pro = row["Viktor Hovland"]
                    return d <= max(8, pro * 0.10)
                return d <= 3
            gaps["Close"] = gaps.apply(is_close, axis=1)
            close_metrics = gaps[gaps["Close"]].groupby("Metric").size()
            need_work = gaps[~gaps["Close"]].groupby("Metric").size()
            close_list = list(close_metrics.index) if len(close_metrics) else []
            work_list = list(need_work.index) if len(need_work) else []
            if close_list:
                st.success(f"**Closest to Hovland:** You're within a reasonable range on **{', '.join(close_list)}** for the clubs you hit.")
            if work_list:
                st.warning(f"**Most room to improve:** Focus on **{', '.join(work_list)}**—these show the largest gaps vs Hovland's benchmarks.")
            if not close_list and not work_list:
                st.info("Compare your numbers to the table and charts above to see where you stand vs Viktor Hovland.")
    else:
        st.warning("No data with Club Type and comparison metrics available for Tour Pro Comparison.")
else:
    if "Club Type" not in df.columns:
        st.caption("Upload data with **Club Type** to see the Tour Pro Comparison (Viktor Hovland).")
    elif len(comparison_available) < 2:
        st.caption("Add **Club Path**, **Club Face**, **Attack Angle**, **Club Speed**, or **Ball Speed** to your data to enable Tour Pro Comparison.")

st.subheader("📊 Swing Path Statistics")
st.dataframe(swing_df[swing_path_cols].describe(), use_container_width=True)
if "Club Type" in swing_df.columns:
    st.subheader("Swing Path by Club Type")
    st.dataframe(swing_df.groupby("Club Type")[swing_path_cols].agg(["mean", "std"]).round(2), use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
from golf_data import get_data_and_filters

all_dfs, df = get_data_and_filters()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see swing path analysis.")
    st.stop()

swing_path_cols = ["Club Path", "Club Face", "Face to Path"]
if not all(col in df.columns for col in swing_path_cols):
    st.warning("This dataset does not contain Club Path, Club Face, and Face to Path columns.")
    st.stop()

st.header("🎯 Swing Path Analysis & Coaching")
st.markdown("Analyze your swing path, face angle, and face-to-path relationship to improve your ball flight.")

swing_df = df[swing_path_cols + (["Club Type"] if "Club Type" in df.columns else [])].dropna(subset=swing_path_cols)
if len(swing_df) == 0:
    st.warning("Not enough swing path data available.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    avg_path = swing_df["Club Path"].mean()
    st.metric("Avg Club Path", f"{avg_path:.1f}°", delta="In-to-Out" if avg_path > 0 else "Out-to-In" if avg_path < 0 else "Neutral")
with col2:
    avg_face = swing_df["Club Face"].mean()
    st.metric("Avg Face Angle", f"{avg_face:.1f}°", delta="Closed" if avg_face < 0 else "Open" if avg_face > 0 else "Square")
with col3:
    avg_ftp = swing_df["Face to Path"].mean()
    st.metric("Avg Face-to-Path", f"{avg_ftp:.1f}°", delta="Draw Bias" if avg_ftp > 0 else "Fade Bias" if avg_ftp < 0 else "Straight")
with col4:
    in_to_out_pct = (swing_df["Club Path"] > 0).sum() / len(swing_df) * 100
    st.metric("In-to-Out Swings", f"{in_to_out_pct:.1f}%", delta=f"{in_to_out_pct:.0f}% of swings")

col1, col2 = st.columns(2)
with col1:
    fig = px.histogram(swing_df, x="Club Path", nbins=30, title="Club Path Distribution", labels={"Club Path": "Club Path (degrees)", "count": "Frequency"}, color_discrete_sequence=["#2E86AB"])
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Neutral Path", annotation_position="top")
    fig.add_vline(x=2, line_dash="dot", line_color="green", annotation_text="Ideal In-to-Out", annotation_position="top")
    st.plotly_chart(fig, use_container_width=True)
    fig = px.scatter(swing_df, x="Club Path", y="Face to Path", color="Club Type" if "Club Type" in swing_df.columns else None, title="Face-to-Path vs Club Path", labels={"Club Path": "Club Path (degrees)", "Face to Path": "Face-to-Path (degrees)"}, hover_data=["Club Face"] if "Club Face" in swing_df.columns else None)
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5, y1=3, fillcolor="lightgreen", opacity=0.2, layer="below", line_width=0)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.histogram(swing_df, x="Club Face", nbins=30, title="Face Angle Distribution", labels={"Club Face": "Face Angle (degrees)", "count": "Frequency"}, color_discrete_sequence=["#A23B72"])
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Square Face", annotation_position="top")
    st.plotly_chart(fig, use_container_width=True)
    fig = px.histogram(swing_df, x="Face to Path", nbins=30, title="Face-to-Path Distribution", labels={"Face to Path": "Face-to-Path (degrees)", "count": "Frequency"}, color_discrete_sequence=["#F18F01"])
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Straight", annotation_position="top")
    fig.add_vline(x=2, line_dash="dot", line_color="green", annotation_text="Ideal Draw", annotation_position="top")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("💡 Personalized Coaching Tips")
avg_club_path = swing_df["Club Path"].mean()
avg_face_to_path = swing_df["Face to Path"].mean()
consistency_path = swing_df["Club Path"].std()
consistency_ftp = swing_df["Face to Path"].std()
tips = []
if avg_club_path < -3:
    tips.append({"Priority": "🔴 HIGH", "Issue": "Out-to-In Swing Path", "Current": f"Your average club path is {avg_club_path:.1f}° (out-to-in)", "Impact": "This causes slices, pulls, and loss of distance", "Tips": ["Focus on swinging from inside the ball.", "Feel like you're swinging 'out to right field' (right-handed golfers).", "Work on hip rotation so your hips clear before impact.", "Try the 'wall drill': stand close to a wall on your trail side to force an inside path."]})
elif avg_club_path < 0:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Slightly Out-to-In Path", "Current": f"Your average club path is {avg_club_path:.1f}°", "Impact": "Can cause fades and slight loss of distance", "Tips": ["Start your downswing with your lower body, not your arms.", "Practice the 'pump drill' focusing on dropping the club inside.", "Check your setup: trail shoulder shouldn't be too high."]})
elif avg_club_path < 2:
    tips.append({"Priority": "🟢 GOOD", "Issue": "Neutral to Slightly In-to-Out Path", "Current": f"Your average club path is {avg_club_path:.1f}°", "Impact": "Good foundation; close to ideal", "Tips": ["Maintain this path.", "Focus on consistency and fine-tune face-to-path for desired ball flight."]})
else:
    tips.append({"Priority": "✅ EXCELLENT", "Issue": "Strong In-to-Out Path", "Current": f"Your average club path is {avg_club_path:.1f}°", "Impact": "Excellent for draws and distance", "Tips": ["Maintain this path.", "Focus on face control so face-to-path matches your target."]})
if abs(avg_face_to_path) > 5:
    tips.append({"Priority": "🔴 HIGH", "Issue": "Extreme Face-to-Path", "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°", "Impact": f"Causes severe {'hooks' if avg_face_to_path > 0 else 'slices'}", "Tips": ["Work on face angle control.", "Practice with impact tape; try the 'gate drill' with two tees.", "Check grip and wrist position at impact."]})
elif avg_face_to_path < -2:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Face Open to Path (Fade Bias)", "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°", "Impact": "Promotes fades and slices", "Tips": ["Close the face slightly relative to path for a draw.", "Check grip; focus on rotating forearms through impact."]})
if consistency_path > 5:
    tips.append({"Priority": "🟡 MEDIUM", "Issue": "Inconsistent Club Path", "Current": f"Your path varies by {consistency_path:.1f}° on average", "Impact": "Inconsistent ball flight", "Tips": ["Focus on tempo and alignment aids.", "Work on consistent setup; slow down to focus on path control."]})
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

st.subheader("📊 Swing Path Statistics")
st.dataframe(swing_df[swing_path_cols].describe(), use_container_width=True)
if "Club Type" in swing_df.columns:
    st.subheader("Swing Path by Club Type")
    st.dataframe(swing_df.groupby("Club Type")[swing_path_cols].agg(["mean", "std"]).round(2), use_container_width=True)

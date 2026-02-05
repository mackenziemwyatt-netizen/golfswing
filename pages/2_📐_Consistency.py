import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from golf_data import get_data_and_filters

all_dfs, df = get_data_and_filters()
if df is None or len(df) == 0:
    st.info("👆 Upload CSV files on **Home** to see consistency scoring.")
    st.stop()

consistency_metrics = ["Club Path", "Club Face", "Club Speed"]
consistency_available = [m for m in consistency_metrics if m in df.columns]

if len(consistency_available) < 1:
    st.warning("No consistency metrics (Club Path, Club Face, Club Speed) in this dataset.")
    st.stop()

st.header("📐 Consistency Scoring")
st.markdown(
    "Dispersion scores for **club path**, **face angle**, and **club speed**. "
    "For each metric we compute standard deviation and convert to a **0–100 consistency score** (lower SD = higher score). "
    "**Gauge bands:** 🟢 Excellent (80–100) · 🟡 Good (60–79) · 🔴 Needs work (below 60)."
)

sd_max = {"Club Path": 8, "Club Face": 8, "Club Speed": 10}

def consistency_score_from_sd(sd, metric_name):
    mx = sd_max.get(metric_name, 8)
    if pd.isna(sd) or mx <= 0:
        return 0
    return max(0, min(100, 100 - (sd / mx) * 100))

def consistency_label(score):
    if score >= 80:
        return "Excellent", "#28a745", "🟢"
    if score >= 60:
        return "Good", "#ffc107", "🟡"
    return "Needs Work", "#dc3545", "🔴"

cons_df = df[consistency_available].dropna(how="all")
if len(cons_df) == 0:
    st.warning("No rows with consistency metrics.")
    st.stop()

scores_by_metric = {}
for m in consistency_available:
    sd = cons_df[m].std()
    scores_by_metric[m] = {
        "std_dev": sd,
        "score": consistency_score_from_sd(sd, m),
        "label": consistency_label(consistency_score_from_sd(sd, m))[0],
        "color": consistency_label(consistency_score_from_sd(sd, m))[1],
    }

overall_score = sum(s["score"] for s in scores_by_metric.values()) / len(scores_by_metric)
overall_label, overall_color, overall_emoji = consistency_label(overall_score)

st.subheader("Overall Consistency Score")
gauge_fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=round(overall_score, 1),
        number={"suffix": "/ 100", "font": {"size": 28}},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": overall_color},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 60], "color": "rgba(220, 53, 69, 0.2)"},
                {"range": [60, 80], "color": "rgba(255, 193, 7, 0.2)"},
                {"range": [80, 100], "color": "rgba(40, 167, 69, 0.2)"},
            ],
            "threshold": {"line": {"color": overall_color, "width": 4}, "thickness": 0.75, "value": round(overall_score, 1)},
        },
        title={"text": f"{overall_emoji} {overall_label}", "font": {"size": 20}},
    )
)
gauge_fig.update_layout(height=280, margin=dict(l=20, r=20, t=60, b=20), paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(gauge_fig, use_container_width=True)

st.subheader("Consistency by Metric")
cols = st.columns(len(consistency_available))
units = {"Club Path": "°", "Club Face": "°", "Club Speed": " mph"}
for idx, m in enumerate(consistency_available):
    with cols[idx]:
        sd = scores_by_metric[m]["std_dev"]
        sc = scores_by_metric[m]["score"]
        u = units.get(m, "")
        st.metric(m, f"SD: {sd:.2f}{u}", f"Score: {sc:.0f}/100")
        label_text, bar_color, _ = consistency_label(sc)
        st.markdown(f"**{label_text}**")
        bar_fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=sc,
                number={"suffix": "", "font": {"size": 18}},
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {"range": [0, 100], "visible": True},
                    "bar": {"color": bar_color},
                    "bgcolor": "lightgray",
                    "borderwidth": 1,
                    "steps": [
                        {"range": [0, 60], "color": "rgba(220, 53, 69, 0.3)"},
                        {"range": [60, 80], "color": "rgba(255, 193, 7, 0.3)"},
                        {"range": [80, 100], "color": "rgba(40, 167, 69, 0.3)"},
                    ],
                    "threshold": {"line": {"color": bar_color}, "thickness": 0.8, "value": sc},
                },
            )
        )
        bar_fig.update_layout(height=140, margin=dict(l=10, r=10, t=5, b=5), showlegend=False)
        st.plotly_chart(bar_fig, use_container_width=True)

st.subheader("Dispersion Details")
disp_table = pd.DataFrame(
    [
        {
            "Metric": m,
            "Standard Deviation": f"{scores_by_metric[m]['std_dev']:.3f}",
            "Consistency Score (0-100)": f"{scores_by_metric[m]['score']:.1f}",
            "Rating": scores_by_metric[m]["label"],
        }
        for m in consistency_available
    ]
)
st.dataframe(disp_table, use_container_width=True, hide_index=True)

if "Club Type" in df.columns and len(consistency_available) > 0:
    st.subheader("Consistency Breakdown by Club Type")
    club_consistency = []
    for club in df["Club Type"].dropna().unique():
        sub = df[df["Club Type"] == club]
        row = {"Club Type": club}
        total_score = count = 0
        for m in consistency_available:
            vals = sub[m].dropna()
            if len(vals) >= 2:
                sd = vals.std()
                sc = consistency_score_from_sd(sd, m)
                row[f"{m} SD"] = round(sd, 3)
                row[f"{m} Score"] = round(sc, 1)
                total_score += sc
                count += 1
        if count > 0:
            row["Overall Score"] = round(total_score / count, 1)
            row["Rating"] = consistency_label(row["Overall Score"])[0]
            club_consistency.append(row)

    if club_consistency:
        club_cons_df = pd.DataFrame(club_consistency).sort_values("Overall Score", ascending=False).reset_index(drop=True)

        st.subheader("Most & Least Consistent Clubs")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            most = club_cons_df.iloc[0]
            m_label, _, _ = consistency_label(most["Overall Score"])
            st.markdown("**🟢 Most consistent**")
            st.metric(most["Club Type"], f"{most['Overall Score']:.1f} / 100", m_label)
        with c2:
            if len(club_cons_df) > 1:
                least = club_cons_df.iloc[-1]
                l_label, _, _ = consistency_label(least["Overall Score"])
                st.markdown("**🔴 Least consistent**")
                st.metric(least["Club Type"], f"{least['Overall Score']:.1f} / 100", l_label)
            else:
                st.info("Only one club type in data.")
        with c3:
            st.caption("Focus practice on least consistent clubs.")

        st.subheader("Consistency by Club Type (full table)")
        st.dataframe(club_cons_df, use_container_width=True, hide_index=True)

        fig_club = px.bar(
            club_cons_df,
            x="Club Type",
            y="Overall Score",
            color="Overall Score",
            color_continuous_scale=["#dc3545", "#ffc107", "#28a745"],
            range_color=[0, 100],
            title="Overall Consistency Score by Club Type (higher = more consistent)",
            labels={"Overall Score": "Consistency Score (0-100)"},
        )
        fig_club.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Excellent (80+)")
        fig_club.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Good (60–79)")
        fig_club.update_layout(showlegend=False)
        st.plotly_chart(fig_club, use_container_width=True)

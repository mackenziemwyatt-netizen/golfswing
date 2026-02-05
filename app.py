import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import io

# Persistent directory for saved CSV files (relative to app directory)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_DATA_DIR = os.path.join(APP_DIR, "saved_data")

def ensure_saved_data_dir():
    """Create the saved data directory if it doesn't exist."""
    os.makedirs(SAVED_DATA_DIR, exist_ok=True)

def get_saved_csv_paths():
    """Return list of full paths to all CSV files in the saved data directory."""
    ensure_saved_data_dir()
    paths = []
    for name in os.listdir(SAVED_DATA_DIR):
        if name.lower().endswith(".csv"):
            path = os.path.join(SAVED_DATA_DIR, name)
            if os.path.isfile(path):
                paths.append(path)
    return sorted(paths)

def save_uploaded_file(file) -> str:
    """Save an uploaded file to the persistent directory. Returns the path."""
    ensure_saved_data_dir()
    # Use original name; if exists, add timestamp prefix to avoid overwriting
    base = file.name
    path = os.path.join(SAVED_DATA_DIR, base)
    if os.path.exists(path):
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = f"{stamp}_{base}"
        path = os.path.join(SAVED_DATA_DIR, base)
    with open(path, "wb") as f:
        f.write(file.getvalue())
    return path

def delete_saved_file(path: str) -> bool:
    """Delete a file from the saved data directory. Returns True if deleted."""
    path = os.path.normpath(path)
    if not path.startswith(os.path.normpath(SAVED_DATA_DIR)):
        return False
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False

def load_golf_data(file):
    """Load golf swing data from file-like object, skipping the units row (row 2)."""
    df = pd.read_csv(file, skiprows=[1])  # Skip row 2 (index 1) which contains units
    
    # Try to parse Date column if it exists
    if 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except:
            pass
    
    # Add filename as a column for tracking
    df['Source File'] = file.name
    
    return df

def load_golf_data_from_path(path: str):
    """Load golf swing data from a file path, skipping the units row (row 2)."""
    with open(path, "rb") as f:
        df = pd.read_csv(io.BytesIO(f.read()), skiprows=[1])
    if 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except:
            pass
    df['Source File'] = os.path.basename(path)
    return df

# Page configuration
st.set_page_config(
    page_title="Golf Swing Data Analyzer",
    page_icon="⛳",
    layout="wide"
)

# Title and description
st.title("⛳ Golf Swing Data Analyzer")
st.markdown("Upload CSV file(s) containing golf swing data to view statistics and visualizations. "
            "Uploaded files are saved and **automatically loaded** when you return.")

# Sidebar: Manage saved files (always visible)
st.sidebar.header("📁 Saved Data")
with st.sidebar.expander("Manage saved files", expanded=False):
    saved_paths = get_saved_csv_paths()
    if not saved_paths:
        st.info("No saved files yet. Upload CSV files to save them.")
    else:
        st.caption("Saved files are loaded automatically on startup.")
        for i, path in enumerate(saved_paths):
            name = os.path.basename(path)
            try:
                size = os.path.getsize(path)
                size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
            except OSError:
                size_str = "?"
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"{name}")
                st.caption(size_str)
            with col2:
                if st.button("🗑️", key=f"del_{i}_{name}", help=f"Delete {name}"):
                    if delete_saved_file(path):
                        st.success("Deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete.")

# File uploader - allow multiple files
uploaded_files = st.file_uploader(
    "Choose CSV file(s)",
    type=['csv'],
    help="Upload one or more CSV files with golf swing metrics",
    accept_multiple_files=True
)

# Build data: load all saved CSVs + save and include any newly uploaded files
all_dfs = []
# 1) Load all saved files from disk
for path in get_saved_csv_paths():
    try:
        all_dfs.append(load_golf_data_from_path(path))
    except Exception:
        pass  # Skip corrupted or unreadable files
# 2) Save any newly uploaded files to disk and add to list
if uploaded_files:
    for file in uploaded_files:
        try:
            save_uploaded_file(file)
            file.seek(0)
            all_dfs.append(load_golf_data(file))
        except Exception:
            pass
# 3) If we have any data (saved or just uploaded), use it
if all_dfs:
    try:
        # Combine all dataframes (saved + newly uploaded)
        df = pd.concat(all_dfs, ignore_index=True)
        
        # Filters sidebar
        st.sidebar.header("🔍 Filters")
        
        # Club Type filter
        if 'Club Type' in df.columns:
            club_types = ['All'] + sorted(df['Club Type'].dropna().unique().tolist())
            selected_club = st.sidebar.selectbox("Filter by Club Type", club_types)
            if selected_club != 'All':
                df = df[df['Club Type'] == selected_club]
        
        # Date range filter
        if 'Date' in df.columns and df['Date'].notna().any():
            dates = df['Date'].dropna()
            if len(dates) > 0:
                min_date = dates.min()
                max_date = dates.max()
                date_range = st.sidebar.date_input(
                    "Date Range",
                    value=(min_date.date() if hasattr(min_date, 'date') else min_date, 
                           max_date.date() if hasattr(max_date, 'date') else max_date),
                    min_value=min_date.date() if hasattr(min_date, 'date') else min_date,
                    max_value=max_date.date() if hasattr(max_date, 'date') else max_date
                )
                if len(date_range) == 2:
                    df = df[(df['Date'] >= pd.Timestamp(date_range[0])) & 
                            (df['Date'] <= pd.Timestamp(date_range[1]))]
        
        # Display basic info about the dataset
        st.header("📊 Dataset Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Swings", len(df))
        with col2:
            if 'Club Type' in df.columns:
                unique_clubs = df['Club Type'].nunique()
                st.metric("Club Types", unique_clubs)
            else:
                st.metric("Total Columns", len(df.columns))
        with col3:
            if 'Carry Distance' in df.columns:
                avg_carry = df['Carry Distance'].mean()
                st.metric("Avg Carry Distance", f"{avg_carry:.1f} yds")
            else:
                st.metric("Numeric Columns", len(df.select_dtypes(include=['float64', 'int64']).columns))
        with col4:
            if 'Total Distance' in df.columns:
                avg_total = df['Total Distance'].mean()
                st.metric("Avg Total Distance", f"{avg_total:.1f} yds")
            else:
                st.metric("Missing Values", df.isnull().sum().sum())
        
        # Display first few rows
        st.subheader("Preview Data")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Consistency Scoring Section
        consistency_metrics = ['Club Path', 'Club Face', 'Club Speed']
        consistency_available = [m for m in consistency_metrics if m in df.columns]
        
        if len(consistency_available) >= 1:
            st.header("📐 Consistency Scoring")
            st.markdown("Dispersion scores for key metrics. Lower standard deviation = more consistent. Overall score 0–100.")
            
            # Thresholds: SD beyond this maps to 0. (degrees for path/face, mph for speed)
            sd_max = {'Club Path': 8, 'Club Face': 8, 'Club Speed': 10}
            
            def consistency_score_from_sd(sd, metric_name):
                """Convert standard deviation to 0-100 consistency score."""
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
            
            # Overall consistency: use available metrics only
            cons_df = df[consistency_available].dropna(how='all')
            if len(cons_df) > 0:
                scores_by_metric = {}
                for m in consistency_available:
                    sd = cons_df[m].std()
                    scores_by_metric[m] = {
                        'std_dev': sd,
                        'score': consistency_score_from_sd(sd, m),
                        'label': consistency_label(consistency_score_from_sd(sd, m))[0],
                        'color': consistency_label(consistency_score_from_sd(sd, m))[1],
                    }
                
                overall_score = sum(s['score'] for s in scores_by_metric.values()) / len(scores_by_metric)
                overall_label, overall_color, overall_emoji = consistency_label(overall_score)
                
                # Visual gauge for overall consistency
                st.subheader("Overall Consistency Score")
                gauge_fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=round(overall_score, 1),
                    number={'suffix': "/ 100", 'font': {'size': 28}},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1},
                        'bar': {'color': overall_color},
                        'bgcolor': 'white',
                        'borderwidth': 2,
                        'bordercolor': 'gray',
                        'steps': [
                            {'range': [0, 60], 'color': 'rgba(220, 53, 69, 0.2)'},
                            {'range': [60, 80], 'color': 'rgba(255, 193, 7, 0.2)'},
                            {'range': [80, 100], 'color': 'rgba(40, 167, 69, 0.2)'},
                        ],
                        'threshold': {
                            'line': {'color': overall_color, 'width': 4},
                            'thickness': 0.75,
                            'value': round(overall_score, 1),
                        },
                    },
                    title={'text': f"{overall_emoji} {overall_label}", 'font': {'size': 20}},
                ))
                gauge_fig.update_layout(
                    height=280,
                    margin=dict(l=20, r=20, t=60, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(gauge_fig, use_container_width=True)
                
                # Metric-level: SD and 0-100 score with mini gauges
                st.subheader("Consistency by Metric")
                cols = st.columns(len(consistency_available))
                units = {'Club Path': '°', 'Club Face': '°', 'Club Speed': ' mph'}
                for idx, m in enumerate(consistency_available):
                    with cols[idx]:
                        sd = scores_by_metric[m]['std_dev']
                        sc = scores_by_metric[m]['score']
                        lbl = scores_by_metric[m]['label']
                        u = units.get(m, '')
                        st.metric(f"{m}", f"SD: {sd:.2f}{u}", f"Score: {sc:.0f}/100")
                        label_text, bar_color, _ = consistency_label(sc)
                        st.markdown(f"**{label_text}**")
                        # Small horizontal bar for visual
                        bar_fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=sc,
                            number={'suffix': "", 'font': {'size': 18}},
                            domain={'x': [0, 1], 'y': [0, 1]},
                            gauge={
                                'axis': {'range': [0, 100], 'visible': True},
                                'bar': {'color': bar_color},
                                'bgcolor': 'lightgray',
                                'borderwidth': 1,
                                'steps': [
                                    {'range': [0, 60], 'color': 'rgba(220, 53, 69, 0.3)'},
                                    {'range': [60, 80], 'color': 'rgba(255, 193, 7, 0.3)'},
                                    {'range': [80, 100], 'color': 'rgba(40, 167, 69, 0.3)'},
                                ],
                                'threshold': {'line': {'color': bar_color}, 'thickness': 0.8, 'value': sc},
                            },
                        ))
                        bar_fig.update_layout(height=140, margin=dict(l=10, r=10, t=5, b=5), showlegend=False)
                        st.plotly_chart(bar_fig, use_container_width=True)
                
                # Table: Standard deviation and score per metric
                st.subheader("Dispersion Details")
                disp_table = pd.DataFrame([
                    {
                        'Metric': m,
                        'Standard Deviation': f"{scores_by_metric[m]['std_dev']:.3f}",
                        'Consistency Score (0-100)': f"{scores_by_metric[m]['score']:.1f}",
                        'Rating': scores_by_metric[m]['label'],
                    }
                    for m in consistency_available
                ])
                st.dataframe(disp_table, use_container_width=True, hide_index=True)
                
                # Consistency breakdown by club type
                if 'Club Type' in df.columns and len(consistency_available) > 0:
                    st.subheader("Consistency Breakdown by Club Type")
                    club_consistency = []
                    for club in df['Club Type'].dropna().unique():
                        sub = df[df['Club Type'] == club]
                        row = {'Club Type': club}
                        total_score = 0
                        count = 0
                        for m in consistency_available:
                            vals = sub[m].dropna()
                            if len(vals) >= 2:
                                sd = vals.std()
                                sc = consistency_score_from_sd(sd, m)
                                row[f'{m} SD'] = round(sd, 3)
                                row[f'{m} Score'] = round(sc, 1)
                                total_score += sc
                                count += 1
                        if count > 0:
                            row['Overall Score'] = round(total_score / count, 1)
                            row['Rating'] = consistency_label(row['Overall Score'])[0]
                            club_consistency.append(row)
                    
                    if club_consistency:
                        club_cons_df = pd.DataFrame(club_consistency)
                        st.dataframe(club_cons_df, use_container_width=True, hide_index=True)
                        
                        # Bar chart: overall consistency score by club type
                        fig_club = px.bar(
                            club_cons_df,
                            x='Club Type',
                            y='Overall Score',
                            color='Overall Score',
                            color_continuous_scale=['#dc3545', '#ffc107', '#28a745'],
                            range_color=[0, 100],
                            title="Overall Consistency Score by Club Type",
                            labels={'Overall Score': 'Consistency Score (0-100)'},
                        )
                        fig_club.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Excellent")
                        fig_club.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Good")
                        fig_club.update_layout(showlegend=False)
                        st.plotly_chart(fig_club, use_container_width=True)
        
        # Golf-specific visualizations
        st.header("⛳ Golf-Specific Analysis")
        
        # Get numeric columns only
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if numeric_cols:
            # Key golf metrics visualization
            col1, col2 = st.columns(2)
            
            with col1:
                # Club Speed vs Distance
                if 'Club Speed' in df.columns and 'Carry Distance' in df.columns:
                    fig = px.scatter(
                        df,
                        x='Club Speed',
                        y='Carry Distance',
                        color='Club Type' if 'Club Type' in df.columns else None,
                        title="Club Speed vs Carry Distance",
                        labels={'Club Speed': 'Club Speed (mph)', 'Carry Distance': 'Carry Distance (yards)'},
                        hover_data=['Ball Speed'] if 'Ball Speed' in df.columns else None
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Launch Angle vs Distance
                if 'Launch Angle' in df.columns and 'Total Distance' in df.columns:
                    fig = px.scatter(
                        df,
                        x='Launch Angle',
                        y='Total Distance',
                        color='Club Type' if 'Club Type' in df.columns else None,
                        title="Launch Angle vs Total Distance",
                        labels={'Launch Angle': 'Launch Angle (degrees)', 'Total Distance': 'Total Distance (yards)'},
                        hover_data=['Ball Speed'] if 'Ball Speed' in df.columns else None
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Ball Speed vs Distance
                if 'Ball Speed' in df.columns and 'Carry Distance' in df.columns:
                    fig = px.scatter(
                        df,
                        x='Ball Speed',
                        y='Carry Distance',
                        color='Club Type' if 'Club Type' in df.columns else None,
                        title="Ball Speed vs Carry Distance",
                        labels={'Ball Speed': 'Ball Speed (mph)', 'Carry Distance': 'Carry Distance (yards)'},
                        hover_data=['Smash Factor'] if 'Smash Factor' in df.columns else None
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Spin Rate vs Distance
                if 'Spin Rate' in df.columns and 'Total Distance' in df.columns:
                    fig = px.scatter(
                        df,
                        x='Spin Rate',
                        y='Total Distance',
                        color='Club Type' if 'Club Type' in df.columns else None,
                        title="Spin Rate vs Total Distance",
                        labels={'Spin Rate': 'Spin Rate (rpm)', 'Total Distance': 'Total Distance (yards)'},
                        hover_data=['Launch Angle'] if 'Launch Angle' in df.columns else None
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Performance by Club Type
            if 'Club Type' in df.columns:
                st.subheader("Performance by Club Type")
                club_metrics = ['Carry Distance', 'Total Distance', 'Club Speed', 'Ball Speed']
                available_metrics = [m for m in club_metrics if m in df.columns]
                
                if available_metrics:
                    col1, col2 = st.columns(2)
                    with col1:
                        metric = st.selectbox("Select Metric", available_metrics, key="club_metric")
                    
                    if metric:
                        club_stats = df.groupby('Club Type')[metric].agg(['mean', 'std', 'count']).reset_index()
                        club_stats.columns = ['Club Type', 'Mean', 'Std Dev', 'Count']
                        
                        fig = px.bar(
                            club_stats,
                            x='Club Type',
                            y='Mean',
                            error_y='Std Dev',
                            title=f"Average {metric} by Club Type",
                            labels={'Mean': f'Average {metric}', 'Club Type': 'Club Type'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.dataframe(club_stats, use_container_width=True)
            
            # Swing Path Analysis Section
            swing_path_cols = ['Club Path', 'Club Face', 'Face to Path']
            if all(col in df.columns for col in swing_path_cols):
                st.header("🎯 Swing Path Analysis & Coaching")
                st.markdown("Analyze your swing path, face angle, and face-to-path relationship to improve your ball flight.")
                
                # Create a copy for analysis (remove missing values for swing path metrics)
                swing_df = df[swing_path_cols + (['Club Type'] if 'Club Type' in df.columns else [])].dropna(subset=swing_path_cols)
                
                if len(swing_df) > 0:
                    # Overview metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        avg_path = swing_df['Club Path'].mean()
                        st.metric("Avg Club Path", f"{avg_path:.1f}°", 
                                 delta="In-to-Out" if avg_path > 0 else "Out-to-In" if avg_path < 0 else "Neutral")
                    
                    with col2:
                        avg_face = swing_df['Club Face'].mean()
                        st.metric("Avg Face Angle", f"{avg_face:.1f}°",
                                 delta="Closed" if avg_face < 0 else "Open" if avg_face > 0 else "Square")
                    
                    with col3:
                        avg_ftp = swing_df['Face to Path'].mean()
                        st.metric("Avg Face-to-Path", f"{avg_ftp:.1f}°",
                                 delta="Draw Bias" if avg_ftp > 0 else "Fade Bias" if avg_ftp < 0 else "Straight")
                    
                    with col4:
                        in_to_out_pct = (swing_df['Club Path'] > 0).sum() / len(swing_df) * 100
                        st.metric("In-to-Out Swings", f"{in_to_out_pct:.1f}%",
                                 delta=f"{in_to_out_pct:.0f}% of swings")
                    
                    # Visualizations
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Club Path Distribution
                        fig = px.histogram(
                            swing_df,
                            x='Club Path',
                            nbins=30,
                            title="Club Path Distribution",
                            labels={'Club Path': 'Club Path (degrees)', 'count': 'Frequency'},
                            color_discrete_sequence=['#2E86AB']
                        )
                        # Add reference lines
                        fig.add_vline(x=0, line_dash="dash", line_color="red", 
                                     annotation_text="Neutral Path", annotation_position="top")
                        fig.add_vline(x=2, line_dash="dot", line_color="green", 
                                     annotation_text="Ideal In-to-Out", annotation_position="top")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Face to Path vs Club Path
                        fig = px.scatter(
                            swing_df,
                            x='Club Path',
                            y='Face to Path',
                            color='Club Type' if 'Club Type' in swing_df.columns else None,
                            title="Face-to-Path vs Club Path",
                            labels={'Club Path': 'Club Path (degrees)', 
                                   'Face to Path': 'Face-to-Path (degrees)'},
                            hover_data=['Club Face'] if 'Club Face' in swing_df.columns else None
                        )
                        # Add quadrant lines
                        fig.add_hline(y=0, line_dash="dash", line_color="gray")
                        fig.add_vline(x=0, line_dash="dash", line_color="gray")
                        # Add ideal zone (in-to-out with slight draw)
                        fig.add_shape(
                            type="rect",
                            x0=0, y0=0, x1=5, y1=3,
                            fillcolor="lightgreen",
                            opacity=0.2,
                            layer="below",
                            line_width=0,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Face Angle Distribution
                        fig = px.histogram(
                            swing_df,
                            x='Club Face',
                            nbins=30,
                            title="Face Angle Distribution",
                            labels={'Club Face': 'Face Angle (degrees)', 'count': 'Frequency'},
                            color_discrete_sequence=['#A23B72']
                        )
                        fig.add_vline(x=0, line_dash="dash", line_color="red",
                                     annotation_text="Square Face", annotation_position="top")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Face-to-Path Distribution
                        fig = px.histogram(
                            swing_df,
                            x='Face to Path',
                            nbins=30,
                            title="Face-to-Path Distribution",
                            labels={'Face to Path': 'Face-to-Path (degrees)', 'count': 'Frequency'},
                            color_discrete_sequence=['#F18F01']
                        )
                        fig.add_vline(x=0, line_dash="dash", line_color="red",
                                     annotation_text="Straight", annotation_position="top")
                        fig.add_vline(x=2, line_dash="dot", line_color="green",
                                     annotation_text="Ideal Draw", annotation_position="top")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Personalized Coaching Tips
                    st.subheader("💡 Personalized Coaching Tips")
                    
                    # Calculate key statistics
                    avg_club_path = swing_df['Club Path'].mean()
                    avg_face_to_path = swing_df['Face to Path'].mean()
                    consistency_path = swing_df['Club Path'].std()
                    consistency_ftp = swing_df['Face to Path'].std()
                    in_to_out_count = (swing_df['Club Path'] > 0).sum()
                    total_swings = len(swing_df)
                    
                    # Generate coaching tips
                    tips = []
                    
                    # Club Path Analysis
                    if avg_club_path < -3:
                        tips.append({
                            "Priority": "🔴 HIGH",
                            "Issue": "Out-to-In Swing Path",
                            "Current": f"Your average club path is {avg_club_path:.1f}° (out-to-in)",
                            "Impact": "This causes slices, pulls, and loss of distance",
                            "Tips": [
                                "Focus on swinging from inside the ball: Imagine hitting the inside quadrant of the ball",
                                "Practice with alignment sticks: Place one outside your ball-to-target line to encourage an inside approach",
                                "Feel like you're swinging 'out to right field' (for right-handed golfers)",
                                "Work on hip rotation: Ensure your hips clear before impact to allow the club to come from inside",
                                "Try the 'wall drill': Stand close to a wall on your trail side to force an inside path"
                            ]
                        })
                    elif avg_club_path < 0:
                        tips.append({
                            "Priority": "🟡 MEDIUM",
                            "Issue": "Slightly Out-to-In Path",
                            "Current": f"Your average club path is {avg_club_path:.1f}°",
                            "Impact": "Can cause fades and slight loss of distance",
                            "Tips": [
                                "Focus on starting your downswing with your lower body, not your arms",
                                "Practice the 'pump drill': Take practice swings focusing on dropping the club inside",
                                "Check your setup: Ensure your trail shoulder isn't too high, which promotes an outside path",
                                "Work on maintaining your spine angle through impact"
                            ]
                        })
                    elif avg_club_path < 2:
                        tips.append({
                            "Priority": "🟢 GOOD",
                            "Issue": "Neutral to Slightly In-to-Out Path",
                            "Current": f"Your average club path is {avg_club_path:.1f}°",
                            "Impact": "Good foundation! This is close to ideal",
                            "Tips": [
                                "Maintain this path! You're on the right track",
                                "Focus on consistency: Work on repeating this path swing after swing",
                                "Fine-tune your face-to-path relationship for desired ball flight",
                                "Consider slightly increasing to 2-4° for more draw bias if desired"
                            ]
                        })
                    else:
                        tips.append({
                            "Priority": "✅ EXCELLENT",
                            "Issue": "Strong In-to-Out Path",
                            "Current": f"Your average club path is {avg_club_path:.1f}°",
                            "Impact": "Excellent! This promotes draws and maximum distance",
                            "Tips": [
                                "Maintain this path - it's ideal for power and draw shots",
                                "Focus on face control: Ensure your face-to-path relationship matches your target",
                                "Monitor for over-correction: If path gets too extreme (>5°), you may hook the ball"
                            ]
                        })
                    
                    # Face-to-Path Analysis
                    if abs(avg_face_to_path) > 5:
                        tips.append({
                            "Priority": "🔴 HIGH",
                            "Issue": "Extreme Face-to-Path Relationship",
                            "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°",
                            "Impact": f"This causes severe {'hooks' if avg_face_to_path > 0 else 'slices'}",
                            "Tips": [
                                "Work on face angle control: The face should be slightly closed relative to path for a draw",
                                "Practice with impact tape: Check where on the face you're making contact",
                                "Focus on grip: Ensure your grip isn't too strong or too weak",
                                "Try the 'gate drill': Place two tees just wider than your clubhead to practice square contact",
                                "Work on wrist position: Avoid excessive cupping or bowing at impact"
                            ]
                        })
                    elif avg_face_to_path < -2:
                        tips.append({
                            "Priority": "🟡 MEDIUM",
                            "Issue": "Face Open to Path (Fade Bias)",
                            "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°",
                            "Impact": "Promotes fades and slices",
                            "Tips": [
                                "To achieve a draw, close the face slightly relative to your path",
                                "Check your grip: A stronger grip can help close the face",
                                "Focus on rotating your forearms through impact",
                                "Practice with a slightly stronger grip to feel the face closing"
                            ]
                        })
                    elif avg_face_to_path <= 3:
                        tips.append({
                            "Priority": "🟢 GOOD",
                            "Issue": "Good Face-to-Path Relationship",
                            "Current": f"Your average face-to-path is {avg_face_to_path:.1f}°",
                            "Impact": "Promotes straight shots to slight draws",
                            "Tips": [
                                "This is an ideal relationship for consistent ball flight",
                                "Maintain this relationship while working on path consistency",
                                "If you want more draw, aim for 2-3° face-to-path with an in-to-out path"
                            ]
                        })
                    
                    # Consistency Analysis
                    if consistency_path > 5:
                        tips.append({
                            "Priority": "🟡 MEDIUM",
                            "Issue": "Inconsistent Club Path",
                            "Current": f"Your path varies by {consistency_path:.1f}° on average",
                            "Impact": "Inconsistent ball flight and difficulty controlling direction",
                            "Tips": [
                                "Focus on tempo: A consistent tempo leads to a consistent path",
                                "Practice with alignment aids: Use alignment sticks to groove a repeatable path",
                                "Work on your setup: Consistent setup leads to consistent path",
                                "Slow down your swing: Focus on path control before adding speed",
                                "Film your swing: Review video to identify what causes path variations"
                            ]
                        })
                    
                    if consistency_ftp > 4:
                        tips.append({
                            "Priority": "🟡 MEDIUM",
                            "Issue": "Inconsistent Face-to-Path",
                            "Current": f"Your face-to-path varies by {consistency_ftp:.1f}° on average",
                            "Impact": "Inconsistent ball flight patterns",
                            "Tips": [
                                "Work on grip consistency: Same grip every time",
                                "Focus on impact position: Practice hitting the ball with a square face",
                                "Use impact drills: Focus on where the clubface is pointing at impact",
                                "Check your wrist angles: Consistent wrist position leads to consistent face angle"
                            ]
                        })
                    
                    # Display tips
                    for i, tip in enumerate(tips, 1):
                        with st.expander(f"{tip['Priority']} - {tip['Issue']}", expanded=(i == 1)):
                            st.write(f"**Current Performance:** {tip['Current']}")
                            if 'Impact' in tip:
                                st.write(f"**Impact:** {tip['Impact']}")
                            st.write("**Recommendations:**")
                            for j, recommendation in enumerate(tip['Tips'], 1):
                                st.write(f"{j}. {recommendation}")
                    
                    # Summary Statistics Table
                    st.subheader("📊 Swing Path Statistics")
                    path_stats = swing_df[swing_path_cols].describe()
                    st.dataframe(path_stats, use_container_width=True)
                    
                    # Path Consistency by Club Type
                    if 'Club Type' in swing_df.columns:
                        st.subheader("Swing Path by Club Type")
                        club_path_stats = swing_df.groupby('Club Type')[swing_path_cols].agg(['mean', 'std']).round(2)
                        st.dataframe(club_path_stats, use_container_width=True)
                else:
                    st.warning("⚠️ Not enough swing path data available. Please ensure your CSV contains 'Club Path', 'Club Face', and 'Face to Path' columns with valid data.")
            
            # Basic Statistics
            st.header("📈 Statistical Summary")
            
            # Display statistics table
            st.subheader("Numeric Column Statistics")
            stats_df = df[numeric_cols].describe()
            st.dataframe(stats_df, use_container_width=True)
            
            # Allow user to select columns for visualization
            st.header("📊 Custom Visualizations")
            
            # Column selection for charts
            col1, col2 = st.columns(2)
            
            with col1:
                selected_col = st.selectbox(
                    "Select a column for analysis",
                    numeric_cols,
                    help="Choose a numeric column to visualize"
                )
            
            with col2:
                chart_type = st.selectbox(
                    "Select chart type",
                    ["Histogram", "Box Plot", "Line Chart", "Scatter Plot"],
                    help="Choose the type of visualization"
                )
            
            # Create visualizations based on selection
            if selected_col:
                if chart_type == "Histogram":
                    fig = px.histogram(
                        df,
                        x=selected_col,
                        nbins=30,
                        title=f"Distribution of {selected_col}",
                        labels={selected_col: selected_col}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Box Plot":
                    fig = px.box(
                        df,
                        y=selected_col,
                        title=f"Box Plot of {selected_col}",
                        labels={selected_col: selected_col}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Line Chart":
                    # Use index as x-axis for line chart
                    fig = px.line(
                        df,
                        y=selected_col,
                        title=f"Line Chart of {selected_col}",
                        labels={selected_col: selected_col, "index": "Record Number"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Scatter Plot":
                    # For scatter plot, need two columns
                    if len(numeric_cols) > 1:
                        x_col = st.selectbox(
                            "Select X-axis column",
                            [c for c in numeric_cols if c != selected_col],
                            key="scatter_x"
                        )
                        fig = px.scatter(
                            df,
                            x=x_col,
                            y=selected_col,
                            title=f"Scatter Plot: {x_col} vs {selected_col}",
                            labels={x_col: x_col, selected_col: selected_col}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Need at least 2 numeric columns for scatter plot")
            
            # Correlation matrix if multiple numeric columns
            if len(numeric_cols) > 1:
                st.subheader("Correlation Matrix")
                corr_matrix = df[numeric_cols].corr()
                fig = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    title="Correlation Between Numeric Variables",
                    color_continuous_scale="RdBu"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics by column
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
                        "Kurtosis": df[col].kurtosis()
                    }
                    stats_display = pd.DataFrame([col_stats]).T
                    stats_display.columns = ["Value"]
                    st.dataframe(stats_display, use_container_width=True)
        else:
            st.warning("No numeric columns found in the dataset. Please upload a CSV with numeric golf swing metrics.")
        
        # Display column information
        st.header("📋 Column Information")
        col_info = pd.DataFrame({
            "Column Name": df.columns,
            "Data Type": df.dtypes.astype(str),
            "Non-Null Count": df.count().values,
            "Null Count": df.isnull().sum().values
        })
        st.dataframe(col_info, use_container_width=True)
        
        # Session comparison (if multiple files)
        if len(all_dfs) > 1 and 'Source File' in df.columns:
            st.header("📅 Session Comparison")
            
            # Build aggregation dictionary with only available columns
            agg_dict = {}
            metrics = ['Carry Distance', 'Total Distance', 'Club Speed', 'Ball Speed', 'Smash Factor']
            for metric in metrics:
                if metric in df.columns:
                    agg_dict[metric] = 'mean'
            
            if agg_dict:
                session_stats = df.groupby('Source File').agg(agg_dict).reset_index()
            
            if len(session_stats.columns) > 1:
                st.subheader("Average Metrics by Session")
                st.dataframe(session_stats, use_container_width=True)
                
                # Visualize session comparison
                if len(session_stats) > 1:
                    metrics_to_plot = [col for col in session_stats.columns if col != 'Source File']
                    if metrics_to_plot:
                        fig = go.Figure()
                        for metric in metrics_to_plot[:4]:  # Limit to 4 metrics
                            fig.add_trace(go.Scatter(
                                x=session_stats['Source File'],
                                y=session_stats[metric],
                                mode='lines+markers',
                                name=metric
                            ))
                        fig.update_layout(
                            title="Session Comparison",
                            xaxis_title="Session",
                            yaxis_title="Value",
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error reading CSV file(s): {str(e)}")
        st.info("Please make sure your CSV files are properly formatted.")
        st.exception(e)
else:
    st.info("👆 Please upload one or more CSV files to get started.")
    st.markdown("""
    ### Expected CSV Format
    Your CSV file should contain golf swing metrics such as:
    - **Club Speed** - Speed of the club at impact (mph)
    - **Ball Speed** - Speed of the ball after impact (mph)
    - **Launch Angle** - Angle at which the ball launches (degrees)
    - **Spin Rate** - Rate of ball rotation (rpm)
    - **Carry Distance** - Distance ball travels in the air (yards)
    - **Total Distance** - Total distance including roll (yards)
    - **Club Type** - Type of club used
    - And many other swing metrics
    
    The app automatically skips the units row (row 2) in your CSV files.
    """)
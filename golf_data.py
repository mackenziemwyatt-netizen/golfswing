"""
Shared data loading and sidebar logic for the Golf Swing Analyzer.
"""
import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_DATA_DIR = os.path.join(APP_DIR, "saved_data")


def ensure_saved_data_dir():
    os.makedirs(SAVED_DATA_DIR, exist_ok=True)


def get_saved_csv_paths():
    ensure_saved_data_dir()
    paths = []
    for name in os.listdir(SAVED_DATA_DIR):
        if name.lower().endswith(".csv"):
            path = os.path.join(SAVED_DATA_DIR, name)
            if os.path.isfile(path):
                paths.append(path)
    return sorted(paths)


def save_uploaded_file(file) -> str:
    ensure_saved_data_dir()
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
    path = os.path.normpath(path)
    if not path.startswith(os.path.normpath(SAVED_DATA_DIR)):
        return False
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def load_golf_data(file):
    """Load from file-like object."""
    df = pd.read_csv(file, skiprows=[1])
    if "Date" in df.columns:
        try:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        except Exception:
            pass
    df["Source File"] = file.name
    return df


def load_golf_data_from_path(path: str):
    """Load from file path."""
    with open(path, "rb") as f:
        df = pd.read_csv(io.BytesIO(f.read()), skiprows=[1])
    if "Date" in df.columns:
        try:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        except Exception:
            pass
    df["Source File"] = os.path.basename(path)
    return df


def load_all_from_disk():
    """Load all CSV files from saved_data. Returns (list of dfs, concatenated df or None)."""
    all_dfs = []
    for path in get_saved_csv_paths():
        try:
            all_dfs.append(load_golf_data_from_path(path))
        except Exception:
            pass
    if not all_dfs:
        return [], None
    return all_dfs, pd.concat(all_dfs, ignore_index=True)


def render_sidebar_upload_and_files():
    """Render file uploader and manage-saved-files in sidebar. Call from main app only."""
    st.sidebar.header("📁 Data")
    with st.sidebar.expander("Manage saved files", expanded=False):
        saved_paths = get_saved_csv_paths()
        if not saved_paths:
            st.info("No saved files yet. Upload CSV files below.")
        else:
            st.caption("Saved files load automatically.")
            for i, path in enumerate(saved_paths):
                name = os.path.basename(path)
                try:
                    size = os.path.getsize(path)
                    size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
                except OSError:
                    size_str = "?"
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(name)
                    st.caption(size_str)
                with col2:
                    if st.button("🗑️", key=f"del_{i}_{name}", help=f"Delete {name}"):
                        if delete_saved_file(path):
                            st.success("Deleted.")
                            st.rerun()
                        else:
                            st.error("Could not delete.")
    uploaded = st.sidebar.file_uploader(
        "Upload CSV file(s)",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload golf swing CSVs; they are saved and loaded on all pages.",
    )
    return uploaded


def render_sidebar_filters(df_all):
    """Render club/date filters in sidebar and return filtered dataframe."""
    if df_all is None or len(df_all) == 0:
        return None
    st.sidebar.header("🔍 Filters")
    df = df_all.copy()
    if "Club Type" in df.columns:
        club_types = ["All"] + sorted(df["Club Type"].dropna().unique().tolist())
        selected_club = st.sidebar.selectbox("Club Type", club_types)
        if selected_club != "All":
            df = df[df["Club Type"] == selected_club]
    if "Date" in df.columns and df["Date"].notna().any():
        dates = df["Date"].dropna()
        if len(dates) > 0:
            min_date = dates.min()
            max_date = dates.max()
            min_d = min_date.date() if hasattr(min_date, "date") else min_date
            max_d = max_date.date() if hasattr(max_date, "date") else max_date
            date_range = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
            if len(date_range) == 2:
                df = df[(df["Date"] >= pd.Timestamp(date_range[0])) & (df["Date"] <= pd.Timestamp(date_range[1]))]
    return df


def get_data_and_filters():
    """
    Load from disk, handle uploads (caller must pass uploaded_files and rerun after save),
    render sidebar (manage files + filters), return (all_dfs, filtered_df).
    """
    all_dfs, df_all = load_all_from_disk()
    uploaded_files = render_sidebar_upload_and_files()
    if uploaded_files:
        for f in uploaded_files:
            try:
                save_uploaded_file(f)
                f.seek(0)
                all_dfs.append(load_golf_data(f))
            except Exception:
                pass
        if all_dfs:
            df_all = pd.concat(all_dfs, ignore_index=True)
    df = render_sidebar_filters(df_all) if df_all is not None else None
    return all_dfs, df

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


def _unique_practice_dates(df_all):
    """Return sorted list of (date_value, display_label) from Date column."""
    if df_all is None or "Date" not in df_all.columns:
        return []
    dates = df_all["Date"].dropna()
    if len(dates) == 0:
        return []
    try:
        ts = pd.to_datetime(dates, errors="coerce")
        ts = ts.dt.normalize().dt.tz_localize(None)
        unique = sorted(ts.unique())
        return [(d, d.strftime("%b %d, %Y")) for d in unique]
    except Exception:
        return []


def get_selected_session_label():
    """Return the current session selection for display: 'All Sessions' or a formatted date."""
    return st.session_state.get("golf_selected_session_label", "All Sessions")


def render_session_banner():
    """Show selected session prominently at top of page when a single session is selected."""
    label = get_selected_session_label()
    if label != "All Sessions":
        st.info(f"📅 **Viewing session: {label}** — Switch to *All Sessions* in the sidebar to see combined data.")


def render_sidebar_filters(df_all):
    """Render club and session filters in sidebar and return filtered dataframe."""
    if df_all is None or len(df_all) == 0:
        return None
    st.sidebar.header("🔍 Filters")
    df = df_all.copy()

    # Session / date selector: All Sessions or a specific practice date (only when Date column exists)
    if "Date" in df_all.columns:
        practice_dates = _unique_practice_dates(df_all)
        session_options = ["All Sessions"]
        session_values = [None]  # None = no date filter
        for date_val, display_label in practice_dates:
            session_options.append(display_label)
            session_values.append(date_val)
        prev_label = st.session_state.get("golf_selected_session_label", "All Sessions")
        default_idx = 0
        if prev_label in session_options:
            default_idx = session_options.index(prev_label)
        selected_label = st.sidebar.selectbox(
            "📅 Practice session",
            session_options,
            index=default_idx,
            help="Choose a single session to analyze that day only, or All Sessions to combine data.",
        )
        selected_value = session_values[session_options.index(selected_label)]
        st.session_state["golf_selected_session_value"] = selected_value
        st.session_state["golf_selected_session_label"] = selected_label
    else:
        st.session_state["golf_selected_session_value"] = None
        st.session_state["golf_selected_session_label"] = "All Sessions"
        selected_value = None
    if selected_value is not None:
        df["_date_norm"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize().dt.tz_localize(None)
        target = pd.Timestamp(selected_value).normalize() if hasattr(selected_value, "normalize") else pd.Timestamp(selected_value)
        df = df[df["_date_norm"] == target].drop(columns=["_date_norm"], errors="ignore")

    if "Club Type" in df.columns:
        club_types = ["All"] + sorted(df["Club Type"].dropna().unique().tolist())
        selected_club = st.sidebar.selectbox("Club Type", club_types)
        if selected_club != "All":
            df = df[df["Club Type"] == selected_club]
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

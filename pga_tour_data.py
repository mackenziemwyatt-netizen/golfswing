"""
PGA Tour averages from TrackMan (publicly available data).
Used for comparison and gap analysis. Units: mph, deg, rpm, yards.
"""
import pandas as pd

# TrackMan PGA Tour Averages (yards) - exact from official TrackMan PGA Tour Averages
# Columns: Club Type, Club Speed (mph), Attack Angle (deg), Ball Speed (mph), Smash Factor,
#          Launch Angle (deg), Spin Rate (rpm), Max Height (yds), Land Angle (deg), Carry (yds)
PGA_TOUR_AVERAGES = [
    {"Club Type": "Driver", "Club Speed": 115, "Attack Angle": -0.9, "Ball Speed": 171, "Smash Factor": 1.49, "Launch Angle": 10.4, "Spin Rate": 2545, "Max Height": 35, "Land Angle": 39, "Carry Distance": 282},
    {"Club Type": "3-wood", "Club Speed": 110, "Attack Angle": -2.3, "Ball Speed": 169, "Smash Factor": 1.47, "Launch Angle": 9.3, "Spin Rate": 3663, "Max Height": 32, "Land Angle": 44, "Carry Distance": 249},
    {"Club Type": "5-wood", "Club Speed": 106, "Attack Angle": -2.5, "Ball Speed": 156, "Smash Factor": 1.47, "Launch Angle": 9.7, "Spin Rate": 4322, "Max Height": 33, "Land Angle": 48, "Carry Distance": 236},
    {"Club Type": "Hybrid 15-18°", "Club Speed": 102, "Attack Angle": -2.4, "Ball Speed": 149, "Smash Factor": 1.47, "Launch Angle": 10.2, "Spin Rate": 4587, "Max Height": 31, "Land Angle": 49, "Carry Distance": 231},
    {"Club Type": "3 Iron", "Club Speed": 100, "Attack Angle": -2.5, "Ball Speed": 145, "Smash Factor": 1.46, "Launch Angle": 10.3, "Spin Rate": 4404, "Max Height": 30, "Land Angle": 48, "Carry Distance": 218},
    {"Club Type": "4 Iron", "Club Speed": 98, "Attack Angle": -2.9, "Ball Speed": 140, "Smash Factor": 1.44, "Launch Angle": 10.8, "Spin Rate": 4782, "Max Height": 31, "Land Angle": 49, "Carry Distance": 209},
    {"Club Type": "5 Iron", "Club Speed": 96, "Attack Angle": -3.4, "Ball Speed": 135, "Smash Factor": 1.41, "Launch Angle": 11.9, "Spin Rate": 5280, "Max Height": 33, "Land Angle": 50, "Carry Distance": 199},
    {"Club Type": "6 Iron", "Club Speed": 94, "Attack Angle": -3.7, "Ball Speed": 130, "Smash Factor": 1.39, "Launch Angle": 14.0, "Spin Rate": 6204, "Max Height": 32, "Land Angle": 50, "Carry Distance": 188},
    {"Club Type": "7 Iron", "Club Speed": 92, "Attack Angle": -3.9, "Ball Speed": 123, "Smash Factor": 1.34, "Launch Angle": 16.1, "Spin Rate": 7124, "Max Height": 34, "Land Angle": 51, "Carry Distance": 176},
    {"Club Type": "8 Iron", "Club Speed": 89, "Attack Angle": -4.2, "Ball Speed": 118, "Smash Factor": 1.33, "Launch Angle": 17.8, "Spin Rate": 8078, "Max Height": 33, "Land Angle": 51, "Carry Distance": 164},
    {"Club Type": "9 Iron", "Club Speed": 87, "Attack Angle": -4.3, "Ball Speed": 112, "Smash Factor": 1.29, "Launch Angle": 20.0, "Spin Rate": 8793, "Max Height": 32, "Land Angle": 52, "Carry Distance": 152},
    {"Club Type": "PW", "Club Speed": 84, "Attack Angle": -4.7, "Ball Speed": 104, "Smash Factor": 1.24, "Launch Angle": 23.7, "Spin Rate": 9316, "Max Height": 32, "Land Angle": 52, "Carry Distance": 142},
]

# DataFrame for easy lookup
PGA_TOUR_DF = pd.DataFrame(PGA_TOUR_AVERAGES)

# Metric key -> (our CSV column name, unit for display)
PGA_METRIC_COLUMNS = [
    ("Club Speed", "Club Speed", "mph"),
    ("Attack Angle", "Attack Angle", "deg"),
    ("Ball Speed", "Ball Speed", "mph"),
    ("Smash Factor", "Smash Factor", ""),
    ("Launch Angle", "Launch Angle", "deg"),
    ("Spin Rate", "Spin Rate", "rpm"),
    ("Max Height", "Apex Height", "yds"),  # TrackMan "Max Height" = Apex Height
    ("Land Angle", "Land Angle", "deg"),
    ("Carry Distance", "Carry Distance", "yds"),
]


def map_user_club_to_pga(user_club_type: str) -> str:
    """Map user's Club Type string to closest PGA Tour table row key (Club Type)."""
    if not user_club_type:
        return "Driver"
    ct = str(user_club_type).strip().lower()
    if "driver" in ct or "1 wood" in ct:
        return "Driver"
    if "3 wood" in ct or "3-wood" in ct or "3 wood" in ct:
        return "3-wood"
    if "5 wood" in ct or "5-wood" in ct:
        return "5-wood"
    if "hybrid" in ct:
        return "Hybrid 15-18°"
    if "pitch" in ct or ct == "pw":
        return "PW"
    for n in range(3, 10):
        if f"{n} iron" in ct or f"{n}-iron" in ct or ct == f"{n} iron":
            return f"{n} Iron"
    return "Driver"


def get_pga_row_for_club(club_type: str) -> dict:
    """Return PGA Tour averages row for the given club type (PGA table key)."""
    row = PGA_TOUR_DF[PGA_TOUR_DF["Club Type"] == club_type]
    if len(row) == 0:
        row = PGA_TOUR_DF[PGA_TOUR_DF["Club Type"] == "Driver"]
    return row.iloc[0].to_dict() if len(row) > 0 else {}


def pct_diff_color(pct_diff: float) -> str:
    """Return color class: green <=10%, yellow 10-25%, red >25% (by absolute % off tour)."""
    if pct_diff is None or (isinstance(pct_diff, float) and pd.isna(pct_diff)):
        return "gray"
    abs_pct = abs(pct_diff)
    if abs_pct <= 10:
        return "green"
    if abs_pct <= 25:
        return "yellow"
    return "red"


def pct_diff(my_val, tour_val):
    """Percentage difference (my - tour) / tour * 100. Handles zero and NaN."""
    if tour_val is None or (isinstance(tour_val, (int, float)) and (pd.isna(tour_val) or tour_val == 0)):
        return None
    if my_val is None or (isinstance(my_val, (int, float)) and pd.isna(my_val)):
        return None
    return (float(my_val) - float(tour_val)) / float(tour_val) * 100


def build_comparison_by_club(df: pd.DataFrame) -> list:
    """
    For each club type in df, compute my avg vs PGA Tour and % diff.
    Returns list of dicts: club_type, pga_club_key, my_avgs, tour_avgs, pct_diffs, score (avg abs % gap).
    """
    if "Club Type" not in df.columns or df.empty:
        return []
    results = []
    for club in df["Club Type"].dropna().unique().tolist():
        sub = df[df["Club Type"] == club]
        pga_key = map_user_club_to_pga(club)
        tour = get_pga_row_for_club(pga_key)
        my_avgs = {}
        tour_avgs = {}
        pct_diffs = {}
        gaps = []
        for display_name, col, _ in PGA_METRIC_COLUMNS:
            if col not in df.columns:
                continue
            tour_val = tour.get(display_name)
            if tour_val is None:
                continue
            my_val = sub[col].mean()
            my_avgs[display_name] = my_val
            tour_avgs[display_name] = tour_val
            d = pct_diff(my_val, tour_val)
            pct_diffs[display_name] = d
            if d is not None:
                gaps.append(abs(d))
        avg_gap = sum(gaps) / len(gaps) if gaps else 100
        results.append({
            "club_type": club,
            "pga_club_key": pga_key,
            "my_avgs": my_avgs,
            "tour_avgs": tour_avgs,
            "pct_diffs": pct_diffs,
            "avg_gap_pct": avg_gap,
            "n_shots": len(sub),
        })
    return results


def gap_analysis_ordered(comparison_list: list) -> tuple:
    """Return (closest to tour first, need most work first)."""
    if not comparison_list:
        return [], []
    by_gap = sorted(comparison_list, key=lambda x: x["avg_gap_pct"])
    closest = by_gap[:5]
    need_work = list(reversed(by_gap))[:5]
    return closest, need_work


# TrackMan-style orange/white table CSS
PGA_TABLE_CSS = """
<style>
.pga-table-wrap { background: #e85d04; padding: 1rem 1.25rem; border-radius: 8px; margin: 1rem 0; }
.pga-table-wrap table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 6px; overflow: hidden; }
.pga-table-wrap th { background: #d35400; color: #fff; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; padding: 0.5rem 0.4rem; text-align: center; }
.pga-table-wrap td { padding: 0.45rem 0.4rem; font-size: 0.8rem; text-align: center; color: #1a1d21; border-bottom: 1px solid #f0f0f0; }
.pga-table-wrap tr:nth-child(even) { background: #fef9f6; }
.pga-table-wrap tr:hover { background: #fff5ee; }
.pga-table-wrap .col-club { text-align: left; font-weight: 600; padding-left: 0.6rem; }
.pga-table-wrap .gap-green { background: #d4edda !important; color: #155724; }
.pga-table-wrap .gap-yellow { background: #fff3cd !important; color: #856404; }
.pga-table-wrap .gap-red { background: #f8d7da !important; color: #721c24; }
.pga-table-wrap .gap-gray { background: #e9ecef !important; color: #6c757d; }
.pga-gap-box { display: inline-block; padding: 0.5rem 0.75rem; margin: 0.25rem; border-radius: 6px; font-size: 0.85rem; }
.pga-gap-closest { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.pga-gap-work { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
"""


def _fmt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if isinstance(v, (int, float)):
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        if abs(v) >= 1 or v == 0:
            return f"{v:.1f}"
        return f"{v:.2f}"
    return str(v)


def build_pga_comparison_table_html(comparison_list: list, metrics_to_show: list = None) -> str:
    """
    Build orange/white TrackMan-style table HTML: Club Type, then each metric with My | PGA columns and color coding.
    comparison_list from build_comparison_by_club. metrics_to_show = list of display names from PGA_METRIC_COLUMNS.
    """
    if metrics_to_show is None:
        metrics_to_show = [m[0] for m in PGA_METRIC_COLUMNS]
    rows = []
    header_cells = ["Club Type"]
    for display_name, _, unit in PGA_METRIC_COLUMNS:
        if display_name not in metrics_to_show:
            continue
        u = f" ({unit})" if unit else ""
        header_cells.append(f"My {display_name}{u}")
        header_cells.append(f"PGA {display_name}{u}")
    rows.append("<tr>" + "".join(f"<th>{h}</th>" for h in header_cells) + "</tr>")
    for c in comparison_list:
        cells = [f'<td class="col-club">{c["club_type"]}</td>']
        for display_name, col, unit in PGA_METRIC_COLUMNS:
            if display_name not in metrics_to_show:
                continue
            my_val = c["my_avgs"].get(display_name)
            tour_val = c["tour_avgs"].get(display_name)
            pct = c["pct_diffs"].get(display_name)
            color_class = pct_diff_color(pct) if pct is not None else "gray"
            cells.append(f'<td class="gap-{color_class}">{_fmt(my_val)}</td>')
            cells.append(f'<td>{_fmt(tour_val)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="pga-table-wrap"><table><thead>' + rows[0] + "</thead><tbody>" + "".join(rows[1:]) + "</tbody></table></div>"


def build_pga_reference_only_html() -> str:
    """Build orange/white table with PGA Tour averages only (no My column)."""
    header = ["Club Type"] + [f"{m[0]} ({m[2]})" if m[2] else m[0] for m in PGA_METRIC_COLUMNS]
    out = ["<tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr>"]
    for r in PGA_TOUR_AVERAGES:
        cells = [f'<td class="col-club">{r["Club Type"]}</td>']
        for m in PGA_METRIC_COLUMNS:
            cells.append(f"<td>{_fmt(r.get(m[0]))}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="pga-table-wrap"><table><thead>' + out[0] + "</thead><tbody>" + "".join(out[1:]) + "</tbody></table></div>"

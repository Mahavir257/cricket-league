import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd

st.set_page_config(
    page_title="Company Cricket League",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── IPL-Style Black & Orange Theme ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
.stApp { background: #0a0a0a; }
section[data-testid="stSidebar"] { background: #111111 !important; border-right: 1px solid #FF6B00; }
section[data-testid="stSidebar"] .stRadio label { color: #cccccc !important; font-family: 'Barlow', sans-serif; }
section[data-testid="stSidebar"] .stRadio label:hover { color: #FF6B00 !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span { color: #cccccc !important; }
section[data-testid="stSidebar"] .stMetric { background: #1a1a1a; border-radius: 8px; padding: 6px 10px; border: 1px solid #2a2a2a; }
section[data-testid="stSidebar"] [data-testid="stMetricValue"] { color: #FF6B00 !important; font-family: 'Barlow Condensed', sans-serif; font-size: 22px !important; }
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #888 !important; font-size: 11px !important; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif !important; color: #ffffff !important; letter-spacing: 0.5px; }
p, li, span, label, div { color: #cccccc; }
[data-testid="stDataFrame"] { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 10px !important; }
.stTextInput input, .stSelectbox select, .stDateInput input, .stTimeInput input,
.stNumberInput input, .stTextArea textarea {
    background: #1a1a1a !important; border: 1px solid #333 !important;
    color: #fff !important; border-radius: 8px !important;
}
.stButton > button {
    font-family: 'Barlow', sans-serif !important; font-weight: 600 !important;
    border-radius: 8px !important; border: 1px solid #FF6B00 !important;
    background: transparent !important; color: #FF6B00 !important; transition: all 0.2s !important;
}
.stButton > button:hover { background: #FF6B00 !important; color: #000 !important; transform: translateY(-1px) !important; }
.stButton > button[kind="primary"] { background: #FF6B00 !important; color: #000 !important; font-weight: 700 !important; }
.stButton > button[kind="primary"]:hover { background: #ff8c00 !important; }
[data-testid="stForm"] { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 12px !important; padding: 16px !important; }
[data-testid="stExpander"] { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary { color: #fff !important; }
.stTabs [data-baseweb="tab-list"] { background: #111 !important; border-bottom: 2px solid #FF6B00 !important; gap: 4px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #888 !important; font-family: 'Barlow', sans-serif !important; font-weight: 500 !important; border-radius: 8px 8px 0 0 !important; padding: 8px 16px !important; }
.stTabs [aria-selected="true"] { background: #FF6B00 !important; color: #000 !important; font-weight: 700 !important; }
hr { border-color: #2a2a2a !important; }
.stSuccess { background: #0d2818 !important; border-left: 4px solid #25a85e !important; color: #25a85e !important; }
.stWarning { background: #2a1800 !important; border-left: 4px solid #FF6B00 !important; }
.stError   { background: #2a0d0d !important; border-left: 4px solid #ff3333 !important; }
[data-testid="stSelectbox"] > div > div { background: #1a1a1a !important; border: 1px solid #333 !important; color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# ── Data persistence ─────────────────────────────────────────────────────────
DATA_FILE = "cricket_league_data.json"
DEFAULT_DATA = {
    "league_name": "Company Cricket League",
    "league_edition": "IPL Season 2026",
    "league_logo": "🏏",
    "teams": [], "players": [], "matches": [], "activity_log": [],
    "next_team_id": 1, "next_player_id": 1, "next_match_id": 1,
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.db, f, indent=2, default=str)

def log_activity(action, detail, icon="🏏"):
    db["activity_log"].insert(0, {"time": datetime.now().strftime("%d %b, %H:%M"), "action": action, "detail": detail, "icon": icon})
    db["activity_log"] = db["activity_log"][:30]

def init():
    if "db" not in st.session_state:
        st.session_state.db = load_data()
    if "live_match_id" not in st.session_state:
        st.session_state.live_match_id = None

init()
db = st.session_state.db

# ── Helpers ──────────────────────────────────────────────────────────────────
def team_by_id(tid):  return next((t for t in db["teams"]   if t["id"] == tid), None)
def match_by_id(mid): return next((m for m in db["matches"] if m["id"] == mid), None)
def fmt_ov(b):        return f"{b//6}.{b%6}"
def calc_sr(r, b):    return round(r/b*100, 1) if b else 0.0
def calc_eco(r, b):   return round(r/(b/6), 2) if b else 0.0

def calc_nrr(team):
    scored = conceded = ob = ow = 0
    for m in db["matches"]:
        if m["status"] != "completed" or not m.get("inn") or not m["inn"][0] or not m["inn"][1]: continue
        if m["teamA"] == team["id"]:
            scored += m["inn"][0].get("runs", 0); ob += m["inn"][0].get("balls", 0)
            conceded += m["inn"][1].get("runs", 0); ow += m["inn"][1].get("balls", 0)
        elif m["teamB"] == team["id"]:
            scored += m["inn"][1].get("runs", 0); ob += m["inn"][1].get("balls", 0)
            conceded += m["inn"][0].get("runs", 0); ow += m["inn"][0].get("balls", 0)
    rf = round(scored/(ob/6), 3) if ob else 0
    ra = round(conceded/(ow/6), 3) if ow else 0
    return round(rf - ra, 3)

ROLE_LABELS  = {"bat": "Batsman", "bowl": "Bowler", "all": "All-rounder", "wk": "Wicket-keeper"}
ROLE_COLORS  = {"bat": "#0d2035", "bowl": "#2a1000", "all": "#0d2018", "wk": "#1a0d2a"}
ROLE_TCOLORS = {"bat": "#4da6ff", "bowl": "#FF6B00", "all": "#25a85e",  "wk": "#b366ff"}

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    logo = db.get("league_logo", "🏏")
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#FF6B00,#cc4400);border-radius:12px;
    padding:16px;margin-bottom:16px;text-align:center;'>
        <div style='font-size:36px;'>{logo}</div>
        <div style='font-family:Barlow Condensed,sans-serif;font-size:20px;font-weight:800;
        color:#fff;margin-top:4px;letter-spacing:1px;'>{db["league_name"]}</div>
        <div style='font-size:11px;color:#ffd4b0;margin-top:2px;'>{db["league_edition"]}</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "🏠 Dashboard", "📅 Schedule", "📊 Points Table",
        "👥 Teams", "🧑 Players", "🎮 Live Scorecard",
        "➕ Manage", "⚙️ Settings"
    ], label_visibility="collapsed")

    st.markdown("---")
    live_count = len([m for m in db["matches"] if m["status"] == "live"])
    total      = len(db["matches"])
    done       = len([m for m in db["matches"] if m["status"] == "completed"])
    upcoming   = len([m for m in db["matches"] if m["status"] == "upcoming"])
    c1, c2 = st.columns(2)
    c1.metric("Teams",   len(db["teams"]))
    c2.metric("Players", len(db["players"]))
    c1.metric("Matches", total)
    c2.metric("Done",    done)
    if live_count:
        st.markdown(f"""<div style='background:#3a0000;border:1px solid #ff3333;border-radius:8px;
        padding:8px;text-align:center;margin-top:8px;'>
        <span style='color:#ff4444;font-weight:700;font-size:13px;'>🔴 {live_count} LIVE NOW</span></div>""", unsafe_allow_html=True)
    if upcoming:
        st.markdown(f"""<div style='background:#1a1000;border:1px solid #FF6B00;border-radius:8px;
        padding:8px;text-align:center;margin-top:6px;'>
        <span style='color:#FF6B00;font-weight:600;font-size:12px;'>⏳ {upcoming} upcoming</span></div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":

    # Hero Banner
    st.markdown(f"""
    <div style='background:#111;border:2px solid #FF6B00;border-radius:16px;
    padding:28px 32px;margin-bottom:24px;position:relative;overflow:hidden;'>
        <div style='position:absolute;right:24px;top:50%;transform:translateY(-50%);
        font-size:80px;opacity:.12;'>{logo}</div>
        <div style='display:flex;align-items:center;gap:18px;'>
            <div style='font-size:52px;'>{logo}</div>
            <div>
                <div style='font-family:Barlow Condensed,sans-serif;font-size:36px;font-weight:800;
                color:#FF6B00;letter-spacing:1px;line-height:1;'>{db["league_name"].upper()}</div>
                <div style='font-size:14px;color:#888;margin-top:6px;'>
                    {db["league_edition"]} &nbsp;·&nbsp;
                    <span style='color:#FF6B00;font-weight:600;'>{len(db["teams"])} Teams</span> &nbsp;·&nbsp;
                    <span style='color:#FF6B00;font-weight:600;'>{len(db["players"])} Players</span> &nbsp;·&nbsp;
                    <span style='color:#FF6B00;font-weight:600;'>{total} Matches</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stat row
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, num, lbl, clr in [
        (c1, len(db["teams"]),   "Teams",     "#FF6B00"),
        (c2, len(db["players"]), "Players",   "#ffd700"),
        (c3, total,              "Matches",   "#4da6ff"),
        (c4, done,               "Completed", "#25a85e"),
        (c5, live_count,         "Live Now",  "#ff3333"),
    ]:
        col.markdown(f"""<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;
        padding:16px;text-align:center;'>
        <div style='font-family:Barlow Condensed,sans-serif;font-size:34px;font-weight:800;color:{clr};'>{num}</div>
        <div style='font-size:11px;color:#555;margin-top:2px;text-transform:uppercase;letter-spacing:.05em;'>{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<h3 style='color:#FF6B00;'>⚡ Live & Recent Matches</h3>", unsafe_allow_html=True)
        shown = ([m for m in db["matches"] if m["status"] == "live"] +
                 [m for m in db["matches"] if m["status"] == "completed"][-3:] +
                 [m for m in db["matches"] if m["status"] == "upcoming"][:2])
        if not shown:
            st.markdown("""<div style='background:#111;border:1px solid #2a2a2a;border-radius:12px;
            padding:20px;text-align:center;color:#444;'>No matches yet. Schedule in Manage →</div>""", unsafe_allow_html=True)
        else:
            for m in shown[:6]:
                ta = team_by_id(m["teamA"]); tb = team_by_id(m["teamB"])
                if not ta or not tb: continue
                i0 = (m.get("inn") or [None, None])[0]
                i1 = (m.get("inn") or [None, None])[1] if m.get("inn") and len(m["inn"]) > 1 else None
                sc  = {"live": "#ff3333", "completed": "#25a85e", "upcoming": "#FF6B00"}[m["status"]]
                sb  = {"live": "#3a0000", "completed": "#0d2018", "upcoming": "#1a1000"}[m["status"]]
                sl  = {"live": "🔴 LIVE", "completed": "✅ DONE", "upcoming": "⏳ UPCOMING"}[m["status"]]
                sa  = f"<span style='font-family:Barlow Condensed,sans-serif;font-size:26px;font-weight:800;color:{ta['color']};'>{i0['runs']}/{i0['wickets']}</span><span style='font-size:11px;color:#555;margin-left:4px;'>{fmt_ov(i0['balls'])} ov</span>" if i0 else "<span style='color:#333;font-size:18px;'>—</span>"
                sb2 = f"<span style='font-family:Barlow Condensed,sans-serif;font-size:26px;font-weight:800;color:{tb['color']};'>{i1['runs']}/{i1['wickets']}</span><span style='font-size:11px;color:#555;margin-left:4px;'>{fmt_ov(i1['balls'])} ov</span>" if i1 else "<span style='color:#333;font-size:18px;'>—</span>"
                st.markdown(f"""
                <div style='background:#111;border:1px solid #2a2a2a;border-left:4px solid {sc};
                border-radius:12px;padding:14px 16px;margin-bottom:8px;'>
                    <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;'>
                        <span style='background:{sb};color:{sc};padding:2px 10px;border-radius:6px;
                        font-size:11px;font-weight:700;font-family:Barlow Condensed,sans-serif;letter-spacing:.5px;'>{sl}</span>
                        <span style='font-size:11px;color:#444;'>{m.get("date","")} · {m.get("venue","")} · {m.get("overs",20)} ov</span>
                    </div>
                    <div style='display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;'>
                        <div>
                            <div style='font-family:Barlow Condensed,sans-serif;font-size:15px;font-weight:800;color:{ta["color"]};margin-bottom:4px;'>{ta["name"].upper()}</div>
                            {sa}
                        </div>
                        <div style='font-family:Barlow Condensed,sans-serif;font-size:18px;font-weight:800;color:#2a2a2a;text-align:center;'>VS</div>
                        <div style='text-align:right;'>
                            <div style='font-family:Barlow Condensed,sans-serif;font-size:15px;font-weight:800;color:{tb["color"]};margin-bottom:4px;'>{tb["name"].upper()}</div>
                            {sb2}
                        </div>
                    </div>
                    {f'<div style="font-size:13px;color:#FF6B00;font-weight:600;margin-top:6px;">{m["result"]}</div>' if m.get("result") else ""}
                </div>
                """, unsafe_allow_html=True)

        # Charts
        st.markdown("<h3 style='color:#FF6B00;margin-top:16px;'>📊 Run Scoring Chart</h3>", unsafe_allow_html=True)
        completed = [m for m in db["matches"] if m["status"] == "completed" and m.get("inn") and m["inn"][0]]
        if completed:
            rows = []
            for m in completed[-8:]:
                ta2 = team_by_id(m["teamA"]); tb2 = team_by_id(m["teamB"])
                if not ta2 or not tb2: continue
                label = f"{ta2['name'][:6]} v {tb2['name'][:6]}"
                ra = m["inn"][0].get("runs", 0) if m["inn"][0] else 0
                rb = m["inn"][1].get("runs", 0) if m["inn"] and m["inn"][1] else 0
                rows.append({"Match": label, ta2["name"]: ra, tb2["name"]: rb})
            if rows:
                df_c = pd.DataFrame(rows).set_index("Match")
                st.bar_chart(df_c, color=["#FF6B00", "#ffd700"], height=220)
        else:
            st.markdown("""<div style='background:#111;border:1px solid #2a2a2a;border-radius:10px;
            padding:16px;text-align:center;color:#444;font-size:13px;'>Charts appear after matches are completed</div>""", unsafe_allow_html=True)

    with col_right:
        # Standings
        st.markdown("<h3 style='color:#FF6B00;'>🏆 Standings</h3>", unsafe_allow_html=True)
        if db["teams"]:
            ranked = sorted(db["teams"], key=lambda t: (-t.get("pts", 0), -calc_nrr(t)))
            medals = ["🥇", "🥈", "🥉"]
            for i, t in enumerate(ranked[:6]):
                nrr = calc_nrr(t)
                q   = " <span style='font-size:9px;background:#FF6B00;color:#000;padding:1px 5px;border-radius:4px;font-weight:700;'>Q</span>" if i < 2 else ""
                st.markdown(f"""
                <div style='background:#111;border:1px solid {"#FF6B00" if i<2 else "#1a1a1a"};
                border-radius:10px;padding:9px 12px;margin-bottom:5px;display:flex;align-items:center;gap:8px;'>
                    <span style='font-size:18px;min-width:24px;'>{medals[i] if i<3 else str(i+1)}</span>
                    <span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:{t["color"]};flex-shrink:0;'></span>
                    <span style='flex:1;font-weight:600;color:#fff;font-size:13px;'>{t["name"]}{q}</span>
                    <span style='font-family:Barlow Condensed,sans-serif;font-size:20px;font-weight:800;color:#FF6B00;'>{t.get("pts",0)}</span>
                    <span style='font-size:10px;color:{"#25a85e" if nrr>=0 else "#ff4444"};min-width:50px;text-align:right;'>
                        {("+" if nrr>=0 else "")+str(nrr)} NRR
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""<div style='color:#444;font-size:13px;padding:12px 0;'>No teams yet</div>""", unsafe_allow_html=True)

        # Top Performers
        st.markdown("<h3 style='color:#FF6B00;margin-top:16px;'>⭐ Top Performers</h3>", unsafe_allow_html=True)
        pt1, pt2 = st.tabs(["🏏 Batting", "🎳 Bowling"])
        with pt1:
            top_bat = sorted(db["players"], key=lambda p: p.get("runs", 0), reverse=True)[:5]
            if top_bat:
                for p in top_bat:
                    t = team_by_id(p["team"]); tc = t["color"] if t else "#FF6B00"
                    st.markdown(f"""<div style='display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid #1a1a1a;'>
                    <div style='width:26px;height:26px;border-radius:50%;background:{tc};display:flex;align-items:center;
                    justify-content:center;font-family:Barlow Condensed,sans-serif;font-size:12px;font-weight:700;color:#000;flex-shrink:0;'>{p["name"][0]}</div>
                    <div style='flex:1;'><div style='font-size:13px;font-weight:500;color:#fff;'>{p["name"]}</div>
                    <div style='font-size:10px;color:#555;'>{(t or {}).get("name","")}</div></div>
                    <div style='font-family:Barlow Condensed,sans-serif;font-size:20px;font-weight:800;color:#FF6B00;'>{p.get("runs",0)}</div>
                    <div style='font-size:10px;color:#555;'>runs</div></div>""", unsafe_allow_html=True)
            else:
                st.caption("No batting data yet")
        with pt2:
            top_bwl = sorted(db["players"], key=lambda p: p.get("wkts", 0), reverse=True)[:5]
            if top_bwl:
                for p in top_bwl:
                    t = team_by_id(p["team"]); tc = t["color"] if t else "#FF6B00"
                    st.markdown(f"""<div style='display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid #1a1a1a;'>
                    <div style='width:26px;height:26px;border-radius:50%;background:{tc};display:flex;align-items:center;
                    justify-content:center;font-family:Barlow Condensed,sans-serif;font-size:12px;font-weight:700;color:#000;flex-shrink:0;'>{p["name"][0]}</div>
                    <div style='flex:1;'><div style='font-size:13px;font-weight:500;color:#fff;'>{p["name"]}</div>
                    <div style='font-size:10px;color:#555;'>{(t or {}).get("name","")}</div></div>
                    <div style='font-family:Barlow Condensed,sans-serif;font-size:20px;font-weight:800;color:#ffd700;'>{p.get("wkts",0)}</div>
                    <div style='font-size:10px;color:#555;'>wkts</div></div>""", unsafe_allow_html=True)
            else:
                st.caption("No bowling data yet")

        # Activity Feed
        st.markdown("<h3 style='color:#FF6B00;margin-top:16px;'>📋 Recent Activity</h3>", unsafe_allow_html=True)
        activities = db.get("activity_log", [])
        if activities:
            for act in activities[:8]:
                st.markdown(f"""<div style='display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #1a1a1a;align-items:flex-start;'>
                <div style='font-size:15px;flex-shrink:0;'>{act.get("icon","🏏")}</div>
                <div><div style='font-size:12.5px;color:#ccc;'><strong style='color:#fff;'>{act["action"]}</strong> — {act["detail"]}</div>
                <div style='font-size:10px;color:#444;margin-top:1px;'>{act["time"]}</div></div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#444;font-size:12px;padding:10px 0;'>Activity appears as you manage the league</div>", unsafe_allow_html=True)

        # Next Match Countdown
        upcoming_matches = [m for m in db["matches"] if m["status"] == "upcoming" and m.get("date")]
        if upcoming_matches:
            st.markdown("<h3 style='color:#FF6B00;margin-top:16px;'>⏳ Next Match</h3>", unsafe_allow_html=True)
            nm = sorted(upcoming_matches, key=lambda m: m.get("date", "9999"))[0]
            ta2 = team_by_id(nm["teamA"]); tb2 = team_by_id(nm["teamB"])
            if ta2 and tb2:
                try:
                    days_left = (datetime.strptime(nm["date"], "%Y-%m-%d") - datetime.now()).days
                    cdtxt = "Today!" if days_left == 0 else (f"In {days_left} day{'s' if days_left!=1 else ''}" if days_left > 0 else "Overdue")
                    cdclr = "#25a85e" if days_left == 0 else ("#FF6B00" if days_left <= 3 else "#4da6ff")
                except Exception:
                    cdtxt = nm.get("date", ""); cdclr = "#FF6B00"
                st.markdown(f"""<div style='background:#111;border:1px solid #FF6B00;border-radius:12px;padding:14px;'>
                <div style='font-family:Barlow Condensed,sans-serif;font-size:22px;font-weight:800;color:{cdclr};margin-bottom:6px;'>{cdtxt}</div>
                <div style='font-size:14px;color:#fff;font-weight:600;'>
                    <span style='color:{ta2["color"]};'>{ta2["name"]}</span>
                    <span style='color:#333;'> vs </span>
                    <span style='color:{tb2["color"]};'>{tb2["name"]}</span>
                </div>
                <div style='font-size:11px;color:#555;margin-top:4px;'>{nm.get("date","")} · {nm.get("time","")} · {nm.get("venue","")}</div>
                </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📅 Schedule":
    st.markdown("<h2>📅 Match Schedule</h2>", unsafe_allow_html=True)
    f = st.selectbox("Filter", ["All", "Upcoming", "Live", "Completed"])
    matches = db["matches"] if f == "All" else [m for m in db["matches"] if m["status"] == f.lower()]
    if not matches:
        st.info("No matches found.")
    else:
        by_date = {}
        for m in sorted(matches, key=lambda x: x.get("date", "9999")):
            by_date.setdefault(m.get("date", "No date"), []).append(m)
        for dt, ms in by_date.items():
            try: dlbl = datetime.strptime(dt, "%Y-%m-%d").strftime("%A, %d %B %Y")
            except Exception: dlbl = dt
            st.markdown(f"<div style='font-family:Barlow Condensed,sans-serif;font-size:16px;font-weight:700;color:#FF6B00;text-transform:uppercase;letter-spacing:.5px;margin:12px 0 8px;'>{dlbl}</div>", unsafe_allow_html=True)
            for m in ms:
                ta = team_by_id(m["teamA"]); tb = team_by_id(m["teamB"])
                if not ta or not tb: continue
                i0 = (m.get("inn") or [None, None])[0]
                i1 = (m.get("inn") or [None, None])[1] if m.get("inn") and len(m["inn"]) > 1 else None
                sc = {"live":"#ff3333","completed":"#25a85e","upcoming":"#FF6B00"}[m["status"]]
                sl = {"live":"🔴 LIVE","completed":"✅ DONE","upcoming":"⏳ UPCOMING"}[m["status"]]
                sb = {"live":"#3a0000","completed":"#0d2018","upcoming":"#1a1000"}[m["status"]]
                st.markdown(f"""
                <div style='background:#111;border:1px solid #2a2a2a;border-left:4px solid {sc};
                border-radius:12px;padding:14px 18px;margin-bottom:8px;'>
                    <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                        <span style='background:{sb};color:{sc};padding:2px 10px;border-radius:6px;font-size:11px;font-weight:700;'>{sl}</span>
                        <span style='font-size:11px;color:#444;'>{m.get("time","")} · {m.get("venue","")} · {m.get("overs",20)} ov</span>
                    </div>
                    <div style='display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;'>
                        <div>
                            <div style='font-family:Barlow Condensed,sans-serif;font-size:17px;font-weight:800;color:{ta["color"]};'>{ta["name"].upper()}</div>
                            <div style='font-family:Barlow Condensed,sans-serif;font-size:24px;font-weight:800;color:#fff;'>{str(i0["runs"])+"/"+str(i0["wickets"]) if i0 else "—"}</div>
                        </div>
                        <div style='font-family:Barlow Condensed,sans-serif;font-size:18px;font-weight:800;color:#2a2a2a;'>VS</div>
                        <div style='text-align:right;'>
                            <div style='font-family:Barlow Condensed,sans-serif;font-size:17px;font-weight:800;color:{tb["color"]};'>{tb["name"].upper()}</div>
                            <div style='font-family:Barlow Condensed,sans-serif;font-size:24px;font-weight:800;color:#fff;'>{str(i1["runs"])+"/"+str(i1["wickets"]) if i1 else "—"}</div>
                        </div>
                    </div>
                    {f'<div style="font-size:13px;color:#FF6B00;font-weight:600;margin-top:6px;">{m["result"]}</div>' if m.get("result") else ""}
                </div>
                """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  POINTS TABLE
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📊 Points Table":
    st.markdown("<h2>📊 Points Table</h2>", unsafe_allow_html=True)
    if not db["teams"]:
        st.info("Add teams first in Manage.")
    else:
        rows = sorted(db["teams"], key=lambda t: (-t.get("pts", 0), -calc_nrr(t)))
        medals = ["🥇", "🥈", "🥉"]
        hdr = "<div style='background:#FF6B00;border-radius:10px 10px 0 0;padding:10px 14px;display:grid;grid-template-columns:40px 1fr 50px 50px 50px 50px 60px 70px;gap:4px;'>"
        for h in ["#", "Team", "P", "W", "L", "T", "Pts", "NRR"]:
            hdr += f"<span style='font-family:Barlow Condensed,sans-serif;font-size:13px;font-weight:700;color:#000;text-align:center;'>{h}</span>"
        hdr += "</div>"
        body = ""
        for i, t in enumerate(rows):
            nrr = calc_nrr(t)
            bg  = "#1a1a1a" if i % 2 == 0 else "#111"
            br  = "border:1px solid #FF6B00;" if i < 2 else ""
            rr  = "border-radius:0 0 10px 10px;" if i == len(rows)-1 else ""
            body += f"""<div style='background:{bg};{br}padding:10px 14px;display:grid;
            grid-template-columns:40px 1fr 50px 50px 50px 50px 60px 70px;gap:4px;align-items:center;{rr}'>
                <span style='font-size:18px;text-align:center;'>{medals[i] if i<3 else str(i+1)}</span>
                <span>
                    <span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{t["color"]};margin-right:5px;'></span>
                    <span style='font-weight:600;color:#fff;font-size:13px;'>{t["name"]}</span>
                    {' <span style="font-size:9px;background:#FF6B00;color:#000;padding:1px 5px;border-radius:4px;font-weight:700;">Q</span>' if i<2 else ""}
                </span>
                <span style='text-align:center;color:#ccc;font-size:13px;'>{t.get("played",0)}</span>
                <span style='text-align:center;color:#25a85e;font-size:13px;font-weight:600;'>{t.get("won",0)}</span>
                <span style='text-align:center;color:#ff4444;font-size:13px;'>{t.get("lost",0)}</span>
                <span style='text-align:center;color:#888;font-size:13px;'>{t.get("tied",0)}</span>
                <span style='text-align:center;font-family:Barlow Condensed,sans-serif;font-size:20px;font-weight:800;color:#FF6B00;'>{t.get("pts",0)}</span>
                <span style='text-align:center;font-size:13px;font-weight:600;color:{"#25a85e" if nrr>=0 else "#ff4444"};'>{("+" if nrr>=0 else "")+str(nrr)}</span>
            </div>"""
        st.markdown(hdr + body, unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px;color:#555;margin-top:8px;'>Top 2 teams qualify for finals · NRR used as tiebreaker</div>", unsafe_allow_html=True)
        if len(db["teams"]) > 1:
            st.markdown("<h3 style='margin-top:20px;color:#FF6B00;'>📊 Points Comparison</h3>", unsafe_allow_html=True)
            df_pts = pd.DataFrame([{"Team": t["name"], "Points": t.get("pts",0)} for t in db["teams"]])
            st.bar_chart(df_pts.set_index("Team"), color="#FF6B00", height=250)

# ═══════════════════════════════════════════════════════════════════════════
#  TEAMS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "👥 Teams":
    st.markdown("<h2>👥 Teams</h2>", unsafe_allow_html=True)
    if not db["teams"]:
        st.info("No teams yet. Add them in Manage → Add Team.")
    for t in db["teams"]:
        players = [p for p in db["players"] if p["team"] == t["id"]]
        with st.expander(f"**{t['name']}**  ·  {t.get('captain','TBD')}  ·  {len(players)} players"):
            c_info, c_edit = st.columns([3, 1])
            with c_info:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Played", t.get("played",0)); c2.metric("Won",    t.get("won",0))
                c3.metric("Lost",   t.get("lost",0));   c4.metric("Points", t.get("pts",0))
            with c_edit:
                if st.button("✏️ Edit",   key=f"et_{t['id']}"):
                    st.session_state[f"edit_team_{t['id']}"] = True
                if st.button("🗑️ Delete", key=f"dt_{t['id']}"):
                    db["teams"]   = [x for x in db["teams"]   if x["id"] != t["id"]]
                    db["players"] = [x for x in db["players"] if x["team"] != t["id"]]
                    log_activity("Team deleted", t["name"], "🗑️")
                    save_data(); st.rerun()
            if st.session_state.get(f"edit_team_{t['id']}"):
                with st.form(f"f_team_{t['id']}"):
                    nn = st.text_input("Team name",  value=t["name"])
                    nc = st.text_input("Captain",    value=t.get("captain",""))
                    nclr = st.color_picker("Color",  value=t["color"])
                    a, b2 = st.columns(2)
                    if a.form_submit_button("💾 Save", type="primary"):
                        t["name"] = nn; t["captain"] = nc; t["color"] = nclr
                        log_activity("Team updated", nn, "✏️")
                        save_data(); st.session_state[f"edit_team_{t['id']}"] = False; st.rerun()
                    if b2.form_submit_button("Cancel"):
                        st.session_state[f"edit_team_{t['id']}"] = False; st.rerun()
            if players:
                cols = st.columns(3)
                for i, p in enumerate(players):
                    cols[i%3].markdown(f"""<div style='background:{ROLE_COLORS.get(p.get("role","bat"),"#1a1a1a")};
                    border:1px solid #2a2a2a;border-radius:8px;padding:6px 10px;margin-bottom:4px;'>
                    <span style='color:{ROLE_TCOLORS.get(p.get("role","bat"),"#ccc")};font-weight:600;font-size:12px;'>{p["name"]}</span><br/>
                    <span style='font-size:10px;color:#555;'>{ROLE_LABELS.get(p.get("role","bat"),"")}</span></div>""", unsafe_allow_html=True)
            else:
                st.caption("No players yet")

# ═══════════════════════════════════════════════════════════════════════════
#  PLAYERS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🧑 Players":
    st.markdown("<h2>🧑 Player Profiles</h2>", unsafe_allow_html=True)
    team_opts = {"All Teams": 0} | {t["name"]: t["id"] for t in db["teams"]}
    c1, c2 = st.columns(2)
    ft = c1.selectbox("Team", list(team_opts.keys()))
    fr = c2.selectbox("Role", ["All Roles", "Batsman", "Bowler", "All-rounder", "Wicket-keeper"])
    role_rev = {"Batsman":"bat","Bowler":"bowl","All-rounder":"all","Wicket-keeper":"wk"}
    players  = db["players"]
    if team_opts[ft]:     players = [p for p in players if p["team"] == team_opts[ft]]
    if fr != "All Roles": players = [p for p in players if p.get("role") == role_rev.get(fr)]
    if not players:
        st.info("No players found.")
    for p in players:
        t = team_by_id(p["team"]); tc = t["color"] if t else "#FF6B00"
        with st.expander(f"**{p['name']}** · {(t or {}).get('name','')} · {ROLE_LABELS.get(p.get('role','bat'),'')}", expanded=False):
            cl, cr = st.columns([3, 1])
            with cl:
                st.markdown(f"""<div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>
                <div style='width:50px;height:50px;border-radius:50%;background:{tc};display:flex;
                align-items:center;justify-content:center;font-family:Barlow Condensed,sans-serif;
                font-size:22px;font-weight:800;color:#000;flex-shrink:0;'>{p["name"][0]}</div>
                <div><div style='font-size:18px;font-weight:700;color:#fff;'>{p["name"]}</div>
                <div style='font-size:12px;color:#888;'>{(t or {}).get("name","")} &nbsp;·&nbsp;
                <span style='background:{ROLE_COLORS.get(p.get("role","bat"),"#1a1a1a")};
                color:{ROLE_TCOLORS.get(p.get("role","bat"),"#ccc")};padding:2px 8px;border-radius:6px;font-size:11px;'>
                {ROLE_LABELS.get(p.get("role","bat"),"")}
                </span></div></div></div>""", unsafe_allow_html=True)
                r1 = st.columns(4)
                r1[0].metric("Runs",    p.get("runs",0));  r1[1].metric("Balls",   p.get("balls",0))
                r1[2].metric("Fours",   p.get("fours",0)); r1[3].metric("Sixes",   p.get("sixes",0))
                r2 = st.columns(4)
                r2[0].metric("SR",      calc_sr(p.get("runs",0),p.get("balls",0)))
                r2[1].metric("Wickets", p.get("wkts",0))
                r2[2].metric("Bowl Ov", fmt_ov(p.get("bowl_balls",0)))
                r2[3].metric("Economy", calc_eco(p.get("runs_conceded",0),p.get("bowl_balls",0)))
            with cr:
                if st.button("✏️ Edit",   key=f"ep_{p['id']}"):
                    st.session_state[f"edit_player_{p['id']}"] = True
                if st.button("🗑️ Delete", key=f"dp_{p['id']}"):
                    db["players"] = [x for x in db["players"] if x["id"] != p["id"]]
                    log_activity("Player removed", p["name"], "🗑️")
                    save_data(); st.rerun()
            if st.session_state.get(f"edit_player_{p['id']}"):
                with st.form(f"f_player_{p['id']}"):
                    nn = st.text_input("Name", value=p["name"])
                    tnames = [t2["name"] for t2 in db["teams"]]
                    ct  = next((t2["name"] for t2 in db["teams"] if t2["id"]==p["team"]), tnames[0] if tnames else "")
                    nt  = st.selectbox("Team", tnames, index=tnames.index(ct) if ct in tnames else 0)
                    nr  = st.selectbox("Role", list(ROLE_LABELS.values()),
                                       index=list(ROLE_LABELS.keys()).index(p.get("role","bat")))
                    nru = st.number_input("Career Runs",    value=p.get("runs",0),  min_value=0)
                    nwk = st.number_input("Career Wickets", value=p.get("wkts",0),  min_value=0)
                    a, b2 = st.columns(2)
                    if a.form_submit_button("💾 Save", type="primary"):
                        to = next((t2 for t2 in db["teams"] if t2["name"]==nt), None)
                        p["name"]=nn; p["team"]=to["id"] if to else p["team"]
                        p["role"]=list(ROLE_LABELS.keys())[list(ROLE_LABELS.values()).index(nr)]
                        p["runs"]=nru; p["wkts"]=nwk
                        log_activity("Player updated", nn, "✏️")
                        save_data(); st.session_state[f"edit_player_{p['id']}"]=False; st.rerun()
                    if b2.form_submit_button("Cancel"):
                        st.session_state[f"edit_player_{p['id']}"]=False; st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  LIVE SCORECARD
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🎮 Live Scorecard":
    st.markdown("<h2>🎮 Live Scorecard</h2>", unsafe_allow_html=True)
    live_or_up = [m for m in db["matches"] if m["status"] in ("live","upcoming")]
    if not live_or_up:
        st.info("No live or upcoming matches.")
        st.stop()
    labels = {m["id"]: f'{(team_by_id(m["teamA"]) or {}).get("name","?")} vs {(team_by_id(m["teamB"]) or {}).get("name","?")} · {m.get("date","")} · {m.get("overs",20)} ov' for m in live_or_up}
    sel_lbl = st.selectbox("Select match", list(labels.values()))
    sel_mid = next(mid for mid, lbl in labels.items() if lbl == sel_lbl)
    sel_m   = match_by_id(sel_mid)

    if sel_m and st.button("🚀 Open / Resume Scorecard", type="primary"):
        if sel_m["status"] == "upcoming":
            sel_m["status"] = "live"
            if not sel_m.get("inn"):
                sel_m["inn"] = [
                    {"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[],"innings_done":False},
                    {"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[],"innings_done":False}
                ]
            ta2 = team_by_id(sel_m["teamA"]); tb2 = team_by_id(sel_m["teamB"])
            log_activity("Match started", f'{(ta2 or {}).get("name","")} vs {(tb2 or {}).get("name","")}', "🔴")
        st.session_state.live_match_id = sel_mid
        save_data(); st.rerun()

    if st.session_state.live_match_id != sel_mid: st.stop()

    m   = match_by_id(sel_mid)
    ta  = team_by_id(m["teamA"]); tb = team_by_id(m["teamB"])
    if not m.get("inn"): st.stop()

    ci  = 1 if m["inn"][0].get("innings_done") else 0
    inn = m["inn"][ci]
    opp = m["inn"][0] if ci == 1 else None
    i0  = m["inn"][0]; i1 = m["inn"][1]

    st.markdown(f"""
    <div style='background:#111;border:2px solid #FF6B00;border-radius:14px;padding:16px 20px;margin-bottom:12px;'>
        <div style='font-size:12px;color:#444;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px;'>
            {m.get("date","")} · {m.get("venue","")} · {m.get("overs",20)} overs
        </div>
        <div style='display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;'>
            <div>
                <div style='font-family:Barlow Condensed,sans-serif;font-size:18px;font-weight:800;color:{ta["color"]};'>{ta["name"].upper()}</div>
                <div style='font-family:Barlow Condensed,sans-serif;font-size:36px;font-weight:800;color:#fff;'>{i0["runs"]}/{i0["wickets"]}</div>
                <div style='font-size:12px;color:#555;'>{fmt_ov(i0["balls"])} ov</div>
            </div>
            <div style='font-family:Barlow Condensed,sans-serif;font-size:22px;font-weight:800;color:#FF6B00;'>VS</div>
            <div style='text-align:right;'>
                <div style='font-family:Barlow Condensed,sans-serif;font-size:18px;font-weight:800;color:{tb["color"]};'>{tb["name"].upper()}</div>
                <div style='font-family:Barlow Condensed,sans-serif;font-size:36px;font-weight:800;color:#fff;'>{str(i1["runs"])+"/"+str(i1["wickets"]) if ci==1 or i1.get("balls",0)>0 else "—"}</div>
                <div style='font-size:12px;color:#555;'>{fmt_ov(i1["balls"])+" ov" if ci==1 or i1.get("balls",0)>0 else "Yet to bat"}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if ci == 1 and opp:
        target = opp["runs"]+1; need = target-inn["runs"]; bleft = m["overs"]*6-inn["balls"]
        rrr = round(need/(bleft/6), 2) if bleft > 0 else 0
        st.markdown(f"""<div style='background:#1a1000;border:1px solid #FF6B00;border-radius:8px;padding:10px;
        text-align:center;margin-bottom:10px;'><span style='color:#FF6B00;font-weight:700;font-size:14px;'>
        Need {max(0,need)} runs from {bleft} balls &nbsp;·&nbsp; RRR: {rrr}</span></div>""", unsafe_allow_html=True)

    if m.get("result"):
        st.markdown(f"""<div style='background:#0d2018;border:2px solid #25a85e;border-radius:12px;
        padding:16px;text-align:center;margin-bottom:12px;'><div style='font-family:Barlow Condensed,sans-serif;
        font-size:24px;font-weight:800;color:#25a85e;'>🏆 {m["result"]}</div></div>""", unsafe_allow_html=True)
        st.stop()

    st.divider()
    ca, cb, cc = st.columns(3)
    striker     = ca.text_input("🏏 Striker",    key="lv_s",  placeholder="Batsman name")
    nstriker    = cb.text_input("🏏 Non-striker", key="lv_ns", placeholder="Batsman name")
    bowler_name = cc.text_input("🎳 Bowler",      key="lv_b",  placeholder="Bowler name")

    def _swap():
        s=st.session_state.get("lv_s",""); n=st.session_state.get("lv_ns","")
        st.session_state["lv_s"]=n; st.session_state["lv_ns"]=s

    def _chkov(bwl):
        if inn["balls"]>0 and inn["balls"]%6==0:
            bwl["completed_overs"]=bwl.get("completed_overs",0)+1; bwl["balls"]=0
            inn["overBalls"]=[]; _swap()

    def _endinn():
        inn["innings_done"]=True
        if ci==0:
            st.session_state["lv_s"]=""; st.session_state["lv_ns"]=""; st.session_state["lv_b"]=""

    def _finish(res):
        m["result"]=res; m["status"]="completed"; inn["innings_done"]=True
        ta2=team_by_id(m["teamA"]); tb2=team_by_id(m["teamB"])
        for t2 in [ta2,tb2]:
            if not t2: continue
            t2.setdefault("played",0); t2.setdefault("won",0); t2.setdefault("lost",0); t2.setdefault("tied",0); t2.setdefault("pts",0)
            t2["played"]+=1
        if ta2 and ta2["name"] in res: ta2["won"]+=1; ta2["pts"]+=2
        if tb2 and tb2["name"] in res: tb2["won"]+=1; tb2["pts"]+=2
        if ta2 and ta2["name"] not in res and tb2 and tb2["name"] not in res:
            ta2["pts"]+=1; ta2["tied"]=ta2.get("tied",0)+1; tb2["pts"]+=1; tb2["tied"]=tb2.get("tied",0)+1
        if ta2 and ta2["name"] in res and tb2: tb2["lost"]=tb2.get("lost",0)+1
        if tb2 and tb2["name"] in res and ta2: ta2["lost"]=ta2.get("lost",0)+1
        log_activity("Match completed", res, "🏆")

    def add_ball(run):
        s=striker.strip() or "Batsman A"; ns=nstriker.strip() or "Batsman B"; bw=bowler_name.strip() or "Bowler"
        if s not in inn["batsmen"]: inn["batsmen"][s]={"runs":0,"balls":0,"fours":0,"sixes":0,"out":False}
        if bw not in inn["bowlers"]: inn["bowlers"][bw]={"balls":0,"completed_overs":0,"runs":0,"wickets":0}
        b=inn["batsmen"][s]; bwl=inn["bowlers"][bw]
        inn["history"].append({"run":str(run),"striker":s,"nstriker":ns,"bowler":bw})
        if run in ("wd","nb"):
            inn["runs"]+=1; inn["extras"]+=1; bwl["runs"]+=1; inn["overBalls"].append(run)
        elif run=="W":
            b["balls"]+=1; b["out"]=True; bwl["balls"]+=1; bwl["wickets"]+=1
            inn["balls"]+=1; inn["wickets"]+=1; inn["overBalls"].append("W")
            _chkov(bwl)
            if inn["wickets"]>=10: _endinn(); save_data(); st.rerun(); return
        else:
            b["runs"]+=run; b["balls"]+=1; bwl["runs"]+=run; bwl["balls"]+=1
            inn["runs"]+=run; inn["balls"]+=1
            if run==4: b["fours"]+=1; inn["fours"]+=1
            if run==6: b["sixes"]+=1; inn["sixes"]+=1
            inn["overBalls"].append(str(run))
            if run%2==1: _swap()
            _chkov(bwl)
        if inn["balls"]>=m["overs"]*6: _endinn(); save_data(); st.rerun(); return
        if ci==1 and opp and inn["runs"]>=opp["runs"]+1:
            wl=10-inn["wickets"]
            _finish(f"{tb['name'] if ci else ta['name']} win by {wl} wicket{'s' if wl!=1 else ''}!")
            save_data(); st.rerun(); return
        save_data(); st.rerun()

    st.markdown("**Add delivery**")
    bc = st.columns(10)
    for i, (lbl, val) in enumerate([("0","0"),("1","1"),("2","2"),("3","3"),("4️⃣","4"),("6️⃣","6"),("🔴W","W"),("Wd","wd"),("Nb","nb"),("↩️","undo")]):
        if bc[i].button(lbl, key=f"ball_{val}", use_container_width=True):
            if val == "undo":
                if inn.get("history"):
                    last=inn["history"].pop()
                    if inn["overBalls"]: inn["overBalls"].pop()
                    run=last["run"]; s=last["striker"]; bw=last["bowler"]
                    if run in ("wd","nb"):
                        inn["runs"]-=1; inn["extras"]-=1
                        if bw in inn["bowlers"]: inn["bowlers"][bw]["runs"]-=1
                    elif run=="W":
                        if s in inn["batsmen"]: inn["batsmen"][s]["balls"]-=1; inn["batsmen"][s]["out"]=False
                        if bw in inn["bowlers"]: inn["bowlers"][bw]["balls"]-=1; inn["bowlers"][bw]["wickets"]-=1
                        inn["balls"]-=1; inn["wickets"]-=1
                    else:
                        rv=int(run)
                        if s in inn["batsmen"]:
                            inn["batsmen"][s]["runs"]-=rv; inn["batsmen"][s]["balls"]-=1
                            if rv==4: inn["batsmen"][s]["fours"]-=1; inn["fours"]-=1
                            if rv==6: inn["batsmen"][s]["sixes"]-=1; inn["sixes"]-=1
                        if bw in inn["bowlers"]: inn["bowlers"][bw]["balls"]-=1; inn["bowlers"][bw]["runs"]-=rv
                        inn["runs"]-=rv; inn["balls"]-=1
                    save_data(); st.rerun()
            else:
                add_ball(int(val) if val.isdigit() else val)

    if inn.get("overBalls"):
        st.markdown("**Current over:**")
        oh = "".join([f"<span style='display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;font-size:12px;font-weight:700;margin-right:4px;background:{'#3a0000' if b=='W' else '#0d2018' if b=='6' else '#0d1a2a' if b=='4' else '#1a1000' if b in ('wd','nb') else '#1a1a1a'};color:{'#ff4444' if b=='W' else '#25a85e' if b=='6' else '#4da6ff' if b=='4' else '#FF6B00' if b in ('wd','nb') else '#ccc'};border:1px solid {'#ff4444' if b=='W' else '#25a85e' if b=='6' else '#4da6ff' if b=='4' else '#FF6B00' if b in ('wd','nb') else '#2a2a2a'};'>{b}</span>" for b in inn["overBalls"]])
        st.markdown(oh, unsafe_allow_html=True)

    if inn.get("innings_done") and ci == 0:
        st.warning("1st innings complete!")
        if st.button("▶️ Start 2nd Innings", type="primary"): save_data(); st.rerun()
        st.stop()

    cb1, cb2 = st.columns(2)
    with cb1:
        st.markdown("**🏏 Batting**")
        bats = inn.get("batsmen", {})
        if bats:
            st.dataframe(pd.DataFrame([{"Batsman":n+(" *" if not b["out"] else ""),"R":b["runs"],"B":b["balls"],"4s":b["fours"],"6s":b["sixes"],"SR":calc_sr(b["runs"],b["balls"])} for n,b in bats.items()]), use_container_width=True, hide_index=True)
        else: st.caption("No batting data")
    with cb2:
        st.markdown("**🎳 Bowling**")
        bwls = inn.get("bowlers", {})
        if bwls:
            st.dataframe(pd.DataFrame([{"Bowler":n,"O":fmt_ov(bw.get("balls",0)+bw.get("completed_overs",0)*6),"R":bw["runs"],"W":bw["wickets"],"Eco":calc_eco(bw["runs"],bw.get("balls",0)+bw.get("completed_overs",0)*6)} for n,bw in bwls.items()]), use_container_width=True, hide_index=True)
        else: st.caption("No bowling data")

# ═══════════════════════════════════════════════════════════════════════════
#  MANAGE
# ═══════════════════════════════════════════════════════════════════════════
elif page == "➕ Manage":
    st.markdown("<h2>➕ Manage</h2>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🏏 Add Team", "🧑 Add Player", "📅 Schedule Match"])

    with t1:
        with st.form("add_team"):
            st.markdown("### Add New Team")
            c1, c2 = st.columns(2)
            tn = c1.text_input("Team name *", placeholder="e.g. Sales Warriors")
            tc = c2.text_input("Captain",     placeholder="e.g. Rahul Mehta")
            col = st.color_picker("Jersey color", value="#FF6B00")
            if st.form_submit_button("➕ Add Team", type="primary"):
                if tn.strip():
                    db["teams"].append({"id":db["next_team_id"],"name":tn.strip(),"captain":tc.strip(),"color":col,"played":0,"won":0,"lost":0,"tied":0,"pts":0})
                    db["next_team_id"]+=1; log_activity("Team added", tn, "👥"); save_data()
                    st.success(f"✅ Team **{tn}** added!")
                else: st.error("Team name required")

    with t2:
        if not db["teams"]: st.warning("Add at least one team first.")
        else:
            with st.form("add_player"):
                st.markdown("### Add New Player")
                c1, c2 = st.columns(2)
                pn = c1.text_input("Player name *", placeholder="e.g. Virat Singh")
                pt = c2.selectbox("Team *", [t["name"] for t in db["teams"]])
                c3, c4 = st.columns(2)
                pr = c3.selectbox("Role", list(ROLE_LABELS.values()))
                pj = c4.text_input("Jersey #", placeholder="18")
                if st.form_submit_button("➕ Add Player", type="primary"):
                    if pn.strip():
                        to = next(t for t in db["teams"] if t["name"]==pt)
                        rk = list(ROLE_LABELS.keys())[list(ROLE_LABELS.values()).index(pr)]
                        db["players"].append({"id":db["next_player_id"],"name":pn.strip(),"team":to["id"],"role":rk,"jersey":pj,"runs":0,"balls":0,"fours":0,"sixes":0,"wkts":0,"bowl_balls":0,"runs_conceded":0})
                        db["next_player_id"]+=1; log_activity("Player added", f"{pn} → {pt}", "🧑"); save_data()
                        st.success(f"✅ **{pn}** added to **{pt}**!")
                    else: st.error("Player name required")

    with t3:
        if len(db["teams"]) < 2: st.warning("Need at least 2 teams.")
        else:
            with st.form("add_match"):
                st.markdown("### Schedule a Match")
                tnames = [t["name"] for t in db["teams"]]
                c1, c2 = st.columns(2)
                mta = c1.selectbox("Team A *", tnames, index=0)
                mtb = c2.selectbox("Team B *", tnames, index=1 if len(tnames)>1 else 0)
                c3, c4, c5 = st.columns(3)
                mdt = c3.date_input("Date *", value=date.today())
                mti = c4.time_input("Time *")
                mov = c5.selectbox("Overs", [5,10,15,20,50], index=3)
                mve = st.text_input("Venue", placeholder="Company Ground A")
                if st.form_submit_button("📅 Schedule Match", type="primary"):
                    if mta == mtb: st.error("Teams cannot be the same")
                    else:
                        taid = next(t["id"] for t in db["teams"] if t["name"]==mta)
                        tbid = next(t["id"] for t in db["teams"] if t["name"]==mtb)
                        db["matches"].append({"id":db["next_match_id"],"teamA":taid,"teamB":tbid,"date":str(mdt),"time":str(mti),"venue":mve or "TBD","overs":mov,"status":"upcoming",
                            "inn":[{"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[],"innings_done":False},
                                   {"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[],"innings_done":False}],
                            "result":""})
                        db["next_match_id"]+=1; log_activity("Match scheduled", f"{mta} vs {mtb} on {mdt}", "📅"); save_data()
                        st.success(f"✅ **{mta} vs {mtb}** on {mdt}!")

# ═══════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown("<h2>⚙️ League Settings</h2>", unsafe_allow_html=True)
    with st.form("league_settings"):
        c1, c2 = st.columns(2)
        nn = c1.text_input("League name",    value=db["league_name"])
        ne = c2.text_input("Edition/Season", value=db["league_edition"])
        nl = st.text_input("League emoji/logo", value=db.get("league_logo","🏏"), help="Paste any emoji")
        if st.form_submit_button("💾 Save Settings", type="primary"):
            db["league_name"]=nn; db["league_edition"]=ne; db["league_logo"]=nl
            log_activity("Settings updated", nn, "⚙️"); save_data(); st.success("✅ Saved!"); st.rerun()

    st.divider()
    st.markdown("### Data Management")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Export Data (JSON)", data=json.dumps(db,indent=2,default=str),
            file_name="cricket_league_data.json", mime="application/json")
    with c2:
        up = st.file_uploader("📤 Import Data (JSON)", type="json")
        if up:
            st.session_state.db=json.load(up); save_data(); st.success("✅ Imported!"); st.rerun()

    st.divider()
    with st.expander("⚠️ Danger Zone"):
        st.warning("These actions cannot be undone!")
        c1, c2, c3 = st.columns(3)
        if c1.button("🗑️ Clear Matches"): db["matches"]=[]; save_data(); st.rerun()
        if c2.button("🗑️ Clear Players"): db["players"]=[]; save_data(); st.rerun()
        if c3.button("🔄 Full Reset"):    st.session_state.db=DEFAULT_DATA.copy(); save_data(); st.rerun()

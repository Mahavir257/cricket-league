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

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.5px; }

.stApp { background: #f5f7f4; }

.league-banner {
    background: linear-gradient(135deg, #1a6b3c 0%, #0f4224 100%);
    border-radius: 16px; padding: 20px 28px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 18px;
}
.league-banner h1 { color: #fff; margin: 0; font-size: 28px; }
.league-banner p  { color: #a8d5b5; margin: 0; font-size: 14px; }

.stat-card {
    background: white; border-radius: 12px; padding: 16px;
    text-align: center; border: 1px solid #e8ede8;
}
.stat-card .num { font-family:'Barlow Condensed',sans-serif; font-size:32px; font-weight:700; color:#1a6b3c; }
.stat-card .lbl { font-size:12px; color:#666; margin-top:2px; }

.match-card {
    background: white; border-radius: 12px; padding: 14px 18px;
    border: 1px solid #e8ede8; margin-bottom: 10px;
}
.team-name { font-family:'Barlow Condensed',sans-serif; font-size:18px; font-weight:700; }
.score-big { font-family:'Barlow Condensed',sans-serif; font-size:26px; font-weight:700; color:#1a6b3c; }

.badge-live   { background:#ffebee; color:#b71c1c; padding:2px 10px; border-radius:8px; font-size:11px; font-weight:600; }
.badge-done   { background:#e8f5e9; color:#1b5e20; padding:2px 10px; border-radius:8px; font-size:11px; font-weight:600; }
.badge-upcoming { background:#e3f2fd; color:#0c447c; padding:2px 10px; border-radius:8px; font-size:11px; font-weight:600; }

.player-card {
    background:white; border-radius:12px; padding:14px 16px;
    border:1px solid #e8ede8; margin-bottom:8px;
}
.avatar {
    width:42px; height:42px; border-radius:50%;
    display:inline-flex; align-items:center; justify-content:center;
    font-family:'Barlow Condensed',sans-serif; font-size:17px; font-weight:700;
    color:white; vertical-align:middle;
}

div[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] > div { padding-top: 1rem; }
.stButton > button {
    border-radius: 8px; font-family: 'Barlow', sans-serif;
    font-weight: 500; transition: all .15s;
}
.stButton > button:hover { transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

# ── Data persistence ─────────────────────────────────────────────────────────
DATA_FILE = "cricket_league_data.json"

DEFAULT_DATA = {
    "league_name": "Company Cricket League",
    "league_edition": "Season 2026",
    "teams": [],
    "players": [],
    "matches": [],
    "next_team_id": 1,
    "next_player_id": 1,
    "next_match_id": 1,
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.db, f, indent=2, default=str)

def init():
    if "db" not in st.session_state:
        st.session_state.db = load_data()
    if "live_state" not in st.session_state:
        st.session_state.live_state = None
    if "live_match_id" not in st.session_state:
        st.session_state.live_match_id = None

init()
db = st.session_state.db

# ── Helpers ───────────────────────────────────────────────────────────────────
def team_by_id(tid):
    return next((t for t in db["teams"] if t["id"] == tid), None)

def player_by_id(pid):
    return next((p for p in db["players"] if p["id"] == pid), None)

def match_by_id(mid):
    return next((m for m in db["matches"] if m["id"] == mid), None)

def fmt_ov(balls):
    return f"{balls // 6}.{balls % 6}"

def calc_sr(runs, balls):
    return round(runs / balls * 100, 1) if balls else 0.0

def calc_eco(runs, balls):
    return round(runs / (balls / 6), 2) if balls else 0.0

def calc_nrr(team):
    scored, conceded, ov_bat, ov_bowl = 0, 0, 0, 0
    for m in db["matches"]:
        if m["status"] != "completed" or not m.get("inn") or not m["inn"][0] or not m["inn"][1]:
            continue
        if m["teamA"] == team["id"]:
            scored += m["inn"][0].get("runs", 0)
            ov_bat  += m["inn"][0].get("balls", 0)
            conceded += m["inn"][1].get("runs", 0)
            ov_bowl  += m["inn"][1].get("balls", 0)
        elif m["teamB"] == team["id"]:
            scored += m["inn"][1].get("runs", 0)
            ov_bat  += m["inn"][1].get("balls", 0)
            conceded += m["inn"][0].get("runs", 0)
            ov_bowl  += m["inn"][0].get("balls", 0)
    rpo_for     = round(scored  / (ov_bat  / 6), 3) if ov_bat  else 0
    rpo_against = round(conceded / (ov_bowl / 6), 3) if ov_bowl else 0
    return round(rpo_for - rpo_against, 3)

TEAM_COLORS = [
    "#1565C0", "#B71C1C", "#1a6b3c", "#E65100",
    "#6A1B9A", "#00695C", "#4E342E", "#37474F",
    "#0277BD", "#558B2F", "#AD1457", "#F57F17",
]
ROLE_LABELS  = {"bat": "Batsman", "bowl": "Bowler", "all": "All-rounder", "wk": "Wicket-keeper"}
ROLE_COLORS  = {"bat": "#E3F2FD", "bowl": "#FFF3E0", "all": "#E8F5E9", "wk": "#F3E5F5"}
ROLE_TCOLORS = {"bat": "#0C447C", "bowl": "#E65100", "all": "#1B5E20", "wk": "#6A1B9A"}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='background:#1a6b3c;border-radius:12px;padding:14px 16px;margin-bottom:16px;'>
        <div style='font-family:Barlow Condensed,sans-serif;font-size:22px;font-weight:700;color:white;'>🏏 {db["league_name"]}</div>
        <div style='font-size:12px;color:#a8d5b5;margin-top:2px;'>{db["league_edition"]}</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigation", [
        "🏠 Dashboard", "📅 Schedule", "📊 Points Table",
        "👥 Teams", "🧑 Players", "🎮 Live Scorecard",
        "➕ Manage", "⚙️ League Settings"
    ], label_visibility="collapsed")

    st.divider()
    live_count = len([m for m in db["matches"] if m["status"] == "live"])
    total      = len(db["matches"])
    done       = len([m for m in db["matches"] if m["status"] == "completed"])
    st.metric("Teams",    len(db["teams"]))
    st.metric("Players",  len(db["players"]))
    col1, col2 = st.columns(2)
    col1.metric("Matches", total)
    col2.metric("Done",    done)
    if live_count:
        st.error(f"🔴 {live_count} LIVE NOW")

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.markdown(f"""
    <div class='league-banner'>
        <div style='font-size:48px;'>🏏</div>
        <div>
            <h1>{db["league_name"]}</h1>
            <p>{db["league_edition"]} &nbsp;·&nbsp; {len(db["teams"])} Teams &nbsp;·&nbsp; {len(db["matches"])} Matches</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [
        (c1, len(db["teams"]),   "Teams"),
        (c2, len(db["players"]), "Players"),
        (c3, total,              "Matches"),
        (c4, done,               "Completed"),
    ]:
        col.markdown(f"<div class='stat-card'><div class='num'>{num}</div><div class='lbl'>{lbl}</div></div>", unsafe_allow_html=True)

    st.markdown("### Recent & Live Matches")
    shown = [m for m in db["matches"] if m["status"] in ("live","completed")][-4:] + \
            [m for m in db["matches"] if m["status"] == "upcoming"][:2]
    if not shown:
        st.info("No matches yet. Schedule matches in **Manage**.")
    for m in shown[:6]:
        ta = team_by_id(m["teamA"]); tb = team_by_id(m["teamB"])
        if not ta or not tb: continue
        badge_cls = {"live":"badge-live","completed":"badge-done","upcoming":"badge-upcoming"}[m["status"]]
        i0 = m.get("inn",[None,None])[0]; i1 = m.get("inn",[None,None])[1] if m.get("inn") else None
        with st.container():
            st.markdown(f"""
            <div class='match-card'>
                <span class='{badge_cls}'>{'🔴 LIVE' if m['status']=='live' else m['status'].upper()}</span>
                <div style='display:flex;align-items:center;gap:12px;margin-top:8px;'>
                    <div style='flex:1;'>
                        <div class='team-name' style='color:{ta["color"]}'>{ta["name"]}</div>
                        <div class='score-big'>{str(i0["runs"])+"/"+str(i0["wickets"]) if i0 else "—"}</div>
                        <div style='font-size:11px;color:#888;'>{fmt_ov(i0["balls"])+" ov" if i0 else ""}</div>
                    </div>
                    <div style='font-size:16px;color:#aaa;font-weight:600;'>vs</div>
                    <div style='flex:1;text-align:right;'>
                        <div class='team-name' style='color:{tb["color"]}'>{tb["name"]}</div>
                        <div class='score-big'>{str(i1["runs"])+"/"+str(i1["wickets"]) if i1 else "—"}</div>
                        <div style='font-size:11px;color:#888;'>{fmt_ov(i1["balls"])+" ov" if i1 else ""}</div>
                    </div>
                </div>
                <div style='font-size:12px;color:#888;margin-top:6px;'>{m.get("date","")} &nbsp;·&nbsp; {m.get("venue","")} &nbsp;·&nbsp; {m.get("overs",20)} overs</div>
                {f'<div style="font-size:13px;font-weight:500;color:#1a6b3c;margin-top:4px;">{m["result"]}</div>' if m.get("result") else ""}
            </div>
            """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🏆 Top Run Scorers")
        top_bat = sorted(db["players"], key=lambda p: p.get("runs", 0), reverse=True)[:5]
        if top_bat:
            df = pd.DataFrame([{
                "Player": p["name"],
                "Team": (team_by_id(p["team"]) or {}).get("name", ""),
                "Runs": p.get("runs", 0),
                "Balls": p.get("balls", 0),
                "4s": p.get("fours", 0),
                "6s": p.get("sixes", 0),
                "SR": calc_sr(p.get("runs",0), p.get("balls",0)),
            } for p in top_bat])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No batting data yet")

    with col_b:
        st.markdown("### 🎯 Top Wicket Takers")
        top_bwl = sorted(db["players"], key=lambda p: p.get("wkts", 0), reverse=True)[:5]
        if top_bwl:
            df = pd.DataFrame([{
                "Player": p["name"],
                "Team": (team_by_id(p["team"]) or {}).get("name", ""),
                "Wkts": p.get("wkts", 0),
                "Runs Conceded": p.get("runs_conceded", 0),
                "Overs": fmt_ov(p.get("bowl_balls", 0)),
                "Eco": calc_eco(p.get("runs_conceded", 0), p.get("bowl_balls", 0)),
            } for p in top_bwl])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No bowling data yet")

# ══════════════════════════════════════════════════════════════════════════════
#  SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Schedule":
    st.markdown("## 📅 Match Schedule")

    filter_status = st.selectbox("Filter by status", ["All","Upcoming","Live","Completed"], index=0)
    matches = db["matches"]
    if filter_status != "All":
        matches = [m for m in matches if m["status"] == filter_status.lower()]

    if not matches:
        st.info("No matches found. Schedule some in **Manage → Add Match**.")
    else:
        by_date: dict = {}
        for m in sorted(matches, key=lambda x: x.get("date","9999")):
            d = m.get("date","No date")
            by_date.setdefault(d, []).append(m)

        for dt, ms in by_date.items():
            try:
                dobj  = datetime.strptime(dt, "%Y-%m-%d")
                dlbl  = dobj.strftime("%A, %d %B %Y")
            except Exception:
                dlbl = dt
            st.markdown(f"**{dlbl}**")
            for m in ms:
                ta = team_by_id(m["teamA"]); tb = team_by_id(m["teamB"])
                if not ta or not tb: continue
                badge_cls = {"live":"badge-live","completed":"badge-done","upcoming":"badge-upcoming"}[m["status"]]
                i0 = m.get("inn",[None,None])[0] if m.get("inn") else None
                i1 = m.get("inn",[None,None])[1] if m.get("inn") and len(m["inn"])>1 else None
                st.markdown(f"""
                <div class='match-card'>
                    <span class='{badge_cls}'>{'🔴 LIVE' if m['status']=='live' else m['status'].upper()}</span>
                    &nbsp;<span style='font-size:12px;color:#888;'>{m.get("time","")} &nbsp;·&nbsp; {m.get("venue","")} &nbsp;·&nbsp; {m.get("overs",20)} ov</span>
                    <div style='display:flex;align-items:center;gap:12px;margin-top:8px;'>
                        <div style='flex:1;'>
                            <div class='team-name' style='color:{ta["color"]}'>{ta["name"]}</div>
                            <div class='score-big'>{str(i0["runs"])+"/"+str(i0["wickets"]) if i0 else "Yet to bat"}</div>
                        </div>
                        <div style='font-size:14px;color:#aaa;font-weight:600;padding:0 8px;'>vs</div>
                        <div style='flex:1;text-align:right;'>
                            <div class='team-name' style='color:{tb["color"]}'>{tb["name"]}</div>
                            <div class='score-big'>{str(i1["runs"])+"/"+str(i1["wickets"]) if i1 else "Yet to bat"}</div>
                        </div>
                    </div>
                    {f'<div style="font-size:13px;color:#1a6b3c;font-weight:500;margin-top:6px;">{m["result"]}</div>' if m.get("result") else ""}
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  POINTS TABLE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Points Table":
    st.markdown("## 📊 Points Table")

    if not db["teams"]:
        st.info("Add teams first in **Manage**.")
    else:
        rows = []
        for t in db["teams"]:
            played = t.get("played", 0)
            won    = t.get("won", 0)
            lost   = t.get("lost", 0)
            tied   = t.get("tied", 0)
            pts    = t.get("pts", 0)
            nrr    = calc_nrr(t)
            rows.append({"id": t["id"], "name": t["name"], "color": t["color"],
                         "played": played, "won": won, "lost": lost, "tied": tied,
                         "pts": pts, "nrr": nrr})
        rows.sort(key=lambda r: (-r["pts"], -r["nrr"]))

        st.markdown("""
        <table style='width:100%;border-collapse:collapse;font-family:Barlow,sans-serif;background:white;border-radius:12px;overflow:hidden;border:1px solid #e8ede8;'>
        <thead><tr style='background:#1a6b3c;color:white;'>
            <th style='padding:10px 12px;text-align:left;font-size:12px;'>#</th>
            <th style='padding:10px 12px;text-align:left;font-size:12px;'>Team</th>
            <th style='padding:10px 12px;text-align:center;font-size:12px;'>P</th>
            <th style='padding:10px 12px;text-align:center;font-size:12px;'>W</th>
            <th style='padding:10px 12px;text-align:center;font-size:12px;'>L</th>
            <th style='padding:10px 12px;text-align:center;font-size:12px;'>T</th>
            <th style='padding:10px 12px;text-align:center;font-size:12px;font-weight:700;'>Pts</th>
            <th style='padding:10px 12px;text-align:center;font-size:12px;'>NRR</th>
        </tr></thead><tbody>
        """ + "".join([f"""
        <tr style='background:{"#f0fbf4" if i<2 else "white"};border-bottom:1px solid #f0f0f0;'>
            <td style='padding:10px 12px;font-weight:700;color:#1a6b3c;font-family:Barlow Condensed,sans-serif;font-size:18px;'>{
                "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else str(i+1)}</td>
            <td style='padding:10px 12px;'>
                <span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{r["color"]};margin-right:6px;'></span>
                <strong>{r["name"]}</strong>
                {" <span style='font-size:10px;background:#e8f5e9;color:#1b5e20;padding:1px 7px;border-radius:8px;margin-left:4px;'>QUALIFIER</span>" if i<2 else ""}
            </td>
            <td style='padding:10px 12px;text-align:center;'>{r["played"]}</td>
            <td style='padding:10px 12px;text-align:center;color:#1a6b3c;font-weight:500;'>{r["won"]}</td>
            <td style='padding:10px 12px;text-align:center;color:#b71c1c;'>{r["lost"]}</td>
            <td style='padding:10px 12px;text-align:center;'>{r["tied"]}</td>
            <td style='padding:10px 12px;text-align:center;font-weight:700;font-size:16px;font-family:Barlow Condensed,sans-serif;'>{r["pts"]}</td>
            <td style='padding:10px 12px;text-align:center;color:{"#1a6b3c" if r["nrr"]>=0 else "#b71c1c"};font-weight:500;'>
                {("+" if r["nrr"]>=0 else "")+str(r["nrr"])}
            </td>
        </tr>
        """ for i, r in enumerate(rows)]) + """
        </tbody></table>
        <div style='font-size:11px;color:#888;margin-top:8px;'>Top 2 teams qualify for finals · NRR used as tiebreaker</div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TEAMS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Teams":
    st.markdown("## 👥 Teams")
    if not db["teams"]:
        st.info("No teams yet. Add them in **Manage → Add Team**.")
    for t in db["teams"]:
        players = [p for p in db["players"] if p["team"] == t["id"]]
        with st.expander(f"**{t['name']}**  ·  Captain: {t.get('captain','TBD')}  ·  {len(players)} players", expanded=False):
            col_info, col_edit = st.columns([3,1])
            with col_info:
                st.markdown(f"<span style='display:inline-block;width:14px;height:14px;border-radius:50%;background:{t['color']};margin-right:6px;vertical-align:middle;'></span><strong>Team Color</strong>", unsafe_allow_html=True)
                st.write(f"**Captain:** {t.get('captain','TBD')}")
                m_played = t.get("played",0); m_won = t.get("won",0); m_lost = t.get("lost",0)
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Played", m_played); c2.metric("Won", m_won)
                c3.metric("Lost", m_lost);     c4.metric("Points", t.get("pts",0))
            with col_edit:
                if st.button("✏️ Edit", key=f"edit_team_{t['id']}"):
                    st.session_state[f"editing_team_{t['id']}"] = True
            if st.session_state.get(f"editing_team_{t['id']}"):
                with st.form(key=f"form_team_{t['id']}"):
                    new_name = st.text_input("Team name", value=t["name"])
                    new_cap  = st.text_input("Captain", value=t.get("captain",""))
                    new_color= st.color_picker("Team color", value=t["color"])
                    c1,c2 = st.columns(2)
                    if c1.form_submit_button("💾 Save"):
                        t["name"] = new_name; t["captain"] = new_cap; t["color"] = new_color
                        save_data(); st.session_state[f"editing_team_{t['id']}"] = False; st.rerun()
                    if c2.form_submit_button("Cancel"):
                        st.session_state[f"editing_team_{t['id']}"] = False; st.rerun()
            st.markdown("**Squad**")
            if players:
                cols = st.columns(3)
                for i, p in enumerate(players):
                    role_lbl = ROLE_LABELS.get(p.get("role","bat"),"Batsman")
                    cols[i%3].markdown(f"""
                    <div style='background:{ROLE_COLORS.get(p.get("role","bat"),"#eee")};
                         color:{ROLE_TCOLORS.get(p.get("role","bat"),"#333")};
                         border-radius:8px;padding:5px 10px;font-size:12px;margin-bottom:4px;'>
                        <strong>{p["name"]}</strong><br/><span style='font-size:10px;'>{role_lbl}</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("No players in this team yet")

            if st.button("🗑️ Delete Team", key=f"del_team_{t['id']}", type="secondary"):
                db["teams"] = [x for x in db["teams"] if x["id"] != t["id"]]
                db["players"] = [x for x in db["players"] if x["team"] != t["id"]]
                save_data(); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  PLAYERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧑 Players":
    st.markdown("## 🧑 Player Profiles")
    team_options = {"All Teams": 0} | {t["name"]: t["id"] for t in db["teams"]}
    filter_team  = st.selectbox("Filter by team", list(team_options.keys()))
    filter_role  = st.selectbox("Filter by role", ["All Roles","Batsman","Bowler","All-rounder","Wicket-keeper"])

    role_map_rev = {"Batsman":"bat","Bowler":"bowl","All-rounder":"all","Wicket-keeper":"wk"}
    players = db["players"]
    if team_options[filter_team]:
        players = [p for p in players if p["team"] == team_options[filter_team]]
    if filter_role != "All Roles":
        players = [p for p in players if p.get("role") == role_map_rev.get(filter_role)]

    if not players:
        st.info("No players found.")
    for p in players:
        t = team_by_id(p["team"])
        tc = t["color"] if t else "#888"
        with st.expander(f"**{p['name']}**  ·  {(t or {}).get('name','Unknown')}  ·  {ROLE_LABELS.get(p.get('role','bat'),'')}", expanded=False):
            col_l, col_r = st.columns([2,1])
            with col_l:
                st.markdown(f"""
                <div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>
                    <div class='avatar' style='background:{tc};width:50px;height:50px;font-size:20px;'>{p["name"][0].upper()}</div>
                    <div>
                        <div style='font-size:18px;font-weight:600;'>{p["name"]}</div>
                        <div style='font-size:13px;color:#666;'>{(t or {}).get("name","")} &nbsp;·&nbsp;
                            <span style='background:{ROLE_COLORS.get(p.get("role","bat"),"#eee")};
                            color:{ROLE_TCOLORS.get(p.get("role","bat"),"#333")};
                            padding:2px 8px;border-radius:8px;font-size:11px;'>
                            {ROLE_LABELS.get(p.get("role","bat"),"")}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Runs",    p.get("runs",0))
                c2.metric("Balls",   p.get("balls",0))
                c3.metric("Fours",   p.get("fours",0))
                c4.metric("Sixes",   p.get("sixes",0))
                c5,c6,c7,c8 = st.columns(4)
                c5.metric("SR",      calc_sr(p.get("runs",0), p.get("balls",0)))
                c6.metric("Wickets", p.get("wkts",0))
                c7.metric("Bowl Ov", fmt_ov(p.get("bowl_balls",0)))
                c8.metric("Economy", calc_eco(p.get("runs_conceded",0), p.get("bowl_balls",0)))
            with col_r:
                if st.button("✏️ Edit", key=f"edit_player_{p['id']}"):
                    st.session_state[f"editing_player_{p['id']}"] = True
                if st.button("🗑️ Delete", key=f"del_player_{p['id']}"):
                    db["players"] = [x for x in db["players"] if x["id"] != p["id"]]
                    save_data(); st.rerun()

            if st.session_state.get(f"editing_player_{p['id']}"):
                with st.form(key=f"form_player_{p['id']}"):
                    st.markdown("**Edit Player**")
                    new_name   = st.text_input("Name",   value=p["name"])
                    team_names = [t2["name"] for t2 in db["teams"]]
                    cur_team   = next((t2["name"] for t2 in db["teams"] if t2["id"] == p["team"]), team_names[0] if team_names else "")
                    new_team_n = st.selectbox("Team", team_names, index=team_names.index(cur_team) if cur_team in team_names else 0)
                    new_role   = st.selectbox("Role", list(ROLE_LABELS.values()),
                                              index=list(ROLE_LABELS.keys()).index(p.get("role","bat")))
                    st.markdown("**Override career stats (optional)**")
                    new_runs   = st.number_input("Career Runs",    value=p.get("runs",0),    min_value=0)
                    new_wkts   = st.number_input("Career Wickets", value=p.get("wkts",0),    min_value=0)
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("💾 Save"):
                        new_team_obj = next((t2 for t2 in db["teams"] if t2["name"] == new_team_n), None)
                        p["name"] = new_name
                        p["team"] = new_team_obj["id"] if new_team_obj else p["team"]
                        p["role"] = list(ROLE_LABELS.keys())[list(ROLE_LABELS.values()).index(new_role)]
                        p["runs"] = new_runs; p["wkts"] = new_wkts
                        save_data()
                        st.session_state[f"editing_player_{p['id']}"] = False
                        st.rerun()
                    if c2.form_submit_button("Cancel"):
                        st.session_state[f"editing_player_{p['id']}"] = False; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE SCORECARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎮 Live Scorecard":
    st.markdown("## 🎮 Live Scorecard")

    live_or_upcoming = [m for m in db["matches"] if m["status"] in ("live","upcoming")]
    if not live_or_upcoming:
        st.info("No live or upcoming matches. Schedule matches in **Manage**.")
        st.stop()

    match_labels = {
        m["id"]: f'{team_by_id(m["teamA"])["name"] if team_by_id(m["teamA"]) else "?"} vs {team_by_id(m["teamB"])["name"] if team_by_id(m["teamB"]) else "?"} · {m.get("date","")} · {m.get("overs",20)} ov'
        for m in live_or_upcoming
    }
    sel_label = st.selectbox("Select match", list(match_labels.values()))
    sel_mid   = next(mid for mid, lbl in match_labels.items() if lbl == sel_label)
    sel_match = match_by_id(sel_mid)

    if sel_match and st.button("🚀 Open / Resume Scorecard", type="primary"):
        if sel_match["status"] == "upcoming":
            sel_match["status"] = "live"
            if not sel_match.get("inn"):
                sel_match["inn"] = [
                    {"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[]},
                    {"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[]}
                ]
        st.session_state.live_match_id = sel_mid
        st.session_state.live_innings  = sel_match["inn"][0].get("innings_done", False) and 2 or 1
        save_data(); st.rerun()

    if st.session_state.live_match_id != sel_mid:
        st.stop()

    m   = match_by_id(sel_mid)
    ta  = team_by_id(m["teamA"]); tb = team_by_id(m["teamB"])
    if not m.get("inn"): st.stop()

    cur_inn_idx = 1 if m["inn"][0].get("innings_done") else 0
    inn = m["inn"][cur_inn_idx]
    opp_inn = m["inn"][0] if cur_inn_idx == 1 else None

    # Score header
    i0 = m["inn"][0]; i1 = m["inn"][1]
    c1,c2,c3 = st.columns([5,1,5])
    with c1:
        st.markdown(f"<div style='background:{ta['color']};color:white;border-radius:12px;padding:12px 16px;text-align:center;'>"
                    f"<div style='font-family:Barlow Condensed;font-size:14px;'>{ta['name']}</div>"
                    f"<div style='font-family:Barlow Condensed;font-size:32px;font-weight:700;'>{i0['runs']}/{i0['wickets']}</div>"
                    f"<div style='font-size:12px;opacity:.8;'>{fmt_ov(i0['balls'])} ov</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='text-align:center;padding-top:28px;font-size:18px;color:#888;font-weight:600;'>vs</div>", unsafe_allow_html=True)
    with c3:
        score2 = f"{i1['runs']}/{i1['wickets']}" if i1.get("balls",0)>0 or cur_inn_idx==1 else "—"
        ov2    = f"{fmt_ov(i1['balls'])} ov" if i1.get("balls",0)>0 else "Yet to bat"
        st.markdown(f"<div style='background:{tb['color']};color:white;border-radius:12px;padding:12px 16px;text-align:center;'>"
                    f"<div style='font-family:Barlow Condensed;font-size:14px;'>{tb['name']}</div>"
                    f"<div style='font-family:Barlow Condensed;font-size:32px;font-weight:700;'>{score2}</div>"
                    f"<div style='font-size:12px;opacity:.8;'>{ov2}</div></div>", unsafe_allow_html=True)

    if cur_inn_idx == 1 and opp_inn:
        target = opp_inn["runs"] + 1
        need   = target - inn["runs"]
        b_left = m["overs"] * 6 - inn["balls"]
        rrr    = round(need / (b_left / 6), 2) if b_left > 0 else 0
        st.markdown(f"""
        <div style='background:#e8f5e9;border:1px solid #a5d6a7;border-radius:10px;padding:10px;text-align:center;margin-top:8px;'>
            <span style='color:#1a6b3c;font-weight:600;'>{tb["name"] if cur_inn_idx else ta["name"]} need {max(0,need)} runs from {b_left} balls &nbsp;·&nbsp; RRR: {rrr}</span>
        </div>""", unsafe_allow_html=True)

    if m.get("result"):
        st.success(f"🏆 {m['result']}")
        if st.button("📋 View Scorecard Summary"):
            pass
        st.stop()

    st.divider()
    st.markdown(f"**Innings {cur_inn_idx+1}** — {'1st batting' if cur_inn_idx==0 else '2nd batting'}")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        striker    = st.text_input("🏏 Striker (on-strike)", key="lv_striker",    placeholder="Batsman name")
    with col_b:
        nstriker   = st.text_input("🏏 Non-striker",         key="lv_nstriker",   placeholder="Batsman name")
    with col_c:
        bowler_name= st.text_input("🎳 Bowler",              key="lv_bowler",     placeholder="Bowler name")

    st.markdown("**Add delivery**")
    bc = st.columns(10)
    ball_map = {0:"0",1:"1",2:"2",3:"3",4:"4",6:"6","W":"W","wd":"Wd","nb":"Nb"}
    ball_colors = {4:"#E3F2FD",6:"#C8E6C9","W":"#FFCDD2","wd":"#FFF8E1","nb":"#FFF8E1"}

    def add_ball(run):
        if not inn: return
        s = striker.strip() or "Batsman A"
        ns= nstriker.strip() or "Batsman B"
        bw= bowler_name.strip() or "Bowler"
        if s not in inn["batsmen"]:
            inn["batsmen"][s] = {"runs":0,"balls":0,"fours":0,"sixes":0,"out":False}
        if bw not in inn["bowlers"]:
            inn["bowlers"][bw] = {"balls":0,"completed_overs":0,"runs":0,"wickets":0}
        b  = inn["batsmen"][s]
        bwl= inn["bowlers"][bw]
        inn["history"].append({"run": str(run), "striker": s, "nstriker": ns, "bowler": bw})
        if run in ("wd","nb"):
            inn["runs"] += 1; inn["extras"] += 1; bwl["runs"] += 1
            inn["overBalls"].append(run)
        elif run == "W":
            b["balls"] += 1; b["out"] = True
            bwl["balls"] += 1; bwl["wickets"] += 1
            inn["balls"] += 1; inn["wickets"] += 1
            inn["overBalls"].append("W")
            _check_over(bwl)
            if inn["wickets"] >= 10:
                _end_innings(); save_data(); st.rerun(); return
        else:
            b["runs"] += run; b["balls"] += 1
            bwl["runs"] += run; bwl["balls"] += 1
            inn["runs"] += run; inn["balls"] += 1
            if run == 4: b["fours"] += 1; inn["fours"] += 1
            if run == 6: b["sixes"] += 1; inn["sixes"] += 1
            inn["overBalls"].append(str(run))
            if run % 2 == 1: _swap_strike()
            _check_over(bwl)
        if inn["balls"] >= m["overs"] * 6:
            _end_innings(); save_data(); st.rerun(); return
        if cur_inn_idx == 1:
            target = opp_inn["runs"] + 1
            if inn["runs"] >= target:
                wleft = 10 - inn["wickets"]
                _finish_match(f"{tb['name'] if cur_inn_idx else ta['name']} win by {wleft} wicket{'s' if wleft!=1 else ''}!")
                save_data(); st.rerun(); return
        save_data(); st.rerun()

    def _swap_strike():
        cur_s  = st.session_state.get("lv_striker","")
        cur_ns = st.session_state.get("lv_nstriker","")
        st.session_state["lv_striker"]  = cur_ns
        st.session_state["lv_nstriker"] = cur_s

    def _check_over(bwl):
        if inn["balls"] > 0 and inn["balls"] % 6 == 0:
            bwl["completed_overs"] = bwl.get("completed_overs",0) + 1
            bwl["balls"] = 0
            inn["overBalls"] = []
            _swap_strike()

    def _end_innings():
        inn["innings_done"] = True
        if cur_inn_idx == 0:
            st.session_state["lv_striker"] = ""
            st.session_state["lv_nstriker"] = ""
            st.session_state["lv_bowler"] = ""

    def _finish_match(result_text):
        m["result"] = result_text
        m["status"] = "completed"
        inn["innings_done"] = True
        _update_points()

    def _update_points():
        ta2 = team_by_id(m["teamA"]); tb2 = team_by_id(m["teamB"])
        for t2 in [ta2, tb2]:
            if not t2: continue
            t2.setdefault("played", 0); t2.setdefault("won",0)
            t2.setdefault("lost",0);   t2.setdefault("tied",0); t2.setdefault("pts",0)
            t2["played"] += 1
        result = m.get("result","")
        if ta2 and ta2["name"] in result:
            ta2["won"] += 1; ta2["pts"] += 2
            if tb2: tb2["lost"] += 1
        elif tb2 and tb2["name"] in result:
            tb2["won"] += 1; tb2["pts"] += 2
            if ta2: ta2["lost"] += 1
        else:
            if ta2: ta2["pts"] += 1; ta2["tied"] += 1
            if tb2: tb2["pts"] += 1; tb2["tied"] += 1

    run_vals = [0,1,2,3,4,6,"W","wd","nb"]
    btn_labels = ["0","1","2","3","4️⃣","6️⃣","🔴W","Wd","Nb"]
    cols = st.columns(len(run_vals)+1)
    for i,(rv,lbl) in enumerate(zip(run_vals,btn_labels)):
        if cols[i].button(lbl, key=f"ball_{rv}", use_container_width=True):
            add_ball(rv)
    if cols[-1].button("↩️ Undo", key="undo_ball", use_container_width=True):
        if inn.get("history"):
            last = inn["history"].pop()
            if inn["overBalls"]: inn["overBalls"].pop()
            run = last["run"]
            s   = last["striker"]; bw = last["bowler"]
            if run in ("wd","nb"):
                inn["runs"] -= 1; inn["extras"] -= 1
                if bw in inn["bowlers"]: inn["bowlers"][bw]["runs"] -= 1
            elif run == "W":
                if s in inn["batsmen"]:
                    inn["batsmen"][s]["balls"] -= 1; inn["batsmen"][s]["out"] = False
                if bw in inn["bowlers"]:
                    inn["bowlers"][bw]["balls"] -= 1; inn["bowlers"][bw]["wickets"] -= 1
                inn["balls"] -= 1; inn["wickets"] -= 1
            else:
                rv = int(run)
                if s in inn["batsmen"]:
                    inn["batsmen"][s]["runs"] -= rv
                    inn["batsmen"][s]["balls"] -= 1
                    if rv==4: inn["batsmen"][s]["fours"] -= 1; inn["fours"] -= 1
                    if rv==6: inn["batsmen"][s]["sixes"] -= 1; inn["sixes"] -= 1
                if bw in inn["bowlers"]:
                    inn["bowlers"][bw]["balls"] -= 1; inn["bowlers"][bw]["runs"] -= rv
                inn["runs"] -= rv; inn["balls"] -= 1
            save_data(); st.rerun()

    # Current over balls
    if inn.get("overBalls"):
        st.markdown("**Current over:**")
        ball_html = "".join([
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:28px;height:28px;border-radius:50%;font-size:11px;font-weight:600;margin-right:4px;"
            f"background:{'#FFCDD2' if b=='W' else '#C8E6C9' if b=='6' else '#BBDEFB' if b=='4' else '#FFF8E1' if b in ('wd','nb') else '#E8EDE8'};"
            f"color:{'#B71C1C' if b=='W' else '#1B5E20' if b=='6' else '#0C447C' if b=='4' else '#E65100' if b in ('wd','nb') else '#333'};'>{b}</span>"
            for b in inn["overBalls"]
        ])
        st.markdown(ball_html, unsafe_allow_html=True)

    if inn.get("innings_done") and cur_inn_idx == 0:
        st.warning("1st innings complete!")
        if st.button("▶️ Start 2nd Innings", type="primary"):
            save_data(); st.rerun()
        st.stop()

    # Batting scorecard
    col_bat, col_bowl = st.columns(2)
    with col_bat:
        st.markdown("**Batting**")
        bats = inn.get("batsmen", {})
        if bats:
            rows = []
            for name, b in bats.items():
                rows.append({
                    "Batsman": name + (" *" if not b["out"] else " (out)"),
                    "R": b["runs"], "B": b["balls"],
                    "4s": b["fours"], "6s": b["sixes"],
                    "SR": calc_sr(b["runs"], b["balls"])
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No batting data yet")

    with col_bowl:
        st.markdown("**Bowling**")
        bwls = inn.get("bowlers", {})
        if bwls:
            rows = []
            for name, bw in bwls.items():
                total_balls = bw.get("balls",0) + bw.get("completed_overs",0)*6
                rows.append({
                    "Bowler": name,
                    "O": fmt_ov(total_balls),
                    "R": bw["runs"], "W": bw["wickets"],
                    "Eco": calc_eco(bw["runs"], total_balls)
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No bowling data yet")

# ══════════════════════════════════════════════════════════════════════════════
#  MANAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "➕ Manage":
    st.markdown("## ➕ Manage")
    tab_team, tab_player, tab_match = st.tabs(["🏏 Add Team", "🧑 Add Player", "📅 Schedule Match"])

    with tab_team:
        st.markdown("### Add New Team")
        with st.form("form_add_team"):
            c1, c2 = st.columns(2)
            t_name  = c1.text_input("Team name *", placeholder="e.g. Sales Warriors")
            t_cap   = c2.text_input("Captain name", placeholder="e.g. Rahul Mehta")
            t_color = st.color_picker("Team jersey color", value="#1565C0")
            if st.form_submit_button("➕ Add Team", type="primary"):
                if t_name.strip():
                    db["teams"].append({
                        "id": db["next_team_id"],
                        "name": t_name.strip(), "captain": t_cap.strip(),
                        "color": t_color, "played":0,"won":0,"lost":0,"tied":0,"pts":0
                    })
                    db["next_team_id"] += 1
                    save_data()
                    st.success(f"✅ Team **{t_name}** added!")
                else:
                    st.error("Team name is required")

    with tab_player:
        st.markdown("### Add New Player")
        if not db["teams"]:
            st.warning("Add at least one team first.")
        else:
            with st.form("form_add_player"):
                c1, c2 = st.columns(2)
                p_name = c1.text_input("Player name *", placeholder="e.g. Virat Singh")
                p_team = c2.selectbox("Team *", [t["name"] for t in db["teams"]])
                c3, c4 = st.columns(2)
                p_role = c3.selectbox("Role", list(ROLE_LABELS.values()))
                p_jersey = c4.text_input("Jersey number", placeholder="e.g. 18")
                if st.form_submit_button("➕ Add Player", type="primary"):
                    if p_name.strip():
                        team_obj  = next(t for t in db["teams"] if t["name"] == p_team)
                        role_key  = list(ROLE_LABELS.keys())[list(ROLE_LABELS.values()).index(p_role)]
                        db["players"].append({
                            "id": db["next_player_id"],
                            "name": p_name.strip(), "team": team_obj["id"],
                            "role": role_key, "jersey": p_jersey,
                            "runs":0,"balls":0,"fours":0,"sixes":0,
                            "wkts":0,"bowl_balls":0,"runs_conceded":0,
                            "innings_played":0
                        })
                        db["next_player_id"] += 1
                        save_data()
                        st.success(f"✅ Player **{p_name}** added to **{p_team}**!")
                    else:
                        st.error("Player name is required")

    with tab_match:
        st.markdown("### Schedule a Match")
        if len(db["teams"]) < 2:
            st.warning("Need at least 2 teams to schedule a match.")
        else:
            with st.form("form_add_match"):
                team_names = [t["name"] for t in db["teams"]]
                c1, c2 = st.columns(2)
                m_ta    = c1.selectbox("Team A *", team_names, index=0)
                m_tb    = c2.selectbox("Team B *", team_names, index=1 if len(team_names)>1 else 0)
                c3, c4, c5 = st.columns(3)
                m_date  = c3.date_input("Date *", value=date.today())
                m_time  = c4.time_input("Time *")
                m_overs = c5.selectbox("Overs", [5,10,15,20,50], index=3)
                m_venue = st.text_input("Venue / Ground", placeholder="e.g. Company Ground A")
                m_notes = st.text_area("Notes (optional)", placeholder="Any notes about the match")
                if st.form_submit_button("📅 Schedule Match", type="primary"):
                    if m_ta == m_tb:
                        st.error("Both teams cannot be the same")
                    else:
                        ta_id = next(t["id"] for t in db["teams"] if t["name"] == m_ta)
                        tb_id = next(t["id"] for t in db["teams"] if t["name"] == m_tb)
                        db["matches"].append({
                            "id": db["next_match_id"],
                            "teamA": ta_id, "teamB": tb_id,
                            "date": str(m_date), "time": str(m_time),
                            "venue": m_venue or "TBD", "overs": m_overs,
                            "notes": m_notes, "status": "upcoming",
                            "inn": [
                                {"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[],"innings_done":False},
                                {"runs":0,"wickets":0,"balls":0,"extras":0,"fours":0,"sixes":0,"batsmen":{},"bowlers":{},"overBalls":[],"history":[],"innings_done":False}
                            ],
                            "result": ""
                        })
                        db["next_match_id"] += 1
                        save_data()
                        st.success(f"✅ Match **{m_ta} vs {m_tb}** scheduled on {m_date}!")

# ══════════════════════════════════════════════════════════════════════════════
#  LEAGUE SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ League Settings":
    st.markdown("## ⚙️ League Settings")

    with st.form("form_league_settings"):
        st.markdown("### League Details")
        new_name    = st.text_input("League name",    value=db["league_name"])
        new_edition = st.text_input("Edition/Season", value=db["league_edition"])
        if st.form_submit_button("💾 Save Settings", type="primary"):
            db["league_name"]    = new_name
            db["league_edition"] = new_edition
            save_data()
            st.success("✅ Settings saved!")
            st.rerun()

    st.divider()
    st.markdown("### Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export Data as JSON"):
            st.download_button(
                label="⬇️ Download cricket_data.json",
                data=json.dumps(db, indent=2, default=str),
                file_name="cricket_league_data.json",
                mime="application/json"
            )
    with col2:
        uploaded = st.file_uploader("📤 Import Data (JSON)", type="json")
        if uploaded:
            imported = json.load(uploaded)
            st.session_state.db = imported
            save_data()
            st.success("✅ Data imported!")
            st.rerun()

    st.divider()
    with st.expander("⚠️ Danger Zone", expanded=False):
        st.warning("These actions are irreversible!")
        c1, c2, c3 = st.columns(3)
        if c1.button("🗑️ Clear All Matches"):
            db["matches"] = []; save_data(); st.rerun()
        if c2.button("🗑️ Clear All Players"):
            db["players"] = []; save_data(); st.rerun()
        if c3.button("🗑️ Reset Everything"):
            st.session_state.db = DEFAULT_DATA.copy()
            save_data(); st.rerun()

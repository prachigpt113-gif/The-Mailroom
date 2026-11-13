import streamlit as st
import random, string, json, os, html, base64
import pandas as pd
from collections import Counter
from openai import OpenAI

# ---------- Session setup (before page config, so the PM screen can go wide) ----------
for key, default in {"role": None, "user": None, "code": None, "submitted": False,
                     "sent_reply": False, "plan": None, "guard": None, "closed_msg": False}.items():
    if key not in st.session_state:
        st.session_state[key] = default

IS_PM = st.session_state.role == "pm"
st.set_page_config(page_title="The Mailroom", page_icon="", layout="wide" if IS_PM else "centered")
st.markdown(f"""
<style>
.block-container {{max-width: {1200 if IS_PM else 760}px; padding-top: 1.5rem;}}
#MainMenu, footer, header {{visibility: hidden;}}
h3 {{font-size: 1.3rem !important;}}

/* Cards, with color-block tones */
[class*="st-key-card_"] {{
    background: #FFFFFF;
    border-radius: 16px !important;
    border: 1px solid #ECE4D8 !important;
    box-shadow: 0 1px 2px rgba(43,29,32,.05), 0 6px 18px rgba(43,29,32,.06);
}}
[class*="st-key-card_rose_"]  {{background: #FBF1F2 !important; border-color: #F0D9DC !important;}}
[class*="st-key-card_sage_"]  {{background: #EEF5EF !important; border-color: #D7E7DA !important;}}
[class*="st-key-card_sand_"]  {{background: #F6F1E9 !important; border-color: #EAE0D2 !important;}}
[class*="st-key-card_amber_"] {{background: #FBF3E3 !important; border-color: #F0DFBC !important;}}
[data-testid="stCheckbox"] label p {{white-space: normal !important;}}

/* Logo as a clean circle */
.band-logo {{border-radius: 50%; background: #FFFFFF; flex-shrink: 0;
             box-shadow: 0 0 0 3px rgba(255,255,255,.25);}}

/* PM masthead: maroon band */
.st-key-band_pm {{
    background: #7A2A35; border-radius: 20px; padding: 1.2rem 1.5rem 1.3rem;
    margin-bottom: .6rem; box-shadow: 0 8px 24px rgba(122,42,53,.18);
}}
.masthead-kicker {{font-size: .78rem; letter-spacing: .18em; text-transform: uppercase;
                   color: rgba(255,255,255,.8); font-weight: 700; margin-bottom: .1rem;}}
.masthead-title {{font-family: serif; font-size: 2.4rem; line-height: 1.15; font-weight: 700; color: #FFFFFF;}}
.chips {{display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .55rem;}}
.chip {{background: rgba(255,255,255,.15); color: #FFFFFF; border-radius: 999px;
        padding: .2rem .8rem; font-size: .85rem;}}
.chip.sealed {{background: #E6F0E8; color: #2F5D3A;}}
.weekbar {{height: 6px; background: rgba(255,255,255,.2); border-radius: 999px; margin-top: .7rem; overflow: hidden;}}
.weekbar > div {{height: 100%; background: #F1ECE4; border-radius: 999px;}}

/* Team header band */
.band {{background: #7A2A35; color: #FAF7F2; border-radius: 20px; padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem; box-shadow: 0 8px 24px rgba(122,42,53,.18);}}
.band-row {{display: flex; gap: 1.1rem; align-items: center;}}
.band-kicker {{font-size: .72rem; letter-spacing: .2em; text-transform: uppercase; opacity: .8; font-weight: 700;}}
.band-title {{font-family: serif; font-size: 1.8rem; font-weight: 700; line-height: 1.2; color: #FFFFFF;}}
.band-sub {{opacity: .92; margin-top: .25rem; line-height: 1.45;}}

/* Keep-an-eye-on tags */
.tag {{display: inline-block; border-radius: 999px; padding: .05rem .6rem; font-size: .78rem;
       font-weight: 600; margin-right: .4rem;}}
.tag-persistent {{background: #F4E3E5; color: #7A2A35;}}
.tag-new {{background: #FBF0DC; color: #8A5A12;}}
.tag-improving {{background: #E6F0E8; color: #2F5D3A;}}
.watch-item {{margin-bottom: .9rem; line-height: 1.55;}}

/* Landing page */
.hero-kicker {{text-align: center; font-size: .8rem; letter-spacing: .22em; text-transform: uppercase;
               color: #7A2A35; font-weight: 700; margin-top: .4rem;}}
.hero-title {{text-align: center; font-family: serif; font-size: 2.7rem; line-height: 1.12;
              font-weight: 700; color: #2B1D20; margin: .4rem 0 .7rem;}}
.hero-sub {{text-align: center; font-size: 1.1rem; color: #5A4A4D; max-width: 560px;
            margin: 0 auto 1.6rem; line-height: 1.5;}}
.steps {{display: flex; gap: .8rem; margin: 0 0 1.6rem;}}
.step {{flex: 1; background: #FFFFFF; border: 1px solid #ECE4D8; border-radius: 14px;
        padding: .9rem 1rem; box-shadow: 0 4px 14px rgba(43,29,32,.05);}}
.step b {{display: block; color: #7A2A35; margin-bottom: .25rem;}}
.step span {{font-size: .9rem; color: #5A4A4D; line-height: 1.4;}}
.hero-note {{text-align: center; font-size: .85rem; color: #8A7B7E; margin-top: .8rem;}}
@media (max-width: 640px) {{ .steps {{flex-direction: column;}} .hero-title {{font-size: 2rem;}}
                             .band-title, .masthead-title {{font-size: 1.6rem;}} }}
/* Inputs: clearly visible fields */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"] {{
    background: #FFFDF9 !important; border: 1.5px solid #CDBDAA !important; border-radius: 10px !important;
}}
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {{
    border-color: #7A2A35 !important; box-shadow: 0 0 0 3px rgba(122,42,53,.12) !important;
}}
[data-testid="stWidgetLabel"] p {{font-weight: 600 !important; color: #2B1D20 !important; font-size: 1rem !important;}}
[data-testid*="Caption"], [data-testid*="Caption"] *, .stCaption, .stCaption *, small {{color: #1A1112 !important; opacity: 1 !important; font-size: .95rem !important;}}

/* Follow-ups: light maroon block */
.st-key-band_followups {{
    background: #F6E7E9; border: 1px solid #EBCFD3; border-radius: 20px;
    padding: 1.2rem 1.4rem; margin: .4rem 0 1rem; box-shadow: 0 6px 20px rgba(122,42,53,.08);
}}
.st-key-band_followups h3 {{color: #7A2A35 !important;}}

/* Slightly deeper card shadow */
[class*="st-key-card_"] {{box-shadow: 0 2px 4px rgba(43,29,32,.06), 0 10px 24px rgba(43,29,32,.08) !important;}}
</style>
""", unsafe_allow_html=True)

# Every card gets a unique key, so the CSS above can style it. Tones: white, rose, sage, sand, amber
_card_ids = iter(range(100000))
def card(tone="white"):
    return st.container(border=True, key=f"card_{tone}_{next(_card_ids)}")

@st.cache_data
def logo_b64():
    if os.path.exists("logo.svg"):
        with open("logo.svg", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def logo_img(size):
    b = logo_b64()
    if not b:
        return '<span style="font-size:2rem"></span>'
    return f'<img src="data:image/svg+xml;base64,{b}" class="band-logo" style="width:{size}px;height:{size}px">'

def team_band(title, subtitle, chips=None):
    chip_html = ""
    if chips:
        chip_html = '<div class="chips">' + "".join(
            f'<span class="chip{" sealed" if "Sealed" in c else ""}">{c}</span>' for c in chips) + "</div>"
    st.markdown(f"""<div class="band"><div class="band-row">{logo_img(68)}<div>
<div class="band-kicker">The Mailroom</div>
<div class="band-title">{title}</div>
<div class="band-sub">{subtitle}</div>
{chip_html}
</div></div></div>""", unsafe_allow_html=True)

DATA_FILE = "mailroom_data.json"
TOTAL_WEEKS = 6
RISKS = ["Unclear requirements", "Timeline too tight", "Dependency on other team",
         "Technical unknowns", "Resourcing", "Something else"]
HELPS = ["Clear priorities", "More time", "Another pair of hands",
         "A decision from leadership", "Something else"]
TEXT_FIELDS = {"risk_detail": "Tell us more", "help_detail": "Anything specific?",
               "other": "Anything else your PM should know?"}

# ---------- Storage: a simple file both windows can read ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
    else:
        data = {"project": None, "checkins": [], "checked_in": []}
    data.setdefault("followups", [])
    data.setdefault("history", {})             # per week: AI themes, checklist, next questions (never raw answers)
    data.setdefault("confidence_history", [])
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def new_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

def save_checkin(data, name, answers):
    # Voting-booth rule: answers and names live in two separate lists
    data["checkins"].append(answers)
    random.shuffle(data["checkins"])                    # order can't reveal who answered when
    data["checked_in"] = sorted(data["checked_in"] + [name])
    save_data(data)

# ---------- Demo data (starts at Week 3, with Weeks 1 and 2 history) ----------
DEMO_Q1 = "Has the scope of upcoming features become clearer since last week?"
DEMO_Q2 = "Is the cross-team dependency now on a committed timeline?"
DEMO_WEEK1 = {
    "themes": "- The scope of an upcoming feature is still being defined.\n"
              "- Testing capacity may be thin for the release.\n"
              "- Overall, the team feels the timeline is achievable.",
    "checklist": [{"text": "Write down the agreed scope for the upcoming feature", "done": False},
                  {"text": "Check testing capacity for the release", "done": False},
                  {"text": "Share the beta milestone plan with the team", "done": True}],
    "questions": [],
}
DEMO_WEEK2 = {
    "themes": "- Requirements for an upcoming feature keep changing.\n"
              "- Progress depends on another team without a committed date.\n"
              "- The team feels pressure on the beta timeline.",
    "checklist": [{"text": "Publish one written source of truth for the spec", "done": True},
                  {"text": "Ask the other team for a committed delivery date", "done": False},
                  {"text": "Review testing capacity before the beta", "done": False}],
    "questions": [DEMO_Q1, DEMO_Q2],
}
DEMO_CHECKINS = [
    {"code": "M4QX", "confidence": 4, "risk": "Unclear requirements",
     "risk_detail": "The payment flow spec changed twice this sprint and the latest version isn't written down anywhere.",
     "help": "Clear priorities", "help_detail": "", "other": "",
     "followthrough": {DEMO_Q1: "No", DEMO_Q2: "No"}},
    {"code": "R7TB", "confidence": 5, "risk": "Dependency on other team",
     "risk_detail": "We're waiting on the platform team's API and they haven't committed to a date.",
     "help": "A decision from leadership", "help_detail": "Someone needs to escalate the API timeline.", "other": "",
     "followthrough": {DEMO_Q1: "Somewhat", DEMO_Q2: "No"}},
    {"code": "A2LK", "confidence": 6, "risk": "Resourcing", "risk_detail": "",
     "help": "Another pair of hands", "help_detail": "", "other": "QA is basically one person.",
     "followthrough": {DEMO_Q1: "Yes", DEMO_Q2: "Somewhat"}},
    {"code": "L9PD", "confidence": 5, "risk": "Unclear requirements",
     "risk_detail": "Not sure if guest checkout is in scope for beta or not.",
     "help": "Clear priorities", "help_detail": "", "other": "",
     "followthrough": {DEMO_Q1: "No", DEMO_Q2: "Somewhat"}},
]
DEMO_NAMES = ["Arin", "Luka", "Mohan", "Rhea"]
DEMO_REPLIES = {
    "Unclear requirements": ["Mostly whether guest checkout is in scope for beta.",
                             "The payment flow. Which version of the spec is final?"],
    "Dependency on other team": ["We need a committed date for the platform API."],
    "Resourcing": ["Even a part-time tester for the last two weeks would help."],
}
DEFAULT_REPLY = "Clearer written decisions after each meeting would help."

# ---------- Sealed AI on NEAR (Confidential TEE) ----------
NEAR_MODEL = "z-ai/glm-5.3-flash"

SUMMARY_RULES = """You summarize anonymous project check-ins for a project manager.
Write 3 to 5 short bullet points describing the shared themes.
Rules:
- Never quote anyone. Paraphrase in neutral language.
- Remove anything that could identify a person: names, team names, tools, roles, locations, unusual phrases.
  Generalize instead, for example "a dependency on another team".
- Never name job roles or functions (like QA, designer, or backend engineer). Describe the work instead, like "testing".
- No preamble. Return only the bullet points."""

REWORD_RULES = """Rewrite this anonymous reply to a project manager in plain, neutral language.
Keep the meaning. Remove names, team names, job roles, and any personal writing style or identifying details.
Return only the rewritten reply, in one or two sentences."""

GUARD_RULES = """You protect the anonymity of someone writing an anonymous note to their project manager.
If the note contains anything that could identify the writer (a name, their role, a team name,
a specific tool or task only they would work on, or distinctive phrasing), reply with a safer
rewrite that keeps the meaning but generalizes those details.
If the note is already safe, reply with exactly: OK
Reply with only OK or the rewrite."""

CHECKLIST_RULES = """You help a project manager act on the anonymous check-in history of one project.
Write exactly 3 concrete actions the PM can take this week, one per line, each under 15 words,
each starting with a verb. Prioritize issues that persist across weeks and planned actions not yet done.
Never suggest identifying or approaching specific individuals.
No numbering, no bullets, no preamble."""

QUESTIONS_RULES = """Write exactly 3 short questions for next week's anonymous team check-in.
Base them on the project history, focusing on persistent issues and actions the PM planned.
Each question must ask about ONE thing only, be under 15 words,
and be answerable with Yes, Somewhat, or No.
Never ask about anyone's role, team, location, or identity.
One per line, no numbering, no bullets, no preamble."""

WATCH_RULES = """You review the anonymous check-in history of one project.
Name the top 3 issues the project manager should keep an eye on.
Prefer issues that persist across weeks, issues where planned actions were not done,
and issues that are not improving.
Never name job roles or functions (like QA, designer, or backend engineer). Describe the work instead, like "testing".
Write one line per issue in exactly this format:
Persistent: the issue — why it matters
Use "Persistent" if it appears in 2 or more weeks, "New" if only this week,
"Improving" if it is getting better. Each line under 25 words. No preamble, no numbering."""

SUGGEST_Q_RULES = """Write one short, open follow-up question a project manager could ask about this risk,
to understand it better. Keep it general: do not repeat specific details from the notes,
and never ask about anyone's identity, role, or team. Return only the question."""

def ask_sealed_ai(rules, text):
    client = OpenAI(base_url="https://cloud-api.near.ai/v1", api_key=st.secrets["NEARAI_API_KEY"])
    response = client.chat.completions.create(
        model=NEAR_MODEL,
        messages=[{"role": "system", "content": rules}, {"role": "user", "content": text}],
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    answer = response.choices[0].message.content or ""
    return answer.split("</think>")[-1].strip()       # drop any leftover "thinking" text

def ai_lines(rules, text, limit=3):
    try:
        answer = ask_sealed_ai(rules, text)
    except Exception:
        return []
    lines = [l.strip().lstrip("-•*0123456789.) ").strip() for l in answer.splitlines()]
    return [l for l in lines if l][:limit]

def build_notes(checkins):
    lines = []
    for c in checkins:
        parts = [f"Risk: {c['risk']}"]
        for field in TEXT_FIELDS:
            if c.get(field):
                parts.append(c[field])
        lines.append(" | ".join(parts))
    return "\n".join(lines)

@st.cache_data(show_spinner=" The sealed AI is reading the notes…")
def themes_cached(notes):
    return ask_sealed_ai(SUMMARY_RULES, notes)

def get_themes(checkins):
    try:
        return themes_cached(build_notes(checkins))
    except Exception:
        return None

def build_context(data, week, themes, checkins):
    # Only AI themes and checklists from past weeks, never raw answers
    parts = []
    for w in sorted(data["history"], key=int):
        h = data["history"][w]
        actions = "; ".join(f"{i['text']} ({'done' if i['done'] else 'not done'})" for i in h["checklist"])
        parts.append(f"Week {w} themes:\n{h['themes']}\nPM actions planned: {actions or 'none'}")
    prev = data["history"].get(str(week - 1))
    if prev and prev["questions"]:
        lines = []
        for q in prev["questions"]:
            a = Counter(c.get("followthrough", {}).get(q) for c in checkins)
            lines.append(f"{q} Yes {a.get('Yes', 0)}, Somewhat {a.get('Somewhat', 0)}, No {a.get('No', 0)}")
        parts.append("Did last week's fixes work?\n" + "\n".join(lines))
    parts.append(f"Week {week} themes (this week):\n{themes}")
    return "\n\n".join(parts)

@st.cache_data(show_spinner=" The sealed AI is comparing this week with earlier weeks…")
def watch_cached(context):
    return ask_sealed_ai(WATCH_RULES, context)

def get_watch_list(context):
    # Returns a list of (tag, text) pairs, e.g. ("persistent", "Requirements keep shifting — ...")
    try:
        text = watch_cached(context)
    except Exception:
        return []
    out = []
    for line in text.splitlines():
        line = line.strip().lstrip("-•*0123456789.) ").strip()
        if not line:
            continue
        first, _, rest = line.partition(" ")
        tag = first.strip("[]:").lower()
        if tag in ("persistent", "new", "improving"):
            out.append((tag, rest.strip()))
        else:
            out.append(("other", line))
    return out[:3]

def ai_reword(text):
    try:
        return ask_sealed_ai(REWORD_RULES, text)
    except Exception:
        # Fail closed: never show a raw reply if it couldn't be reworded
        return "(A reply arrived, but it couldn't be reworded right now, so it's held back to protect the sender.)"

def ai_privacy_check(text):
    try:
        answer = ask_sealed_ai(GUARD_RULES, text)
    except Exception:
        return None
    return None if answer.strip().strip(".").upper() == "OK" else answer

# ---------- Follow-ups ----------
def send_followup(data, theme, question, audience, codes):
    data["followups"].append({"id": new_code(), "theme": theme, "question": question,
                              "audience": audience, "codes": codes,
                              "replies": [], "replied": []})
    save_data(data)

def save_reply(data, fu, code, text):
    fu["replies"].append(ai_reword(text))
    random.shuffle(fu["replies"])                       # reply order can't reveal who answered
    fu["replied"].append(code)
    save_data(data)

# ---------- Callbacks (run before the page redraws) ----------
def accept_safer(field, safer):
    st.session_state[f"f_{field}"] = safer
    st.session_state.guard.pop(field, None)

def dismiss_guard(field):
    st.session_state.guard.pop(field, None)

def suggest_question(theme, checkins):
    notes = "\n".join((c.get("risk_detail") or c.get("other") or "") for c in checkins if c["risk"] == theme)
    try:
        q = ask_sealed_ai(SUGGEST_Q_RULES, f"Risk: {theme}\nNotes:\n{notes}")
    except Exception:
        q = ""
    st.session_state[f"q_{theme}"] = q

def send_inline(theme, audience):
    q = (st.session_state.get(f"q_{theme}") or "").strip()
    if not q:
        return
    d = load_data()
    codes = [c["code"] for c in d["checkins"] if c["risk"] == theme] if audience == "raisers" else []
    if not any(f["theme"] == theme and f["question"] == q for f in d["followups"]): send_followup(d, theme, q, audience, codes)
    st.session_state[f"q_{theme}"] = ""

def go_back():
    for k in ["role", "user", "code", "plan", "guard"]:
        st.session_state[k] = None
    st.session_state.submitted = False

# ---------- Team inbox ----------
def show_inbox(data):
    code = st.session_state.code
    if st.session_state.sent_reply:
        st.success("Reply sealed and delivered")
        st.session_state.sent_reply = False
    mail = [fu for fu in data["followups"]
            if (fu["audience"] == "all" or code in fu["codes"]) and code not in fu["replied"]]
    for fu in mail:
        with card("rose"):
            if fu["audience"] == "raisers":
                st.write("**Your PM asked about a risk you raised**")
            else:
                st.write("**Your PM asked the whole team**")
            st.write(f"*{fu['question']}*")
            st.caption("Your reply is sealed and reworded by the sealed AI. Your PM won't know it came from you.")
            reply = st.text_area("Your reply", key=f"r_{fu['id']}")
            if st.button("Send reply", key=f"s_{fu['id']}", type="primary"):
                if reply.strip():
                    with st.spinner(" Sealing your reply…"):
                        save_reply(data, fu, code, reply.strip())
                    st.session_state.sent_reply = True
                    st.rerun()
                else:
                    st.warning("Write a reply first.")
    c1, c2 = st.columns([4, 1])
    if not mail:
        c1.caption("No new mail. Follow-up questions from your PM will appear here.")
    if c2.button("Refresh inbox"):
        st.rerun()

# ---------- PM dashboard pieces ----------
def masthead(data, project):
    week = project.get("week", 1)
    with st.container(key="band_pm"):
        m1, m2, m3 = st.columns([1.2, 9, 1.4], vertical_alignment="center")
        with m1:
            st.markdown(logo_img(88), unsafe_allow_html=True)
        with m2:
            pct = int(week / TOTAL_WEEKS * 100)
            name = html.escape(project["name"])
            milestone = html.escape(project["milestone"])
            st.markdown(f"""<div class="masthead-kicker">The Mailroom · PM dashboard</div>
<div class="masthead-title">Project {name}</div>
<div class="chips">
<span class="chip">Week {week} of {TOTAL_WEEKS}</span>
<span class="chip"> {milestone}</span>
<span class="chip"> {len(data['checked_in'])} of {len(project['team'])} checked in</span>
<span class="chip sealed"> Sealed by NEAR AI</span>
</div>
<div class="weekbar"><div style="width:{pct}%"></div></div>""", unsafe_allow_html=True)
        with m3:
            b1, b2 = st.columns(2)
            b1.button("←", key="pm_back", on_click=go_back, help="Back to start")
            if b2.button("↻", key="pm_refresh", help="Refresh"):
                st.rerun()

def checklist_card(data, week):
    prev = data["history"].get(str(week - 1))
    st.write("**This week's checklist**")
    if not prev or not prev["checklist"]:
        st.caption("Your checklist appears after you wrap up a week.")
        return
    changed = False
    for i, item in enumerate(prev["checklist"]):
        done = st.checkbox(item["text"], value=item["done"], key=f"cl_{week}_{i}")
        if done != item["done"]:
            item["done"] = done
            changed = True
    if changed:
        save_data(data)

def recap_card(data, week, checkins):
    prev = data["history"].get(str(week - 1))
    with card():
        if not prev:
            st.subheader("Last week")
            st.caption("No earlier weeks yet. Your recap appears after you wrap up a week.")
            return
        st.subheader(f"Week {week - 1} recap")
        st.write("**What the team raised**")
        st.markdown(prev["themes"])
        if prev["questions"] and checkins:
            st.write("**Did the fixes work?**")
            n = len(checkins)
            for q in prev["questions"]:
                a = Counter(c.get("followthrough", {}).get(q) for c in checkins)
                st.caption(q)
                for label in ["Yes", "Somewhat", "No"]:
                    st.progress(a.get(label, 0) / n, text=f"{label}: {a.get(label, 0)}")

def show_pm_dashboard(data, project):
    checkins = data["checkins"]
    n, team_size = len(checkins), len(project["team"])
    week = project.get("week", 1)
    unlocked = n >= 4
    themes = get_themes(checkins) if unlocked else None
    context = build_context(data, week, themes, checkins) if themes else None
    avg = round(sum(c["confidence"] for c in checkins) / n, 1) if unlocked else None

    # ---- Row 1: Radar (chart + checklist) | Keep an eye on ----
    left, right = st.columns([2, 1])
    with left:
        with card():
            st.subheader("Radar")
            chart_col, list_col = st.columns([3, 2])
            with chart_col:
                if unlocked:
                    hist = data["confidence_history"]
                    st.metric("Team confidence", f"{avg} / 10",
                              delta=round(avg - hist[-1], 1) if hist else None)
                    chart = pd.DataFrame({"Confidence": hist + [avg]},
                                         index=[f"Week {i+1}" for i in range(len(hist) + 1)])
                    st.line_chart(chart, height=200, color="#7A2A35")
                else:
                    st.info(f"The radar unlocks at 4 check-ins, so nobody can be singled out. ({n} so far)")
            with list_col:
                checklist_card(data, week)
    with right:
        with card("rose"):
            st.subheader("Keep an eye on")
            if context:
                watch = get_watch_list(context)
                if watch:
                    labels = {"persistent": "Persistent", "new": "New", "improving": "Improving"}
                    for tag, text in watch:
                        pill = f'<span class="tag tag-{tag}">{labels[tag]}</span>' if tag in labels else ""
                        st.markdown(f'<div class="watch-item">{pill}{html.escape(text)}</div>',
                                    unsafe_allow_html=True)
                    st.caption(" The sealed AI compared this week with earlier weeks. No one's words were stored.")
                else:
                    st.caption("The sealed AI couldn't compare weeks just now.")
            else:
                st.caption("Appears once the radar unlocks.")

    # ---- Row 2: Last week recap | What would help ----
    l2, r2 = st.columns([2, 1])
    with l2:
        recap_card(data, week, checkins)
    with r2:
        with card("sand"):
            st.subheader("What would help")
            if unlocked:
                for h, count in Counter(c["help"] for c in checkins).most_common():
                    st.write(f"**{count} of {n}** · {h}")
            else:
                st.caption("Appears once the radar unlocks.")

    if not unlocked:
        return

    # ---- Row 3: Follow-ups (full width) ----
    with st.container(key="band_followups"):
        st.subheader("Follow-ups"); st.caption("Ask about any risk. Risks raised by one person go to the whole team, so nobody is singled out.")
        for risk, count in Counter(c["risk"] for c in checkins).most_common():
            audience = "raisers" if count >= 2 else "all"
            who = "the people who raised it" if audience == "raisers" else "the whole team"
            with card():
                st.write(f"**{count} of {n} flagged · {risk}** · questions go to {who}")
                for fu in [f for f in data["followups"] if f["theme"] == risk]:
                    expected = len(fu["codes"]) if fu["audience"] == "raisers" else team_size
                    st.write(f"{fu['question']}")
                    for r in fu["replies"]:
                        st.write(f"↳ {r}")
                    waiting = expected - len(fu["replies"])
                    st.caption(f"Responses {len(fu['replies'])} of {expected}"
                               + (f" · {waiting} awaited" if waiting > 0 else ""))
                q1, q2, q3 = st.columns([6, 1.4, 1])
                q1.text_input("Ask a follow-up", key=f"q_{risk}", label_visibility="collapsed",
                              placeholder="Ask a follow-up question…")
                q2.button(" Suggest", key=f"sug_{risk}", on_click=suggest_question, args=(risk, checkins))
                q3.button("Send", key=f"send_{risk}", type="primary", on_click=send_inline, args=(risk, audience))
        st.caption(" Each reply is reworded by the sealed AI, so writing style can't identify anyone.")

    # ---- Row 4: Notes | Wrap up ----
    l4, r4 = st.columns([1, 1])
    with l4:
        with card():
            st.subheader("What the notes say")
            if themes:
                st.markdown(themes)
                st.caption(" Written by sealed AI on NEAR (Confidential TEE). You see themes, never quotes.")
            else:
                st.warning("The sealed AI couldn't be reached just now. Try ↻ refresh in a moment.")
    with r4:
        with card("sage"):
            st.subheader(f"Wrap up Week {week}")
            st.caption("The sealed AI drafts your next steps from the project's history. "
                       "When you close the week, raw answers are deleted and only the AI's themes are kept.")
            if not themes:
                st.caption("Available once the notes summary loads.")
                return
            if st.button(f" Prepare Week {week + 1}"):
                with st.spinner(" The sealed AI is drafting your next steps…"):
                    st.session_state.plan = {"checklist": ai_lines(CHECKLIST_RULES, context),
                                             "questions": ai_lines(QUESTIONS_RULES, context)}
            plan = st.session_state.plan
            if plan:
                if not plan["checklist"] and not plan["questions"]:
                    st.warning("The sealed AI couldn't draft next steps just now. Try again.")
                st.write("**Suggested actions for you**")
                for item in plan["checklist"]:
                    st.write(f"☐ {item}")
                st.write(f"**Questions for Week {week + 1}'s check-in** (untick any you don't want)")
                chosen = [q for i, q in enumerate(plan["questions"]) if st.checkbox(q, value=True, key=f"pq_{i}")]
                c1, c2 = st.columns(2)
                if c1.button("↻ New question ideas"):
                    with st.spinner(" Drafting new questions…"):
                        st.session_state.plan["questions"] = ai_lines(QUESTIONS_RULES, context)
                    st.rerun()
                if c2.button(f"Close Week {week} & start Week {week + 1}", type="primary"):
                    data["history"][str(week)] = {"themes": themes,
                                                  "checklist": [{"text": t, "done": False} for t in plan["checklist"]],
                                                  "questions": chosen}
                    data["confidence_history"].append(avg)
                    data["checkins"], data["checked_in"], data["followups"] = [], [], []   # raw answers deleted
                    project["week"] = week + 1
                    save_data(data)
                    st.session_state.plan = None
                    st.session_state.closed_msg = True
                    st.rerun()

def submit_checkin(data, answers):
    save_checkin(data, st.session_state.user, answers)
    st.session_state.submitted = True
    st.session_state.guard = None
    st.rerun()

# ---------- Page ----------
data = load_data()

# Small logo on the "create project" screen (other screens draw their own)
if IS_PM and not data["project"]:
    if os.path.exists("logo.svg"):
        st.markdown(logo_img(90), unsafe_allow_html=True)
    else:
        st.title("The Mailroom")

# ---------- Landing ----------
if st.session_state.role is None:
    _, mid, _ = st.columns([1.3, 1, 1.3])
    with mid:
        if os.path.exists("logo.svg"):
            st.markdown(f'<div style="text-align:center">{logo_img(180)}</div>', unsafe_allow_html=True)
    st.markdown("""<div class="hero-kicker">The Mailroom</div>
<div class="hero-title">Say what you can't say in standup.</div>
<div class="hero-sub">Honest weekly project check-ins, sealed by private AI on NEAR.
Your PM sees patterns, never names.</div>
<div class="steps">
<div class="step"><b>① Check in privately</b><span>Four quick questions. 60 seconds. No names attached.</span></div>
<div class="step"><b>② Sealed AI reads it</b><span>Answers are read only inside NEAR's locked hardware.</span></div>
<div class="step"><b>③ Your PM sees patterns</b><span>Themes, risks and next steps. Never who said what.</span></div>
</div>""", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    if b1.button("I'm a PM  →", type="primary", width="stretch"):
        st.session_state.role = "pm"
        st.rerun()
    if b2.button("I'm on the team  →", width="stretch"):
        st.session_state.role = "team"
        st.rerun()
    st.markdown('<div class="hero-note">Demo: choose a side. In the real app, your work login decides this.<br><br>Built by Prachi Gupta · NEAR AI Hackathon NYC 2026</div>',
                unsafe_allow_html=True)

# ---------- PM side ----------
elif st.session_state.role == "pm":
    project = data["project"]
    if project is None:
        st.button("←", key="pm_back_new", on_click=go_back)
        st.subheader("Create a project")
        name = st.text_input("Project name", "Atlas")
        milestone = st.text_input("Next milestone", "Beta launch, Dec 15")
        emails = st.text_area("Team emails (one per line)",
                              "mohan@atlas.co\nrhea@atlas.co\narin@atlas.co\nluka@atlas.co\nissa@atlas.co")
        st.caption("Every team gets the same core check-in questions, so nobody can be singled out.")
        if st.button("Create & invite", type="primary"):
            team = [e.split("@")[0].strip().capitalize() for e in emails.splitlines() if e.strip()]
            data["project"] = {"name": name, "milestone": milestone, "team": team, "week": 1}
            save_data(data)
            st.rerun()
    else:
        masthead(data, project)
        if st.session_state.closed_msg:
            st.success("Week closed.  Raw answers were deleted; only the sealed AI's themes were kept.")
            st.session_state.closed_msg = False
        with st.expander(f" Team invites · {len(project['team'])} people invited"):
            st.code("http://localhost:8501", language=None)
            st.caption("Share this link in your team's Slack or Teams channel.")

        show_pm_dashboard(data, project)

        with st.expander(" Demo tools"):
            c1, c2, c3 = st.columns(3)
            if c1.button("Load demo (Week 3)"):
                project["week"] = 3
                data["confidence_history"] = [7.4, 6.8]
                data["history"] = {"1": DEMO_WEEK1, "2": DEMO_WEEK2}
                data["checkins"] = [dict(c) for c in DEMO_CHECKINS]
                data["checked_in"] = list(DEMO_NAMES)
                data["followups"] = []
                save_data(data)
                st.rerun()
            if c2.button("Add demo replies"):
                demo_codes = [c["code"] for c in DEMO_CHECKINS]
                with st.spinner(" Sealing demo replies…"):
                    for fu in data["followups"]:
                        pool = fu["codes"] if fu["audience"] == "raisers" else demo_codes[:2]
                        pool = [c for c in pool if c in demo_codes and c not in fu["replied"]]
                        texts = DEMO_REPLIES.get(fu["theme"], [DEFAULT_REPLY])
                        for i, code in enumerate(pool):
                            save_reply(data, fu, code, texts[i % len(texts)])
                st.rerun()
            if c3.button("Reset demo"):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.session_state.plan = None
                st.rerun()

# ---------- Team side ----------
else:
    project = data["project"]
    if project is None:
        team_band("Nothing here yet", "Ask your PM to send you an invite to their project.")
    elif st.session_state.user is None:
        team_band("You've been invited", f"Project {html.escape(project['name'])} · Speak freely here. "
                  "Your answers are sealed, and your PM only ever sees patterns.")
        with card():
            st.caption("Demo login. In the real app, this is your work Google or Microsoft account.")
            name = st.selectbox("Sign in as", project["team"], index=None, placeholder="Choose your name")
            if st.button("Sign in", type="primary", disabled=name is None):
                st.session_state.user = name
                st.session_state.code = new_code()
                st.rerun()
    else:
        week = project.get("week", 1)
        team_band(f"Project {html.escape(project['name'])}",
                  f"Week {week} of {TOTAL_WEEKS} check-in · Speak freely. Only patterns are revealed, never names.",
                  chips=[f" Envelope #{st.session_state.code} this week", " Sealed by NEAR AI"])
        show_inbox(data)
        if st.session_state.submitted or st.session_state.user in data["checked_in"]:
            with card("sage"):
                st.subheader("Check-in sealed and delivered")
                st.write("Your answers can't be traced back to you. Your PM only sees patterns across the team.")
        else:
            prev = data["history"].get(str(week - 1))
            this_week_qs = prev["questions"] if prev else []
            with card():
                confidence = st.slider("1. How confident are you that this project hits its next milestone?", 0, 10, 5)
            with card():
                risk = st.pills("2. What's the biggest thing that could go wrong?", RISKS, key="f_risk")
                risk_detail = st.text_area("Tell us more (optional)", key="f_risk_detail")
            with card():
                help_needed = st.pills("3. What would help most right now?", HELPS, key="f_help")
                help_detail = st.text_input("Anything specific? (optional)", key="f_help_detail")
            with card():
                anything_else = st.text_area("4. Anything else your PM should know? (optional)", key="f_other")
            followthrough = {}
            if this_week_qs:
                with card("sage"):
                    st.markdown("**5. Since last week**")
                    st.caption("Questions written by the sealed AI from last week's team themes.")
                    for i, q in enumerate(this_week_qs):
                        followthrough[q] = st.radio(q, ["Yes", "Somewhat", "No"], index=None,
                                                    horizontal=True, key=f"ft_{i}")

            guard = st.session_state.guard
            if guard:
                for field, safer in list(guard.items()):
                    with card("amber"):
                        st.write(f" **Your answer to “{TEXT_FIELDS[field]}” could point to you.** A safer version:")
                        st.write(f"*{safer}*")
                        g1, g2 = st.columns(2)
                        g1.button("Use safer version", key=f"use_{field}", on_click=accept_safer, args=(field, safer))
                        g2.button("Keep mine", key=f"keep_{field}", on_click=dismiss_guard, args=(field,))

            ready = risk is not None and help_needed is not None
            answers = {"code": st.session_state.code, "confidence": confidence,
                       "risk": risk, "risk_detail": risk_detail,
                       "help": help_needed, "help_detail": help_detail, "other": anything_else,
                       "followthrough": followthrough}
            if guard is None:
                if st.button("Review & submit", type="primary", disabled=not ready, width="stretch"):
                    flagged = {}
                    with st.spinner(" The sealed AI is checking your words for anything that could identify you…"):
                        for field in TEXT_FIELDS:
                            text = (st.session_state.get(f"f_{field}") or "").strip()
                            if text:
                                safer = ai_privacy_check(text)
                                if safer:
                                    flagged[field] = safer
                    if flagged:
                        st.session_state.guard = flagged
                        st.rerun()
                    else:
                        submit_checkin(data, answers)
            else:
                if not guard:
                    st.success("Looks safe now.")
                if st.button("Submit", type="primary", disabled=not ready, width="stretch"):
                    submit_checkin(data, answers)

    st.divider()
    st.button("← Back to start", on_click=go_back)

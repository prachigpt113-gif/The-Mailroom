import streamlit as st
import random, string, json, os
import pandas as pd
from collections import Counter

st.set_page_config(page_title="The Mailroom", page_icon="📬", layout="centered")
st.markdown("""
<style>
.block-container {max-width: 720px; padding-top: 2rem;}
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

DATA_FILE = "mailroom_data.json"
WEEK, TOTAL_WEEKS = 3, 6
RISKS = ["Unclear requirements", "Timeline too tight", "Dependency on other team",
         "Technical unknowns", "Resourcing", "Something else"]
HELPS = ["Clear priorities", "More time", "Another pair of hands",
         "A decision from leadership", "Something else"]

# ---------- Storage: a simple file both windows can read ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
    else:
        data = {"project": None, "checkins": [], "checked_in": []}
    data.setdefault("followups", [])
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

# ---------- Demo data for rehearsals ----------
DEMO_CHECKINS = [
    {"code": "M4QX", "confidence": 4, "risk": "Unclear requirements",
     "risk_detail": "The payment flow spec changed twice this sprint and the latest version isn't written down anywhere.",
     "help": "Clear priorities", "help_detail": "", "other": ""},
    {"code": "R7TB", "confidence": 5, "risk": "Dependency on other team",
     "risk_detail": "We're waiting on the platform team's API and they haven't committed to a date.",
     "help": "A decision from leadership", "help_detail": "Someone needs to escalate the API timeline.", "other": ""},
    {"code": "A2LK", "confidence": 6, "risk": "Resourcing", "risk_detail": "",
     "help": "Another pair of hands", "help_detail": "", "other": "QA is basically one person."},
    {"code": "L9PD", "confidence": 5, "risk": "Unclear requirements",
     "risk_detail": "Not sure if guest checkout is in scope for beta or not.",
     "help": "Clear priorities", "help_detail": "", "other": ""},
]
DEMO_NAMES = ["Arin", "Luka", "Mohan", "Rhea"]
DEMO_REPLIES = {
    "Unclear requirements": ["Mostly whether guest checkout is in scope for beta.",
                             "The payment flow. Which version of the spec is final?"],
    "Dependency on other team": ["We need a committed date for the platform API."],
    "Resourcing": ["Even a part-time tester for the last two weeks would help."],
}
DEFAULT_REPLY = "Clearer written decisions after each meeting would help."

# ---------- Sealed AI (practice mode until Wednesday) ----------
PRACTICE_MODE = True
CONFIDENCE_HISTORY = [7.4, 6.8]   # demo: Week 1 and Week 2

def ai_summary(checkins):
    return ("**Practice mode: fake AI.** On Wednesday this comes from NEAR's sealed AI.\n\n"
            "- Several people say the scope keeps shifting and decisions aren't written down.\n"
            "- The team is waiting on another team's work, with no committed date.\n"
            "- Capacity looks thin for the beta timeline.")

def ai_reword(text):
    # Wednesday: the sealed AI rewrites each reply so writing style can't identify anyone
    return text

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

def show_inbox(data):
    code = st.session_state.code
    if st.session_state.sent_reply:
        st.success("Reply sealed and delivered ✉️")
        st.session_state.sent_reply = False
    mail = [fu for fu in data["followups"]
            if (fu["audience"] == "all" or code in fu["codes"]) and code not in fu["replied"]]
    for fu in mail:
        with st.container(border=True):
            if fu["audience"] == "raisers":
                st.write("📨 **Your PM asked about a risk you raised**")
            else:
                st.write("📨 **Your PM asked the whole team**")
            st.write(f"*{fu['question']}*")
            st.caption("Your reply is sealed. Your PM won't know it came from you.")
            reply = st.text_area("Your reply", key=f"r_{fu['id']}")
            if st.button("Send reply", key=f"s_{fu['id']}", type="primary"):
                if reply.strip():
                    save_reply(data, fu, code, reply.strip())
                    st.session_state.sent_reply = True
                    st.rerun()
                else:
                    st.warning("Write a reply first.")
    if not mail:
        st.caption("📭 No new mail. Follow-up questions from your PM will appear here.")
    if st.button("Refresh inbox"):
        st.rerun()

# ---------- PM radar ----------
def show_radar(data, project):
    checkins = data["checkins"]
    n, team_size = len(checkins), len(project["team"])
    if n < 4:
        st.info(f"The radar unlocks at 4 check-ins, so nobody can be singled out. ({n} so far)")
        return

    st.header("📡 Project radar")
    avg = round(sum(c["confidence"] for c in checkins) / n, 1)
    st.metric("Team confidence", f"{avg} / 10", delta=round(avg - CONFIDENCE_HISTORY[-1], 1))
    chart = pd.DataFrame({"Confidence": CONFIDENCE_HISTORY + [avg]},
                         index=[f"Week {i+1}" for i in range(len(CONFIDENCE_HISTORY) + 1)])
    st.line_chart(chart)

    st.subheader("Biggest risks")
    st.caption("Follow up on any risk. Risks raised by one person go to the whole team, so nobody is singled out.")
    for risk, count in Counter(c["risk"] for c in checkins).most_common():
        st.warning(f"**{count} of {n}** flagged: {risk}")
        if count >= 2:
            label, audience = "Ask the people who raised this", "raisers"
        else:
            label, audience = "Ask the whole team", "all"
        if st.button(label, key=f"fu_{risk}"):
            st.session_state.compose = {"theme": risk, "audience": audience}

    comp = st.session_state.compose
    if comp:
        with st.container(border=True):
            who = "the people who raised it" if comp["audience"] == "raisers" else "the whole team"
            st.write(f"**Follow-up on “{comp['theme']}”** · goes to {who}")
            q = st.text_input("Your question", key=f"q_{comp['theme']}")
            c1, c2 = st.columns(2)
            if c1.button("Send", type="primary"):
                if q.strip():
                    codes = ([c["code"] for c in checkins if c["risk"] == comp["theme"]]
                             if comp["audience"] == "raisers" else [])
                    send_followup(data, comp["theme"], q.strip(), comp["audience"], codes)
                    st.session_state.compose = None
                    st.rerun()
                else:
                    st.warning("Write a question first.")
            if c2.button("Cancel"):
                st.session_state.compose = None
                st.rerun()

    st.subheader("What would help most")
    for h, count in Counter(c["help"] for c in checkins).most_common():
        st.write(f"**{count} of {n}**: {h}")

    st.subheader("What the notes say")
    st.markdown(ai_summary(checkins) if PRACTICE_MODE else "Sealed AI not connected yet.")
    st.caption("🔒 Written answers are read only by the sealed AI. You see themes, never quotes.")

    if data["followups"]:
        st.subheader("📬 Follow-ups")
        for fu in data["followups"]:
            expected = len(fu["codes"]) if fu["audience"] == "raisers" else team_size
            who = "the people who raised it" if fu["audience"] == "raisers" else "the whole team"
            with st.container(border=True):
                st.write(f"**{fu['theme']}:** {fu['question']}")
                st.caption(f"Sent to {who} · Responses {len(fu['replies'])} of {expected}")
                for r in fu["replies"]:
                    st.write(f"• {r}")
                waiting = expected - len(fu["replies"])
                if waiting > 0:
                    st.caption(f"{waiting} response(s) awaited")
        if PRACTICE_MODE:
            st.caption("Practice mode: replies show as written. With the sealed AI, each reply is reworded so writing style can't identify anyone.")

# ---------- Session setup ----------
for key, default in {"role": None, "user": None, "code": None, "submitted": False,
                     "compose": None, "sent_reply": False}.items():
    if key not in st.session_state:
        st.session_state[key] = default

data = load_data()
st.title("📬 The Mailroom")

# ---------- Landing: two doors ----------
if st.session_state.role is None:
    st.write("Honest project check-ins. Sealed answers. Patterns, never names.")
    st.caption("Demo: choose a side. In the real app, your login decides this.")
    col1, col2 = st.columns(2)
    if col1.button("I'm a PM", type="primary"):
        st.session_state.role = "pm"
        st.rerun()
    if col2.button("I'm on the team"):
        st.session_state.role = "team"
        st.rerun()

# ---------- PM side ----------
elif st.session_state.role == "pm":
    project = data["project"]
    if project is None:
        st.subheader("Create a project")
        name = st.text_input("Project name", "Atlas")
        milestone = st.text_input("Next milestone", "Beta launch, Dec 15")
        emails = st.text_area("Team emails (one per line)",
                              "mohan@atlas.co\nrhea@atlas.co\narin@atlas.co\nluka@atlas.co\nissa@atlas.co")
        st.caption("Every team gets the same check-in questions, so nobody can be singled out.")
        if st.button("Create & invite", type="primary"):
            team = [e.split("@")[0].strip().capitalize() for e in emails.splitlines() if e.strip()]
            data["project"] = {"name": name, "milestone": milestone, "team": team}
            save_data(data)
            st.rerun()
    else:
        st.subheader(f"Project: {project['name']} · Week {WEEK} of {TOTAL_WEEKS}")
        st.caption(f"Next milestone: {project['milestone']}")
        st.success(f"Invites sent to {len(project['team'])} people.")
        st.code("http://localhost:8501", language=None)
        st.metric("Checked in this week", f"{len(data['checked_in'])} of {len(project['team'])}")
        show_radar(data, project)

        st.divider()
        st.caption("Demo tools")
        c1, c2, c3 = st.columns(3)
        if c1.button("Load 4 demo check-ins"):
            data["checkins"] = list(DEMO_CHECKINS)
            data["checked_in"] = list(DEMO_NAMES)
            save_data(data)
            st.rerun()
        if c2.button("Add demo replies"):
            demo_codes = [c["code"] for c in DEMO_CHECKINS]
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
            st.session_state.compose = None
            st.rerun()

# ---------- Team side ----------
else:
    project = data["project"]
    if project is None:
        st.info("No project yet. Ask your PM to send you an invite.")
    elif st.session_state.user is None:
        st.subheader("You've been invited to the Mailroom")
        st.write(f"**Project: {project['name']}**")
        st.caption("Demo login. In the real app, this is your work Google or Microsoft account.")
        name = st.selectbox("Sign in as", project["team"], index=None, placeholder="Choose your name")
        if st.button("Sign in", type="primary", disabled=name is None):
            st.session_state.user = name
            st.session_state.code = new_code()
            st.rerun()
    else:
        st.caption(f"✉️ You're Envelope #{st.session_state.code} this week")
        show_inbox(data)
        if st.session_state.submitted or st.session_state.user in data["checked_in"]:
            st.success("Check-in sealed and delivered ✉️")
            st.write("Your answers can't be traced back to you. Your PM only sees patterns across the team.")
        else:
            st.subheader(f"Project: {project['name']} · Week {WEEK} of {TOTAL_WEEKS}")
            st.info("Speak freely in the Mailroom. Your answers are sealed. Only patterns are revealed, never names.")
            confidence = st.slider("1. How confident are you that this project hits its next milestone?", 0, 10, 5)
            risk = st.pills("2. What's the biggest thing that could go wrong?", RISKS)
            risk_detail = st.text_area("Tell us more (optional)")
            help_needed = st.pills("3. What would help most right now?", HELPS)
            help_detail = st.text_input("Anything specific? (optional)")
            anything_else = st.text_area("4. Anything else your PM should know? (optional)")
            if st.button("Submit", type="primary", disabled=risk is None or help_needed is None):
                save_checkin(data, st.session_state.user, {
                    "code": st.session_state.code, "confidence": confidence,
                    "risk": risk, "risk_detail": risk_detail,
                    "help": help_needed, "help_detail": help_detail, "other": anything_else})
                st.session_state.submitted = True
                st.rerun()

# ---------- Back to start (for demo switching) ----------
if st.session_state.role:
    st.divider()
    if st.button("← Back to start"):
        for k in ["role", "user", "code", "compose"]:
            st.session_state[k] = None
        st.session_state.submitted = False
        st.rerun()
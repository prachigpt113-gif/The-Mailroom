# The Mailroom

**Say what you can't say in standup.**

Honest weekly project check-ins, sealed by private AI on NEAR. The PM sees patterns, never names.

Built solo by **Prachi Gupta** at **NEAR Hackathon NYC** (November 2026) · Track: Privacy & Private AI
🎥 Demo video: https://x.com/writeawav/status/2121352994826363348

---

## The problem

Every team has had a *watermelon project*: green in status meetings, red inside. Someone knows a
dependency will slip. Someone doesn't understand the requirements. They say "on track" anyway,
because admitting it out loud has a career cost. By the time the PM finds out, it's too late.

## What it does

**For team members:** a 60-second weekly check-in: confidence (0–10), the biggest risk, what
would help, and optional notes. Each week also includes AI-written "since last week" questions.
Each person gets an anonymous envelope code; their name never touches their answers.

**For the PM:** a dashboard of patterns, never individuals:
- Team confidence over time
- **Keep an eye on:** issues tagged Persistent, New or Improving across weeks
- Last week's recap and whether the fixes worked
- **Sealed follow-ups:** ask about any risk; the question reaches only the people who raised it,
  and their replies come back reworded with no name attached
- **Wrap up the week:** an AI-drafted action checklist and next week's questions

## Where the sealed AI works

Buttons are counted by plain code. **Words are read only by sealed AI**, running on NEAR AI
Cloud in a Confidential TEE (GLM 5.3 Flash), where the model provider can't see prompts or outputs.

| AI job | What it does |
|---|---|
| Privacy guard | Checks a teammate's notes before submitting and suggests a safer version if anything could identify them |
| Themes | Summarizes written notes into themes, never quotes, with names, roles and teams removed |
| Keep an eye on | Compares this week with earlier weeks' themes to flag persistent issues |
| Rewording | Rewrites follow-up replies so writing style can't identify anyone |
| Suggested question | Drafts a follow-up question for the PM |
| Action checklist | Turns the history into three next steps |
| Next week's questions | Writes Yes / Somewhat / No questions to check whether fixes worked |

## Privacy design

- **Voting-booth model:** "who checked in" and "what was said" are stored in separate lists and shuffled, so order can't link them.
- **Anonymous envelope codes:** follow-ups are routed to codes, not people.
- **Minimum group size:** the dashboard unlocks only after 4 check-ins.
- **No single-person follow-ups:** a risk raised by one person can only be asked to the whole team.
- **Fixed core questions:** PMs can't add questions that single someone out.
- **Fail closed:** if a reply can't be reworded, it's held back rather than shown raw.
- **Raw answers deleted at week close:** only the AI's themes are kept between weeks.

## What is and isn't sealed (honest limits)

- ✅ All AI processing runs inside NEAR's Confidential TEE.
- The app itself (Streamlit) runs on a normal server, not in a TEE. It stores the current
  week's answers in a local file until the PM closes the week.
- Login is simulated for the demo (pick your name). A real version would use company sign-in (SSO).
- Next step: move the routing and storage inside a TEE so even the app operator can't link answers to people.

## Run it locally

1. Install: `pip install -r requirements.txt`
2. Get a NEAR AI Cloud API key, then create `.streamlit/secrets.toml` containing:
   `NEARAI_API_KEY = "your-key-here"` (never commit this file)
3. Run: `streamlit run mail_app.py`
4. Demo: choose **I'm a PM** → **Create & invite** → open **Demo tools** → **Load demo (Week 3)**.
   Open a second tab, choose **I'm on the team**, and sign in as Issa.

## Built with

Python · Streamlit · NEAR AI Cloud (Confidential TEE, GLM 5.3 Flash) · OpenAI-compatible Python client

## Roadmap

Company sign-in (SSO) · Slack and Microsoft Teams apps · app logic and storage inside a TEE ·
in-app TEE verification

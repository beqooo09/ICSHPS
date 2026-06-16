# ICSHPS - Intelligent Candidate Screening & Hiring Pipeline System

A multi-agent AI pipeline that automates the entire hiring workflow — from resume intake to final candidate ranking.

## What it does

ICSHPS takes a candidate's resume and hiring bundle as input, runs it through 6 specialized AI agents, and produces a ranked shortlist with full audit trail.

## Architecture
Agent A (Dion)   → Application intake & context building

Agent B (Dion)   → Resume extraction from PDF

Agent C (Erina)  → Job description matching & fit scoring

Agent D (Erina)  → EEO compliance checks

Agent E (Erina)  → Credential verification

Agent H (Beqir)  → Lead orchestrator & decision logic

Agent G (Beqir)  → Final ranking & recommendation

## Output files per candidate

| File | Description |
|------|-------------|
| `candidate_profile.json` | Extracted resume data |
| `match_scores.json` | JD fit scores |
| `compliance_flags.json` | EEO compliance status |
| `credential_report.json` | Verified credentials |
| `hiring_decision.json` | Final decision + reason |
| `audit_log.md` | Full decision trace |

## Pipeline outputs

| File | Description |
|------|-------------|
| `shortlist.csv` | Ranked candidate list |
| `metrics.json` | Pipeline statistics |

## How to run

**1. Clone the repo**
```bash
git clone https://github.com/beqooo09/ICSHPS.git
cd ICSHPS
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the full pipeline**
```bash
python run_pipeline.py
```

**4. View the dashboard**
```bash
python -m streamlit run dashboard/app.py
```

## Project structure
ICSHPS/

├── agents/          # All agent files

├── schemas/         # JSON schemas for inter-agent communication

├── hiring_bundles/  # Input candidate data

├── runs/            # Pipeline outputs per candidate

├── dashboard/       # Streamlit dashboard

├── tests/           # Test scripts

├── run_pipeline.py  # One-command pipeline runner

└── requirements.txt

## Team

| Name | Role |
|------|------|
| Beqir Bytyqi | Agent H, Agent G, Dashboard, Integration |
| Erina Mjeku | Agent C, Agent D, Agent E |
| Dion Latifi | Agent A, Agent B |

## Tech stack

Python, Streamlit, JSON, CSV, Pandas

## Capstone Project — Genpact Academy 2026
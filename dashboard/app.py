import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import subprocess

# Page config
st.set_page_config(
    page_title="ICSHPS Dashboard",
    page_icon="🧠",
    layout="wide"
)

RUNS_FOLDER = "runs"

def load_shortlist():
    filepath = os.path.join(RUNS_FOLDER, "shortlist.csv")
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return None

def load_metrics():
    filepath = os.path.join(RUNS_FOLDER, "metrics.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_candidate_decision(candidate_id):
    filepath = os.path.join(RUNS_FOLDER, candidate_id, "hiring_decision.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_audit_log(candidate_id):
    filepath = os.path.join(RUNS_FOLDER, candidate_id, "audit_log.md")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return None

def get_candidates():
    candidates = []
    if os.path.exists(RUNS_FOLDER):
        for folder in os.listdir(RUNS_FOLDER):
            decision_path = os.path.join(RUNS_FOLDER, folder, "hiring_decision.json")
            if os.path.exists(decision_path):
                candidates.append(folder)
    return candidates

# Header
st.title("ICSHPS")
st.markdown("#### Intelligent Candidate Screening & Hiring Pipeline System")
st.markdown("*Multi-agent AI system for automated candidate screening — Genpact Academy 2026*")
st.divider()

# Run pipeline button
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
with col_btn1:
    if st.button("Run Pipeline", type="primary"):
        with st.spinner("Running pipeline..."):
            result = subprocess.run(
                ["python", "run_pipeline.py"],
                capture_output=True,
                text=True
            )
            st.success("Pipeline completed successfully")
            st.code(result.stdout)

with col_btn2:
    if st.button("Refresh Dashboard"):
        st.rerun()

st.divider()

# Metrics
metrics = load_metrics()
if metrics:
    st.subheader("Pipeline Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Candidates", metrics["total_candidates"])
    with col2:
        st.metric("Advanced", metrics["advanced"], delta=None)
    with col3:
        st.metric("Rejected", metrics["rejected"])
    with col4:
        st.metric("Manual Review", metrics["manual_review"])
    with col5:
        advance_rate = int(metrics.get("advance_rate", 0) * 100)
        st.metric("Advance Rate", f"{advance_rate}%")

    st.divider()

    # Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("**Decision Breakdown**")
        chart_data = {
            "Decision": ["Advanced", "Manual Review", "Rejected"],
            "Count": [
                metrics["advanced"],
                metrics["manual_review"],
                metrics["rejected"]
            ]
        }
        df_chart = pd.DataFrame(chart_data)
        fig = px.pie(
            df_chart,
            values="Count",
            names="Decision",
            color="Decision",
            color_discrete_map={
                "Advanced": "#1a472a",
                "Manual Review": "#7c4a00",
                "Rejected": "#7f1d1d"
            }
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        st.markdown("**Candidate Scores**")
        shortlist = load_shortlist()
        if shortlist is not None and "Overall Score" in shortlist.columns:
            shortlist_filtered = shortlist.dropna(subset=["Overall Score"])
            if not shortlist_filtered.empty:
                fig2 = px.bar(
                    shortlist_filtered,
                    x="Candidate ID",
                    y="Overall Score",
                    color="Decision",
                    color_discrete_map={
                        "advance": "#1a472a",
                        "manual_review": "#7c4a00",
                        "reject": "#7f1d1d"
                    }
                )
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    yaxis_range=[0, 1]
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No scores available yet")
        else:
            st.info("No scores available yet")

st.divider()

# Shortlist
st.subheader("Candidate Shortlist")
shortlist = load_shortlist()

if shortlist is not None:
    st.dataframe(shortlist, use_container_width=True)
else:
    st.warning("No shortlist found. Run the pipeline first.")

st.divider()

# Candidate detail
st.subheader("Candidate Detail")
candidates = get_candidates()

if candidates:
    selected = st.selectbox("Select a candidate", sorted(candidates))

    if selected:
        decision = load_candidate_decision(selected)
        audit = load_audit_log(selected)

        if decision:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### Decision")
                decision_val = decision.get("decision", "unknown")

                if decision_val == "advance":
                    st.success("ADVANCE")
                elif decision_val == "reject":
                    st.error("REJECTED")
                else:
                    st.warning("MANUAL REVIEW")

                st.markdown(f"**Reason:** {decision.get('reason')}")
                st.markdown(f"**Score:** {decision.get('overall_score')}")
                st.markdown(f"**Decided at:** {decision.get('decided_at')}")
                st.markdown(f"**Decided by:** {decision.get('decided_by')}")

            with col2:
                st.markdown("### Compliance & Credentials")
                compliance = decision.get("compliance_passed")
                credentials = decision.get("credentials_passed")

                if compliance is True:
                    st.success("Compliance: Passed")
                elif compliance is False:
                    st.error("Compliance: Failed")
                else:
                    st.warning("Compliance: Not checked")

                if credentials is True:
                    st.success("Credentials: Passed")
                elif credentials is False:
                    st.error("Credentials: Failed")
                else:
                    st.warning("Credentials: Not checked")

            with col3:
                st.markdown("### Agent Status")
                profile = os.path.exists(os.path.join(RUNS_FOLDER, selected, "candidate_profile.json"))
                match = os.path.exists(os.path.join(RUNS_FOLDER, selected, "match_scores.json"))
                comp = os.path.exists(os.path.join(RUNS_FOLDER, selected, "compliance_flags.json"))
                cred = os.path.exists(os.path.join(RUNS_FOLDER, selected, "credential_report.json"))
                hdec = os.path.exists(os.path.join(RUNS_FOLDER, selected, "hiring_decision.json"))

                st.markdown(f"Agent B (Profile): {'Done' if profile else 'Pending'}")
                st.markdown(f"Agent C (Match): {'Done' if match else 'Pending'}")
                st.markdown(f"Agent D (Compliance): {'Done' if comp else 'Pending'}")
                st.markdown(f"Agent E (Credentials): {'Done' if cred else 'Pending'}")
                st.markdown(f"Agent H (Decision): {'Done' if hdec else 'Pending'}")

            if decision.get("warnings"):
                st.divider()
                st.markdown("**Warnings:**")
                for w in decision["warnings"]:
                    st.warning(w)

        if audit:
            st.divider()
            with st.expander("View Full Audit Log"):
                st.markdown(audit)
else:
    st.info("No candidates processed yet. Run the pipeline first.")
import streamlit as st
import json
import os
import pandas as pd

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

# Header
st.title("ICSHPS - Intelligent Candidate Screening & Hiring Pipeline")
st.markdown("**Multi-agent AI system for automated candidate screening**")
st.divider()

# Metrics section
metrics = load_metrics()
if metrics:
    st.subheader("Pipeline Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Candidates", metrics["total_candidates"])
    with col2:
        st.metric("Advanced", metrics["advanced"])
    with col3:
        st.metric("Rejected", metrics["rejected"])
    with col4:
        st.metric("Manual Review", metrics["manual_review"])

    st.divider()

# Shortlist section
st.subheader("Candidate Shortlist")
shortlist = load_shortlist()

if shortlist is not None:
    st.dataframe(shortlist, use_container_width=True)
else:
    st.warning("No shortlist found. Run the pipeline first.")

st.divider()

# Individual candidate detail
st.subheader("Candidate Detail")

candidates = []
if os.path.exists(RUNS_FOLDER):
    for folder in os.listdir(RUNS_FOLDER):
        decision_path = os.path.join(RUNS_FOLDER, folder, "hiring_decision.json")
        if os.path.exists(decision_path):
            candidates.append(folder)

if candidates:
    selected = st.selectbox("Select a candidate", candidates)

    if selected:
        decision = load_candidate_decision(selected)
        audit = load_audit_log(selected)

        if decision:
            col1, col2 = st.columns(2)

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
                st.markdown(f"**Compliance Passed:** {decision.get('compliance_passed')}")
                st.markdown(f"**Credentials Passed:** {decision.get('credentials_passed')}")

                if decision.get("warnings"):
                    st.markdown("**Warnings:**")
                    for w in decision["warnings"]:
                        st.warning(w)
                else:
                    st.success("No warnings")

        if audit:
            st.divider()
            st.markdown("### Audit Log")
            st.markdown(audit)
else:
    st.info("No candidates processed yet.")
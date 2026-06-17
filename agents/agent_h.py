import json
import os
from datetime import datetime


class AgentH:

    def __init__(self, candidate_id, runs_folder="runs"):
        self.candidate_id = candidate_id
        self.runs_folder = runs_folder
        self.candidate_folder = os.path.join(runs_folder, candidate_id)
        self.data = {}
        self.warnings = []

    def load_file(self, filename):
        filepath = os.path.join(self.candidate_folder, filename)

        if not os.path.exists(filepath):
            warning = f"WARNING: {filename} not found for {self.candidate_id}"
            self.warnings.append(warning)
            print(warning)
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all_outputs(self):
        print(f"\nAgent H loading data for candidate: {self.candidate_id}")

        self.data["agent_a"] = self.load_file("agent_a.json")
        self.data["profile"] = self.load_file("candidate_profile.json")
        self.data["match_scores"] = self.load_file("match_scores.json")
        self.data["compliance_flags"] = self.load_file("compliance_flags.json")
        self.data["credential_report"] = self.load_file("credential_report.json")

        print(f"Loaded {sum(1 for v in self.data.values() if v is not None)} out of 5 files")
        return self.data

    def make_decision(self):
        print(f"\nAgent H making decision for: {self.candidate_id}")

        agent_a = self.data.get("agent_a")
        profile = self.data.get("profile")
        match_scores = self.data.get("match_scores")
        compliance = self.data.get("compliance_flags")
        credentials = self.data.get("credential_report")

        # Rule 0: If Agent A already rejected at intake, respect that
        if agent_a and agent_a.get("risk_assessment", {}).get("status") == "rejected":
            risk_flags = agent_a.get("risk_assessment", {}).get("risk_flags", [])
            reasons = ", ".join(f.get("message", f.get("code", "")) for f in risk_flags)
            return {
                "decision": "reject",
                "reason": f"Rejected at intake by Agent A: {reasons}"
            }

        # Rule 1: If no profile, cannot process
        if profile is None:
            return {
                "decision": "manual_review",
                "reason": "No candidate profile available"
            }

        # Rule 2: If extraction confidence is too low
        if profile.get("extraction_confidence", 0) < 0.7:
            return {
                "decision": "manual_review",
                "reason": "Low extraction confidence - needs human review"
            }

        # Rule 3: If compliance failed
        if compliance and not compliance.get("eeo_compliant", True):
            return {
                "decision": "manual_review",
                "reason": "EEO compliance issue detected"
            }

        # Rule 4: If must-have criteria not met
        if match_scores and not match_scores.get("must_have_criteria_met", True):
            return {
                "decision": "reject",
                "reason": "Candidate does not meet must-have job requirements"
            }

        # Rule 5: If overall score is strong
        if match_scores and match_scores.get("overall_score", 0) >= 0.75:
            return {
                "decision": "advance",
                "reason": "Strong match - advance to interview"
            }

        # Rule 6: Default
        return {
            "decision": "manual_review",
            "reason": "Insufficient data or weak match score"
        }

    def write_decision(self, decision_result):
        os.makedirs(self.candidate_folder, exist_ok=True)

        output = {
            "candidate_id": self.candidate_id,
            "decision": decision_result["decision"],
            "reason": decision_result["reason"],
            "overall_score": self.data.get("match_scores", {}).get("overall_score") if self.data.get("match_scores") else None,
            "compliance_passed": self.data.get("compliance_flags", {}).get("eeo_compliant") if self.data.get("compliance_flags") else None,
            "credentials_passed": self.data.get("credential_report", {}).get("verification_status") == "passed" if self.data.get("credential_report") else None,
            "warnings": self.warnings,
            "decided_at": datetime.now().isoformat(),
            "decided_by": "Agent_H"
        }

        filepath = os.path.join(self.candidate_folder, "hiring_decision.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"Decision saved to {filepath}")
        return output

    def write_audit_log(self, decision_result):
        lines = []
        lines.append(f"# Audit Log - {self.candidate_id}")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Decided by:** Agent_H")
        lines.append("")
        lines.append("## Decision")
        lines.append(f"**Result:** {decision_result['decision'].upper()}")
        lines.append(f"**Reason:** {decision_result['reason']}")
        lines.append("")
        lines.append("## Files Loaded")
        for key, value in self.data.items():
            status = "Loaded" if value is not None else "Missing"
            lines.append(f"- {key}: {status}")
        lines.append("")
        lines.append("## Warnings")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"- {w}")
        else:
            lines.append("- No warnings")
        lines.append("")
        lines.append("## Scores")
        if self.data.get("match_scores"):
            lines.append(f"- Overall Score: {self.data['match_scores'].get('overall_score')}")
            lines.append(f"- Must Have Criteria Met: {self.data['match_scores'].get('must_have_criteria_met')}")
        else:
            lines.append("- Match scores not available")

        filepath = os.path.join(self.candidate_folder, "audit_log.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"Audit log saved to {filepath}")
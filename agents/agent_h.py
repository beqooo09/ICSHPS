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

        with open(filepath, "r") as f:
            return json.load(f)

    def load_all_outputs(self):
        print(f"\nAgent H loading data for candidate: {self.candidate_id}")

        self.data["profile"] = self.load_file("candidate_profile.json")
        self.data["match_scores"] = self.load_file("match_scores.json")
        self.data["compliance_flags"] = self.load_file("compliance_flags.json")
        self.data["credential_report"] = self.load_file("credential_report.json")

        print(f"Loaded {sum(1 for v in self.data.values() if v is not None)} out of 4 files")
        return self.data

    def make_decision(self):
        print(f"\nAgent H making decision for: {self.candidate_id}")

        profile = self.data.get("profile")
        match_scores = self.data.get("match_scores")
        compliance = self.data.get("compliance_flags")
        credentials = self.data.get("credential_report")

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
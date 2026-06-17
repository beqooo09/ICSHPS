import json
import os
import re
from datetime import datetime


class AgentD:
    """
    Agent D - EEO compliance check

    """

    def __init__(self, candidate_id, runs_folder="runs"):
        self.candidate_id = candidate_id

        self.base_dir = os.path.dirname(os.path.dirname(__file__))

        self.runs_folder = os.path.join(self.base_dir, runs_folder)

        self.candidate_folder = os.path.join(
            self.runs_folder,
            candidate_id
        )

        self.policy_path = os.path.join(
            self.base_dir,
            "policies",
            "eeo_policy.json"
        )

        self.profile = None
        self.match_scores = None

        self.agent_a = None
        self.job_description = None
        
        self.policy = self.load_policy()

        self.biased_terms = self.policy.get("biased_terms", [])
        self.protected_terms = self.policy.get("protected_terms", [])

    def load_policy(self):
        if not os.path.exists(self.policy_path):
            raise FileNotFoundError(
                f"Policy file not found: {self.policy_path}"
            )

        with open(self.policy_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_file(self, filename):
        path = os.path.join(
            self.candidate_folder,
            filename
        )

        if not os.path.exists(path):
            print(f"WARNING: {filename} not found for {self.candidate_id}")
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_job_description(self):

        self.agent_a = self.load_file("agent_a.json")

        if self.agent_a is None:
            self.job_description = {
                "job_id": "UNKNOWN-JOB",
                "title": "Unknown Role",
                "description": ""
            }
            return self.job_description

        context_packet = self.agent_a.get("context_packet", {})

        self.job_description = {
            "job_id": context_packet.get("job_id", "UNKNOWN-JOB"),
            "title": context_packet.get("role_title", "Unknown Role"),
            "description": context_packet.get("job_description", "")
        }

        return self.job_description    

    def load_inputs(self):
        self.profile = self.load_file("candidate_profile.json")
        self.match_scores = self.load_file("match_scores.json")
        self.load_job_description()

    def check_problematic_jd_language(self):
        jd_text = self.job_description.get(
            "description",
            ""
        ).lower()
        found_terms = []

        for term in self.biased_terms:
            if term.lower() in jd_text:
                found_terms.append(term)

        return found_terms

    def check_protected_characteristics(self):
        if self.profile is None:
            return []

        profile_text = json.dumps(
            self.profile,
            default=str
        ).lower()

        detected = []

        for term in self.protected_terms:
            if re.search(rf"\b{re.escape(term.lower())}\b", profile_text):
                detected.append(term)

        return detected

    def check_adverse_impact_risk(self):
        if self.match_scores is None:
            return "medium"

        overall_score = self.match_scores.get("overall_score", 0)

        must_have_met = self.match_scores.get(
            "must_have_criteria_met",
            True
        )

        if not must_have_met:
            return "low"

        if overall_score < 0.4:
            return "medium"

        return "low"

    def check_data_integrity(self):
        if self.profile is None:
            return False

        required_fields = [
            "candidate_id",
            "skills",
            "education",
            "experience_years"
        ]

        for field in required_fields:
            if field not in self.profile:
                return False

        return True

    def generate_compliance_report(self):
        print(f"\nd - checking EEO compliance for {self.candidate_id}")

        self.load_inputs()

        problematic_jd_language = self.check_problematic_jd_language()
        protected_characteristics = self.check_protected_characteristics()
        adverse_impact_risk = self.check_adverse_impact_risk()
        data_integrity_valid = self.check_data_integrity()

        flags = []

        if problematic_jd_language:
            flags.append({
                "type": "biased_jd_language",
                "severity": "medium",
                "details": problematic_jd_language
            })

        if protected_characteristics:
            flags.append({
                "type": "protected_characteristics_detected",
                "severity": "high",
                "details": protected_characteristics
            })

        if not data_integrity_valid:
            flags.append({
                "type": "data_integrity_issue",
                "severity": "medium",
                "details": "Candidate profile is missing required fields"
            })

        eeo_compliant = len(flags) == 0

        result = {
            "candidate_id": self.candidate_id,
            # "job_id": self.job_description["job_id"],
            "job_id": self.job_description.get(
                "job_id",
                "UNKNOWN-JOB"
                ),
            "job_title": self.job_description.get(
                "title",
                "Unknown Role"
            ),
            "eeo_compliant": eeo_compliant,
            "flags": flags,
            "protected_characteristics_detected": len(protected_characteristics) > 0,
            "problematic_jd_language": problematic_jd_language,
            "adverse_impact_risk": adverse_impact_risk,
            "data_integrity_valid": data_integrity_valid,
            "checked_at": datetime.now().isoformat(),
            "checked_by": "Agent_D",
            "notes": (
                "No compliance issues detected"
                if eeo_compliant
                else "Compliance issue detected, send to manual review"
            )
        }

        return result

    def save_results(self):
        result = self.generate_compliance_report()

        os.makedirs(
            self.candidate_folder,
            exist_ok=True
        )

        output_path = os.path.join(
            self.candidate_folder,
            "compliance_flags.json"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)

        relative_path = os.path.relpath(
            output_path,
            self.base_dir
        )

        print(f"d - check {relative_path}")
        return result

if __name__ == "__main__":

    runs_folder = "../runs"

    candidates = [
        folder for folder in os.listdir(runs_folder)
        if folder.startswith("C")
        and os.path.isdir(
            os.path.join(runs_folder, folder)
        )
    ]

    for candidate_id in candidates:
        agent = AgentD(
            candidate_id,
            runs_folder=runs_folder
        )

        agent.save_results()
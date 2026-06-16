import json
import os
from datetime import datetime


class AgentE:
    """
    agent E - credential verification
    """

    def __init__(self, candidate_id, runs_folder="runs"):
        self.candidate_id = candidate_id
        self.base_dir = os.path.dirname(os.path.dirname(__file__))

        self.runs_folder = os.path.join(self.base_dir, runs_folder)
        self.candidate_folder = os.path.join(self.runs_folder, candidate_id)

        self.policy_path = os.path.join(
            self.base_dir,
            "policies",
            "credential_policy.json"
        )

        self.profile = None
        self.evidence_index = None
        self.policy = self.load_policy()

    def load_json(self, path, label):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{label} missing for {self.candidate_id}: {path}"
            )

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_policy(self):
        return self.load_json(
            self.policy_path,
            "credential_policy.json"
        )

    def load_inputs(self):
        self.profile = self.load_json(
            os.path.join(self.candidate_folder, "candidate_profile.json"),
            "candidate_profile.json"
        )

        self.evidence_index = self.load_json(
            os.path.join(self.candidate_folder, "evidence_index.json"),
            "evidence_index.json"
        )

    def normalize_claims(self, value):
        if value is None:
            return []

        if isinstance(value, str):
            return [value]

        if isinstance(value, dict):
            return [value]

        if isinstance(value, list):
            return value

        return [str(value)]

    def claim_to_text(self, claim):
        if isinstance(claim, str):
            return claim

        if isinstance(claim, dict):
            important_fields = [
                "degree",
                "institution",
                "name",
                "job_title",
                "company",
                "title"
            ]

            parts = []

            for field in important_fields:
                if claim.get(field):
                    parts.append(str(claim.get(field)))

            if parts:
                return " ".join(parts)

            return json.dumps(claim, default=str)

        return str(claim)

    def get_evidence_items(self, category):
        items = self.evidence_index.get(category, [])

        if isinstance(items, dict):
            return [items]

        if isinstance(items, list):
            return items

        return []

    def find_matching_evidence(self, claim, category):
        claim_text = self.claim_to_text(claim).lower()
        evidence_items = self.get_evidence_items(category)

        minimum_confidence = self.policy.get(
            "minimum_evidence_confidence",
            0.7
        )

        for evidence in evidence_items:
            evidence_text = json.dumps(
                evidence,
                default=str
            ).lower()

            verified = evidence.get("verified", True)
            confidence = evidence.get("confidence", 1)

            if (
                claim_text in evidence_text
                and verified is True
                and confidence >= minimum_confidence
            ):
                return evidence

        return None

    def verify_claim_category(self, category):
        claims = self.normalize_claims(
            self.profile.get(category)
        )

        verified = []
        missing = []

        for claim in claims:
            claim_text = self.claim_to_text(claim)
            evidence = self.find_matching_evidence(claim, category)

            if evidence:
                verified.append({
                    "type": category,
                    "claim": claim_text,
                    "evidence_found": True,
                    "source": evidence.get("source", "unknown"),
                    "confidence": evidence.get("confidence", 1)
                })
            else:
                missing.append({
                    "type": category,
                    "claim": claim_text,
                    "evidence_found": False,
                    "reason": "No matching evidence found"
                })

        return verified, missing

    def verify_certifications(self):
        certifications = self.normalize_claims(
            self.profile.get("certifications")
        )

        results = []

        for cert in certifications:
            cert_name = self.claim_to_text(cert)
            evidence = self.find_matching_evidence(
                cert,
                "certifications"
            )

            results.append({
                "name": cert_name,
                "verified": evidence is not None,
                "source": (
                    evidence.get("source", "unknown")
                    if evidence
                    else "No matching evidence found"
                )
            })

        return results

    def calculate_confidence_score(self, verified_count, missing_count):
        if verified_count + missing_count == 0:
            return self.policy.get("manual_review_confidence", 0.55)

        ratio = verified_count / (verified_count + missing_count)

        passed_confidence = self.policy.get("passed_confidence", 0.9)
        manual_confidence = self.policy.get("manual_review_confidence", 0.55)

        if ratio == 1:
            return passed_confidence

        return round(manual_confidence + ((passed_confidence - manual_confidence) * ratio), 2)

    def generate_report(self):
        print(f"\ne - verifying credentials for {self.candidate_id}")

        self.load_inputs()

        verified_credentials = []
        missing_proof = []
        discrepancies_found = []
        red_flags = []

        categories = self.policy.get(
            "claim_categories",
            ["education", "experience", "skills"]
        )

        for category in categories:
            verified, missing = self.verify_claim_category(category)

            verified_credentials.extend(verified)
            missing_proof.extend(missing)

            for item in missing:
                discrepancies_found.append({
                    "type": f"{category}_missing_evidence",
                    "details": item
                })

        certifications_verified = self.verify_certifications()

        for cert in certifications_verified:
            if not cert["verified"]:
                missing_proof.append({
                    "type": "certifications",
                    "claim": cert["name"],
                    "evidence_found": False,
                    "reason": "No matching evidence found"
                })

                discrepancies_found.append({
                    "type": "certification_missing_evidence",
                    "details": cert
                })

        education_verified = not any(
            item["type"] == "education"
            for item in missing_proof
        )

        employment_history_verified = not any(
            item["type"] == "experience"
            for item in missing_proof
        )

        if missing_proof:
            red_flags.append({
                "type": "missing_credential_evidence",
                "severity": "medium",
                "details": missing_proof
            })

        verification_passed = len(red_flags) == 0

        verified_count = len(verified_credentials) + sum(
            1 for cert in certifications_verified if cert["verified"]
        )

        missing_count = len(missing_proof)

        confidence_score = self.calculate_confidence_score(
            verified_count,
            missing_count
        )

        result = {
            "candidate_id": self.candidate_id,
            "education_verified": education_verified,
            "certifications_verified": certifications_verified,
            "employment_history_verified": employment_history_verified,
            "verified_credentials": verified_credentials,
            "missing_proof": missing_proof,
            "discrepancies_found": discrepancies_found,
            "red_flags": red_flags,
            "verification_status": (
                "passed" if verification_passed else "manual_review"
            ),
            "confidence_score": confidence_score,
            "checked_at": datetime.now().isoformat(),
            "checked_by": "Agent_E",
            "notes": (
                "All credentials verified successfully"
                if verification_passed
                else "Credential issues found, send to manual review"
            )
        }

        return result

    def save_results(self):
        result = self.generate_report()

        os.makedirs(self.candidate_folder, exist_ok=True)

        output_path = os.path.join(
            self.candidate_folder,
            "credential_report.json"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)

        relative_path = os.path.relpath(output_path, self.base_dir)

        print(f"e - check {relative_path}")

        return result


if __name__ == "__main__":
    #run test, added evidence_index.json manually only at candidate_001
    candidates = [
        "candidate_001"
    ]

    for candidate_id in candidates:
        agent = AgentE(candidate_id)
        agent.save_results()
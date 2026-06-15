import json
import os
import csv
from datetime import datetime


class AgentG:

    def __init__(self, runs_folder="runs"):
        self.runs_folder = runs_folder
        self.decisions = []

    def load_all_decisions(self):
        print("\nAgent G loading all candidate decisions...")

        if not os.path.exists(self.runs_folder):
            print("No runs folder found")
            return []

        for candidate_folder in os.listdir(self.runs_folder):
            decision_path = os.path.join(
                self.runs_folder,
                candidate_folder,
                "hiring_decision.json"
            )

            if os.path.exists(decision_path):
                with open(decision_path, "r", encoding="utf-8") as f:
                    decision = json.load(f)
                    self.decisions.append(decision)
                    print(f"Loaded decision for: {decision['candidate_id']}")
            else:
                print(f"No decision found for: {candidate_folder}")

        print(f"\nTotal decisions loaded: {len(self.decisions)}")
        return self.decisions

    def rank_candidates(self):
        print("\nAgent G ranking candidates...")

        advanced = []
        manual_review = []
        rejected = []

        for decision in self.decisions:
            if decision["decision"] == "advance":
                advanced.append(decision)
            elif decision["decision"] == "manual_review":
                manual_review.append(decision)
            else:
                rejected.append(decision)

        advanced.sort(
            key=lambda x: x.get("overall_score") or 0,
            reverse=True
        )

        ranked = advanced + manual_review + rejected

        print(f"Advanced: {len(advanced)}")
        print(f"Manual Review: {len(manual_review)}")
        print(f"Rejected: {len(rejected)}")

        return ranked

    def write_shortlist(self, ranked_candidates):
        filepath = os.path.join(self.runs_folder, "shortlist.csv")

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow([
                "Rank",
                "Candidate ID",
                "Decision",
                "Overall Score",
                "Reason",
                "Decided At"
            ])

            for i, candidate in enumerate(ranked_candidates, start=1):
                writer.writerow([
                    i,
                    candidate.get("candidate_id"),
                    candidate.get("decision"),
                    candidate.get("overall_score"),
                    candidate.get("reason"),
                    candidate.get("decided_at")
                ])

        print(f"\nShortlist saved to {filepath}")

    def write_metrics(self, ranked_candidates):
        total = len(ranked_candidates)
        advanced = sum(1 for c in ranked_candidates if c["decision"] == "advance")
        rejected = sum(1 for c in ranked_candidates if c["decision"] == "reject")
        manual = sum(1 for c in ranked_candidates if c["decision"] == "manual_review")

        metrics = {
            "total_candidates": total,
            "advanced": advanced,
            "rejected": rejected,
            "manual_review": manual,
            "advance_rate": round(advanced / total, 2) if total > 0 else 0,
            "generated_at": datetime.now().isoformat()
        }

        filepath = os.path.join(self.runs_folder, "metrics.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        print(f"Metrics saved to {filepath}")
        return metrics
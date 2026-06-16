import json
import os
from datetime import datetime


class AgentC:
    """
    Agent C - job description matching and fit scoring
    """

    def __init__(self, candidate_id, runs_folder="runs"):
        self.candidate_id = candidate_id
        self.runs_folder = runs_folder
        self.candidate_folder = os.path.join(
            runs_folder,
            candidate_id
        )

        self.candidate = None

        # based on agent B kjo ndrron, niher veq me testu C
        self.job_description = {
            "job_id": "JOB-001",
            "title": "Data Engineer",
            "required_skills": [
                "Python",
                "SQL",
                "Azure",
                "Git",
                "Docker"
            ],
            "must_have_skills": [
                "Python",
                "SQL"
            ],
            "experience_required": 2,
            "education_keywords": [
                "Computer Science",
                "Software Engineering"
            ]
        }


    def load_candidate(self):
        path = os.path.join(
            self.candidate_folder,
            "candidate_profile.json"
        )

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"candidate_profile.json missing for {self.candidate_id}"
            )

        with open(path, "r", encoding="utf-8") as f:
            self.candidate = json.load(f)

        return self.candidate


    def calculate_skill_score(self):

        candidate_skills = [
            skill.lower()
            for skill in self.candidate.get("skills", [])
        ]

        required_skills = [
            skill.lower()
            for skill in self.job_description["required_skills"]
        ]

        matched = [
            skill
            for skill in required_skills
            if skill in candidate_skills
        ]

        missing = [
            skill
            for skill in required_skills
            if skill not in candidate_skills
        ]

        score = len(matched) / len(required_skills)

        return score, matched, missing


    def calculate_experience_score(self):

        candidate_exp = self.candidate.get(
            "experience_years",
            0
        )

        required_exp = self.job_description[
            "experience_required"
        ]

        score = min(
            candidate_exp / required_exp,
            1
        )

        return score


    def calculate_education_score(self):

        education = str(
            self.candidate.get("education", "")
        ).lower()

        keywords = self.job_description[
            "education_keywords"
        ]

        for keyword in keywords:
            if keyword.lower() in education:
                return 1.0

        return 0.5


    def check_must_have(self):

        candidate_skills = [
            s.lower()
            for s in self.candidate.get("skills", [])
        ]

        for skill in self.job_description["must_have_skills"]:
            if skill.lower() not in candidate_skills:
                return False

        return True


    def generate_match_score(self):

        print(
            f"\nscoring candidate {self.candidate_id}"
        )

        self.load_candidate()

        (
            skill_score,
            matched,
            missing
        ) = self.calculate_skill_score()

        experience_score = (
            self.calculate_experience_score()
        )

        education_score = (
            self.calculate_education_score()
        )

        overall = (
            skill_score * 0.5
            + experience_score * 0.3
            + education_score * 0.2
        )

        result = {
            "candidate_id": self.candidate_id,
            "job_id": self.job_description["job_id"],

            "overall_score": round(overall, 2),

            "skill_match_score": round(
                skill_score,
                2
            ),

            "experience_match_score": round(
                experience_score,
                2
            ),

            "education_match_score": round(
                education_score,
                2
            ),

            "skills_matched": matched,

            "skills_missing": missing,

            "experience_years_required":
                self.job_description[
                    "experience_required"
                ],

            "experience_years_candidate":
                self.candidate.get(
                    "experience_years",
                    0
                ),

            "must_have_criteria_met":
                self.check_must_have(),

            "scoring_notes":
                "Weighted score generated using skills, experience, and education",

            "scored_at":
                datetime.now().isoformat()
        }

        return result


    def save_results(self):

        result = self.generate_match_score()

        os.makedirs(
            self.candidate_folder,
            exist_ok=True
        )

        output_path = os.path.join(
            self.candidate_folder,
            "match_scores.json"
        )
        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                result,
                f,
                indent=4
            )

        print(
            f"check {output_path}"
        )

        return result
    
if __name__ == "__main__":

        #test run, ma vone shtohet ne pipeline
        candidates = [
            "candidate_001",
            "candidate_002",
            "candidate_003"
        ]

        for candidate_id in candidates:
            agent = AgentC(
                candidate_id,
                runs_folder="../runs"
            )

            agent.save_results()    
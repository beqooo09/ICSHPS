import json
import os
import re
from datetime import datetime

from dotenv import load_dotenv

from bundle_loader import load_bundle, read_json
from pdf_utils import extract_full_text, find_bbox_for_text

load_dotenv()

CONFIDENCE_THRESHOLD = 0.75
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
RANGE_RE = re.compile(r"\((\d{4})\s*-\s*(\d{4})\)")
KNOWN_SKILLS = ("Python", "SQL", "AWS", "Git", "Power BI", "Excel", "Tableau", "Databricks")


class AgentB:
    """Resume PDF extraction into candidate_profile.json."""

    def __init__(self, bundle_root, runs_folder="runs", candidate_id=None):
        self.bundle_root = os.path.normpath(bundle_root)
        self.runs_folder = runs_folder
        self.candidate_id = candidate_id
        self.bundle = None

    def load(self, strict_files=True):
        self.bundle = load_bundle(self.bundle_root, strict_files=strict_files)
        if not self.candidate_id:
            self.candidate_id = self.bundle["candidate_id"]
        return self.bundle

    def _heuristic_profile(self, text):
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        name = lines[0] if lines else "Unknown"

        email_match = EMAIL_RE.search(text)
        phone_match = PHONE_RE.search(text)

        skills = []
        for skill in KNOWN_SKILLS:
            if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
                skills.append(skill)

        education = []
        for line in lines:
            if re.search(
                r"\b(bsc|bachelor|master|computer science|software engineering|information technology)\b",
                line,
                re.IGNORECASE,
            ):
                degree = line.split(":", 1)[-1].strip() if ":" in line else line
                institution = ""
                grad_year = None
                year_match = YEAR_RE.search(line)
                if year_match:
                    grad_year = int(year_match.group())
                education.append({
                    "degree": degree,
                    "institution": institution,
                    "graduation_year": grad_year,
                    "verified": False,
                })

        experience = []
        tenure_years = []
        for line in lines:
            if re.search(r"\b(developer|analyst|engineer|intern)\b", line, re.IGNORECASE):
                years = None
                range_match = RANGE_RE.search(line)
                title = line.split(":", 1)[-1].strip() if ":" in line else line
                company = ""
                if range_match:
                    years = int(range_match.group(2)) - int(range_match.group(1))
                    tenure_years.append(years)
                experience.append({
                    "job_title": title,
                    "company": company,
                    "start_date": None,
                    "end_date": None,
                    "description": line,
                    "years": years,
                })

        certifications = []
        for line in lines:
            if line.lower().startswith("skills:"):
                continue
            if re.search(r"(?i)\b(certified|certifications?\s*:)", line):
                value = line.split(":", 1)[-1].strip() if ":" in line else line
                if value:
                    certifications.append(value)

        projects = []
        for line in lines:
            if re.search(r"\b(project|portfolio)\b", line, re.IGNORECASE):
                projects.append(line.split(":", 1)[-1].strip() if ":" in line else line)

        total_years = sum(tenure_years) if tenure_years else None

        location = None
        for line in lines[1:3]:
            if "@" not in line and "|" not in line and len(line) < 60:
                location = line
                break

        return {
            "name": name,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0).strip() if phone_match else None,
            "location": location,
            "skills": skills,
            "education": education,
            "experience": experience,
            "certifications": certifications,
            "projects": projects,
            "total_years_experience": total_years,
        }

    def _openai_profile(self, text):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        "Extract resume as JSON with keys: name, email, phone, location, "
                        "skills (list), education (list of objects with degree, institution, "
                        "graduation_year), experience (list with job_title, company, description), "
                        "certifications (list), experience_years (int). JSON only.\n\n"
                        f"Resume:\n{text}"
                    ),
                }],
                temperature=0,
            )
            content = response.choices[0].message.content or ""
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1:
                return None
            return json.loads(content[start : end + 1])
        except Exception:
            return None

    def _score_confidence(self, profile, raw_text):
        scores = {}
        name = str(profile.get("name", ""))
        scores["name"] = 0.95 if name and name.lower() in raw_text.lower() else 0.55

        email = profile.get("email")
        scores["email"] = 0.99 if email and email in raw_text else 0.4

        phone = profile.get("phone")
        scores["phone"] = (
            0.9
            if phone and re.sub(r"\s", "", phone) in re.sub(r"\s", "", raw_text)
            else 0.5
        )

        skills = profile.get("skills") or []
        if skills:
            matched = sum(
                1 for s in skills if re.search(rf"\b{re.escape(s)}\b", raw_text, re.I)
            )
            scores["skills"] = round(matched / len(skills), 2)
        else:
            scores["skills"] = 0.3

        education = profile.get("education") or []
        scores["education"] = 0.9 if education else 0.45

        grad_years = YEAR_RE.findall(raw_text)
        scores["graduation_year"] = 0.85 if grad_years else 0.6

        experience = profile.get("experience") or []
        scores["experience"] = 0.9 if experience else 0.5

        certs = profile.get("certifications") or []
        scores["certifications"] = 0.88 if certs else 0.55

        return scores

    def _bounding_boxes(self, resume_path, profile):
        boxes = {}
        name = str(profile.get("name", ""))
        if name:
            bbox = find_bbox_for_text(resume_path, name)
            if bbox:
                boxes["name"] = bbox
        email = profile.get("email")
        if email:
            bbox = find_bbox_for_text(resume_path, email)
            if bbox:
                boxes["email"] = bbox
        for skill in profile.get("skills") or []:
            bbox = find_bbox_for_text(resume_path, str(skill))
            if bbox:
                boxes[f"skill:{skill}"] = bbox
        return boxes

    def _to_candidate_profile(self, parsed, raw_text, confidence, bounding_boxes, anomalies):
        experience = []
        for item in parsed.get("experience") or []:
            experience.append({
                "job_title": item.get("job_title") or item.get("title", ""),
                "company": item.get("company", ""),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
                "description": item.get("description", ""),
            })

        education = parsed.get("education") or []
        normalized_education = []
        for item in education:
            if isinstance(item, str):
                normalized_education.append({
                    "degree": item,
                    "institution": "",
                    "graduation_year": None,
                    "verified": False,
                })
            else:
                normalized_education.append({
                    "degree": item.get("degree", ""),
                    "institution": item.get("institution", ""),
                    "graduation_year": item.get("graduation_year"),
                    "verified": False,
                })

        overall = round(sum(confidence.values()) / len(confidence), 2) if confidence else 0.5
        review_fields = sorted(
            field for field, score in confidence.items() if score < CONFIDENCE_THRESHOLD
        )

        return {
            "candidate_id": self.candidate_id,
            "name": parsed.get("name"),
            "email": parsed.get("email"),
            "phone": parsed.get("phone"),
            "location": parsed.get("location"),
            "education": normalized_education,
            "experience": experience,
            "skills": parsed.get("skills") or [],
            "certifications": parsed.get("certifications") or [],
            "experience_years": parsed.get("total_years_experience")
            or parsed.get("experience_years"),
            "extraction_confidence": overall,
            "extraction_method": "pdf_text",
            "anomalies_detected": anomalies,
            "raw_text_preview": raw_text[:300],
            "field_confidence": confidence,
            "fields_needing_review": review_fields,
            "bounding_boxes": bounding_boxes,
        }

    def run(self, strict_files=True, agent_a_output=None):
        print(f"\nAgent B processing bundle: {self.bundle_root}")
        self.load(strict_files=strict_files)

        if agent_a_output and agent_a_output.get("risk_assessment", {}).get("status") == "rejected":
            print("Skipping extraction — Agent A risk status is rejected")
            return None

        resume_path = self.bundle["paths"]["resume"]
        if not resume_path.lower().endswith(".pdf"):
            return {
                "error": "unsupported_format",
                "format": os.path.splitext(resume_path)[1],
            }

        if not os.path.exists(resume_path):
            return None

        raw_text = extract_full_text(resume_path)
        llm = self._openai_profile(raw_text)
        parsed = self._heuristic_profile(raw_text)
        if llm:
            parsed.update({k: v for k, v in llm.items() if v})

        confidence = self._score_confidence(parsed, raw_text)
        bounding_boxes = self._bounding_boxes(resume_path, parsed)
        anomalies = []
        if confidence.get("email", 1) < CONFIDENCE_THRESHOLD:
            anomalies.append("low_confidence_email")

        profile = self._to_candidate_profile(
            parsed, raw_text, confidence, bounding_boxes, anomalies
        )
        print(f"Extracted: {profile['name']} | confidence: {profile['extraction_confidence']}")
        return profile

    def write_output(self, profile):
        if profile is None:
            print("No profile to write")
            return None

        candidate_folder = os.path.join(self.runs_folder, self.candidate_id)
        os.makedirs(candidate_folder, exist_ok=True)
        filepath = os.path.join(candidate_folder, "candidate_profile.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        print(f"Agent B output saved to {filepath}")
        return filepath

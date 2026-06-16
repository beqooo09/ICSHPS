import json
import os
import re
from datetime import datetime

from bundle_loader import (
    extract_pdf_text,
    load_bundle,
    read_json,
    read_text,
    read_yaml,
)


class AgentA:
    """Application intake, context packet, evidence index, and risk filtering."""

    MIN_RESUME_CHARS = 80

    def __init__(self, bundle_root, runs_folder="runs", known_emails=None):
        self.bundle_root = os.path.normpath(bundle_root)
        self.runs_folder = runs_folder
        self.known_emails = known_emails if known_emails is not None else set()
        self.bundle = None
        self.warnings = []

    def load(self, strict_files=True):
        self.bundle = load_bundle(self.bundle_root, strict_files=strict_files)
        return self.bundle

    def _file_inventory(self):
        manifest_files = self.bundle["manifest"]["files"]
        root = self.bundle["root"]
        paths = self.bundle["paths"]
        inventory = []

        def add_entry(key, path):
            inventory.append({
                "key": key,
                "path": os.path.relpath(path, root),
                "exists": os.path.exists(path),
            })

        add_entry("resume", paths["resume"])
        add_entry("application_form", paths["application_form"])
        if manifest_files.get("cover_letter"):
            add_entry("cover_letter", paths["cover_letter"])
        for idx, portfolio_path in enumerate(paths.get("portfolio", []), start=1):
            add_entry(f"portfolio_{idx}", portfolio_path)
        return inventory

    def _standardized_package(self):
        manifest = self.bundle["manifest"]
        form_data = read_json(self.bundle["paths"]["application_form"])
        cover_letter = None
        if self.bundle["paths"].get("cover_letter"):
            cover_letter = read_text(self.bundle["paths"]["cover_letter"])

        resume_preview = None
        resume_path = self.bundle["paths"]["resume"]
        if os.path.exists(resume_path):
            resume_preview = extract_pdf_text(resume_path)[:500]

        return {
            "candidate_id": self.bundle["candidate_id"],
            "source": manifest["source"],
            "application_type": manifest["application_type"],
            "candidate_category": manifest["candidate_category"],
            "file_inventory": self._file_inventory(),
            "form_data": form_data,
            "cover_letter_text": cover_letter,
            "resume_text_preview": resume_preview,
        }

    def _context_packet(self):
        job = self.bundle["manifest"]["job"]
        requirements = read_yaml(self.bundle["paths"]["job_requirements"])
        return {
            "role_title": job["role_title"],
            "job_id": job["job_id"],
            "job_description": read_text(self.bundle["paths"]["job_description"]).strip(),
            "required_skills": list(requirements.get("required_skills", [])),
            "preferred_skills": list(requirements.get("preferred_skills", [])),
            "experience_years_min": requirements.get("experience_years_min"),
            "location": dict(requirements.get("location", {})),
            "hiring_manager_preferences": list(requirements.get("hiring_manager_preferences", [])),
            "eeo_requirements": list(requirements.get("eeo_requirements", [])),
        }

    def _guess_section_type(self, text):
        lowered = text.lower()
        if lowered.startswith("skills:") or any(
            k in lowered for k in ("skill:", "python", "sql", "power bi", "git")
        ):
            return "skills"
        if any(
            k in lowered
            for k in ("education", "bsc", "bachelor", "university", "software engineering")
        ):
            return "education"
        if any(k in lowered for k in ("certification", "certified")) and not lowered.startswith(
            "skills:"
        ):
            return "certification"
        if any(k in lowered for k in ("experience", "developer", "analyst", "engineer")):
            return "experience"
        return "general"

    def _evidence_index(self):
        entries = []
        counter = 1
        root = self.bundle["root"]

        def add_chunks(source_file, text):
            nonlocal counter
            chunks = [text] if len(text) <= 120 else [
                text[i : i + 120].strip() for i in range(0, len(text), 120)
            ]
            for chunk in chunks:
                if not chunk:
                    continue
                entries.append({
                    "evidence_id": f"E{counter:03d}",
                    "source_file": source_file,
                    "text_span": chunk,
                    "section_type": self._guess_section_type(chunk),
                })
                counter += 1

        resume_path = self.bundle["paths"]["resume"]
        if os.path.exists(resume_path):
            for line in [
                ln.strip() for ln in extract_pdf_text(resume_path).splitlines() if ln.strip()
            ]:
                entries.append({
                    "evidence_id": f"E{counter:03d}",
                    "source_file": os.path.relpath(resume_path, root),
                    "text_span": line,
                    "section_type": self._guess_section_type(line),
                })
                counter += 1

        form_path = self.bundle["paths"]["application_form"]
        add_chunks(
            os.path.relpath(form_path, root),
            json.dumps(read_json(form_path), sort_keys=True),
        )

        cover_path = self.bundle["paths"].get("cover_letter")
        if cover_path and os.path.exists(cover_path):
            normalized = re.sub(r"\s+", " ", read_text(cover_path)).strip()
            add_chunks(os.path.relpath(cover_path, root), normalized)

        return entries

    def _assess_risk(self):
        flags = []
        resume_path = self.bundle["paths"]["resume"]

        if not os.path.exists(resume_path):
            return {
                "status": "rejected",
                "risk_flags": [{
                    "code": "missing_resume",
                    "message": "Resume file is missing",
                }],
            }

        if not read_text(self.bundle["paths"]["job_description"]).strip():
            flags.append({"code": "empty_jd", "message": "Job description is empty"})

        resume_text = extract_pdf_text(resume_path)
        if len(resume_text) < self.MIN_RESUME_CHARS:
            flags.append({
                "code": "suspicious_resume",
                "message": f"Resume text shorter than {self.MIN_RESUME_CHARS} characters",
            })

        form_data = read_json(self.bundle["paths"]["application_form"])
        email = str(form_data.get("email", "")).strip().lower()
        if email and email in self.known_emails:
            flags.append({
                "code": "duplicate_application",
                "message": f"Duplicate application email detected: {email}",
            })
        elif email:
            self.known_emails.add(email)

        if flags:
            return {"status": "flagged", "risk_flags": flags}
        return {"status": "clean", "risk_flags": []}

    def run(self, strict_files=True):
        print(f"\nAgent A processing bundle: {self.bundle_root}")
        self.load(strict_files=strict_files)

        output = {
            "bundle_id": self.bundle["manifest"]["bundle_id"],
            "candidate_id": self.bundle["candidate_id"],
            "processed_at": datetime.now().isoformat(),
            "processed_by": "Agent_A",
            "standardized_candidate_package": self._standardized_package(),
            "context_packet": self._context_packet(),
            "evidence_index": self._evidence_index(),
            "risk_assessment": self._assess_risk(),
        }

        print(f"Risk status: {output['risk_assessment']['status']}")
        return output

    def write_output(self, output):
        candidate_folder = os.path.join(self.runs_folder, self.bundle["candidate_id"])
        os.makedirs(candidate_folder, exist_ok=True)
        filepath = os.path.join(candidate_folder, "agent_a.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        print(f"Agent A output saved to {filepath}")
        return filepath

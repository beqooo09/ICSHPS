#!/usr/bin/env python3
"""Generate resume PDFs for manifest-based hiring bundles."""

import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUNDLE_RESUMES = {
    "synthetic_data_analyst_001": [
        "Jane Doe",
        "jane.doe@example.com | +1-555-0100",
        "Skills: Python, SQL, Power BI, Excel",
        "Experience: Python Developer at ABC Corp (2020-2024)",
        "Education: BSc Computer Science, State University, 2019",
        "Certifications: AWS Certified Cloud Practitioner",
        "Projects: Sales dashboard portfolio project",
    ],
    "synthetic_duplicate_email_003": [
        "Alex Smith",
        "jane.doe@example.com | +1-555-0199",
        "Skills: Python, SQL",
        "Experience: Data Analyst at XYZ Inc (2019-2023)",
        "Education: BSc Mathematics, City College, 2018",
    ],
    "candidate_ana_krasniqi": [
        "Ana Krasniqi",
        "ana.krasniqi@email.com | +383-44-123-456",
        "Skills: Python, SQL, Databricks, Git, Azure",
        "Experience: Junior Data Engineer at TechCorp Kosovo (2023-2025)",
        "Education: BSc Computer Science, University of Pristina, 2023",
        "Certifications: Azure Data Fundamentals",
    ],
    "candidate_mentor_berisha": [
        "Mentor Berisha",
        "mentor.berisha@email.com | +383-44-987-654",
        "Skills: JavaScript, HTML, CSS, Git",
        "Experience: Junior Developer at SoftCo (2022-2024)",
        "Education: BSc Information Technology, University of Prizren, 2022",
    ],
    "candidate_vjosa_gashi": [
        "VjosaGashi",
        "Data Analyst",
        "vjosagashiemailcom",
        "PythonSQLPowerBI",
        "MastersComputerScience",
    ],
}


def write_resume_pdf(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c = canvas.Canvas(path, pagesize=letter)
    y = letter[1] - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
        if y < 72:
            c.showPage()
            y = letter[1] - 72
    c.save()


def main():
    for bundle_id, lines in BUNDLE_RESUMES.items():
        path = os.path.join(ROOT, "hiring_bundles", bundle_id, "resume", "resume.pdf")
        write_resume_pdf(path, lines)
        print(f"Wrote {path}")

    portfolio = os.path.join(
        ROOT, "hiring_bundles", "synthetic_data_analyst_001", "portfolio", "sample_project.pdf"
    )
    os.makedirs(os.path.dirname(portfolio), exist_ok=True)
    c = canvas.Canvas(portfolio, pagesize=letter)
    c.drawString(72, 720, "Sample portfolio project: sales dashboard")
    c.save()
    print(f"Wrote {portfolio}")


if __name__ == "__main__":
    main()
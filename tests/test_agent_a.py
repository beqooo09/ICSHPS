import os
import tempfile

from agents.agent_a import AgentA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAPPY = os.path.join(ROOT, "hiring_bundles", "synthetic_data_analyst_001")
MISSING = os.path.join(ROOT, "hiring_bundles", "synthetic_missing_resume_002")
DUPLICATE = os.path.join(ROOT, "hiring_bundles", "synthetic_duplicate_email_003")


def test_agent_a_happy_path():
    with tempfile.TemporaryDirectory() as tmp:
        agent = AgentA(HAPPY, runs_folder=tmp)
        output = agent.run()
        assert output["risk_assessment"]["status"] == "clean"
        assert output["context_packet"]["role_title"] == "Data Analyst"
        assert "SQL" in output["context_packet"]["required_skills"]
        assert "Power BI" in output["context_packet"]["preferred_skills"]
        assert output["evidence_index"][0]["evidence_id"] == "E001"
        assert agent.write_output(output)


def test_agent_a_missing_resume_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        agent = AgentA(MISSING, runs_folder=tmp)
        output = agent.run(strict_files=False)
        assert output["risk_assessment"]["status"] == "rejected"


def test_agent_a_duplicate_email_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        known = set()
        first = AgentA(HAPPY, runs_folder=tmp, known_emails=known).run()
        assert first["risk_assessment"]["status"] == "clean"
        dup = AgentA(DUPLICATE, runs_folder=tmp, known_emails=known).run()
        assert dup["risk_assessment"]["status"] == "flagged"

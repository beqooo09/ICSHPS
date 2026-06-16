import os
import tempfile

from agents.agent_b import AgentB

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAPPY = os.path.join(ROOT, "hiring_bundles", "synthetic_data_analyst_001")


def test_agent_b_profile_shape():
    with tempfile.TemporaryDirectory() as tmp:
        agent = AgentB(HAPPY, runs_folder=tmp, candidate_id="C101")
        profile = agent.run()
        assert profile["candidate_id"] == "C101"
        assert profile["name"] == "Jane Doe"
        assert "skills" in profile
        assert "field_confidence" in profile
        assert "bounding_boxes" in profile
        assert agent.write_output(profile)


def test_agent_b_confidence_and_certs():
    with tempfile.TemporaryDirectory() as tmp:
        profile = AgentB(HAPPY, runs_folder=tmp, candidate_id="C101").run()
        assert profile["field_confidence"]["email"] >= 0.9
        assert profile["certifications"]


def test_agent_b_bounding_boxes():
    with tempfile.TemporaryDirectory() as tmp:
        profile = AgentB(HAPPY, runs_folder=tmp, candidate_id="C101").run()
        assert profile["bounding_boxes"]
        sample = next(iter(profile["bounding_boxes"].values()))
        assert {"page", "x0", "y0", "x1", "y1"}.issubset(sample)

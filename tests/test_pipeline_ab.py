import os
import tempfile

from agents.agent_a import AgentA
from agents.agent_b import AgentB

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLES = [
    os.path.join(ROOT, "hiring_bundles", "synthetic_data_analyst_001"),
    os.path.join(ROOT, "hiring_bundles", "synthetic_duplicate_email_003"),
]


def test_pipeline_a_to_b():
    with tempfile.TemporaryDirectory() as tmp:
        known = set()
        for bundle_path in BUNDLES:
            agent_a = AgentA(bundle_path, runs_folder=tmp, known_emails=known)
            a_out = agent_a.run()
            assert a_out["risk_assessment"]["status"] in {"clean", "flagged"}
            agent_a.write_output(a_out)

            agent_b = AgentB(bundle_path, runs_folder=tmp, candidate_id=a_out["candidate_id"])
            profile = agent_b.run(agent_a_output=a_out)
            assert profile is not None
            assert profile["skills"]
            agent_b.write_output(profile)

            profile_path = os.path.join(tmp, a_out["candidate_id"], "candidate_profile.json")
            agent_a_path = os.path.join(tmp, a_out["candidate_id"], "agent_a.json")
            assert os.path.exists(profile_path)
            assert os.path.exists(agent_a_path)

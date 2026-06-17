#!/usr/bin/env python3
"""Run Agents A and B on all manifest-based hiring bundles."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agents.agent_a import AgentA
from agents.agent_b import AgentB

HIRING_BUNDLES = os.path.join(ROOT, "hiring_bundles")
RUNS = os.path.join(ROOT, "runs")


def is_manifest_bundle(bundle_path):
    return os.path.exists(os.path.join(bundle_path, "manifest.yaml"))


def main():
    import subprocess

    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "generate_synthetic_pdfs.py")], check=True)

    bundles = sorted(
        b
        for b in os.listdir(HIRING_BUNDLES)
        if os.path.isdir(os.path.join(HIRING_BUNDLES, b)) and is_manifest_bundle(os.path.join(HIRING_BUNDLES, b))
    )

    print(f"Found {len(bundles)} manifest bundles: {bundles}")
    known_emails = set()

    for bundle_name in bundles:
        bundle_path = os.path.join(HIRING_BUNDLES, bundle_name)
        agent_a = AgentA(bundle_path, runs_folder=RUNS, known_emails=known_emails)
        strict = not bundle_name.endswith("missing_resume_002")
        a_out = agent_a.run(strict_files=strict)
        agent_a.write_output(a_out)

        if a_out["risk_assessment"]["status"] != "rejected":
            agent_b = AgentB(bundle_path, runs_folder=RUNS, candidate_id=a_out["candidate_id"])
            profile = agent_b.run(strict_files=strict, agent_a_output=a_out)
            agent_b.write_output(profile)


if __name__ == "__main__":
    main()

import os
import json
import shutil
from datetime import datetime
from agents.agent_h import AgentH
from agents.agent_g import AgentG
from agents.agent_a import AgentA
from agents.agent_b import AgentB
from agents.agent_c import AgentC
from agents.agent_d import AgentD
from agents.agent_e import AgentE

HIRING_BUNDLES_FOLDER = "hiring_bundles"
RUNS_FOLDER = "runs"


def is_manifest_bundle(bundle_path):
    return os.path.exists(os.path.join(bundle_path, "manifest.yaml"))


def run_agents_a_and_b():
    """Process manifest-based bundles through Agents A and B."""
    if not os.path.exists(HIRING_BUNDLES_FOLDER):
        return

    bundles = sorted(
        b
        for b in os.listdir(HIRING_BUNDLES_FOLDER)
        if os.path.isdir(os.path.join(HIRING_BUNDLES_FOLDER, b))
        and is_manifest_bundle(os.path.join(HIRING_BUNDLES_FOLDER, b))
    )

    if not bundles:
        print("\nNo manifest-based bundles found — skipping Agents A & B")
        return

    print(f"\n--- Running Agents A & B on {len(bundles)} manifest bundles ---")
    known_emails = set()

    for bundle_name in bundles:
        bundle_path = os.path.join(HIRING_BUNDLES_FOLDER, bundle_name)
        strict = "missing_resume" not in bundle_name

        agent_a = AgentA(bundle_path, runs_folder=RUNS_FOLDER, known_emails=known_emails)
        a_out = agent_a.run(strict_files=strict)
        agent_a.write_output(a_out)

        if a_out["risk_assessment"]["status"] != "rejected":
            agent_b = AgentB(bundle_path, runs_folder=RUNS_FOLDER, candidate_id=a_out["candidate_id"])
            profile = agent_b.run(strict_files=strict, agent_a_output=a_out)
            agent_b.write_output(profile)


def run_agents_c_d_e(candidate_id):
    """Run Agent C, D, E for one candidate. Skips gracefully if inputs are missing."""
    candidate_folder = os.path.join(RUNS_FOLDER, candidate_id)
    profile_path = os.path.join(candidate_folder, "candidate_profile.json")

    if not os.path.exists(profile_path):
        print(f"Skipping Agents C/D/E for {candidate_id} — no candidate_profile.json")
        return

    try:
        agent_c = AgentC(candidate_id, runs_folder=RUNS_FOLDER)
        agent_c.save_results()
    except Exception as e:
        print(f"Agent C failed for {candidate_id}: {e}")

    try:
        agent_d = AgentD(candidate_id, runs_folder=RUNS_FOLDER)
        agent_d.save_results()
    except Exception as e:
        print(f"Agent D failed for {candidate_id}: {e}")

    agent_a_path = os.path.join(candidate_folder, "agent_a.json")
    if os.path.exists(agent_a_path):
        try:
            agent_e = AgentE(candidate_id, runs_folder=RUNS_FOLDER)
            agent_e.save_results()
        except Exception as e:
            print(f"Agent E failed for {candidate_id}: {e}")
    else:
        print(f"Skipping Agent E for {candidate_id} — no agent_a.json (evidence index unavailable)")


def prepare_run_folder(bundle_name):
    src = os.path.join(HIRING_BUNDLES_FOLDER, bundle_name)

    candidate_id = bundle_name.replace("candidate_0", "C0").replace("candidate_", "C")
    manifest_path = os.path.join(src, "manifest.yaml")
    if os.path.exists(manifest_path):
        import yaml
        with open(manifest_path, encoding="utf-8") as f:
            candidate_id = yaml.safe_load(f)["metadata"]["candidate_id"]

    dst = os.path.join(RUNS_FOLDER, candidate_id)

    os.makedirs(dst, exist_ok=True)

    profile_src = os.path.join(src, "candidate_profile.json")
    profile_dst = os.path.join(dst, "candidate_profile.json")

    if os.path.exists(profile_src) and not os.path.exists(profile_dst):
        shutil.copy2(profile_src, profile_dst)
        print(f"Copied legacy profile for {candidate_id}")

    return candidate_id


def run_pipeline():
    print("=" * 60)
    print("ICSHPS - Intelligent Candidate Screening Pipeline")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not os.path.exists(HIRING_BUNDLES_FOLDER):
        print("No hiring_bundles folder found. Exiting.")
        return

    bundles = [b for b in os.listdir(HIRING_BUNDLES_FOLDER)
               if os.path.isdir(os.path.join(HIRING_BUNDLES_FOLDER, b))]

    print(f"\nFound {len(bundles)} candidate bundles: {bundles}")

    run_agents_a_and_b()

    print("\n--- Running Agents C, D, E and then Agent H for all candidates ---")
    for bundle in bundles:
        candidate_id = prepare_run_folder(bundle)
        print(f"\nProcessing: {candidate_id}")

        run_agents_c_d_e(candidate_id)

        agent_h = AgentH(candidate_id, runs_folder=RUNS_FOLDER)
        agent_h.load_all_outputs()
        decision = agent_h.make_decision()
        agent_h.write_decision(decision)
        agent_h.write_audit_log(decision)

    print("\n--- Running Agent G - Ranking all candidates ---")
    agent_g = AgentG(runs_folder=RUNS_FOLDER)
    agent_g.load_all_decisions()
    ranked = agent_g.rank_candidates()
    agent_g.write_shortlist(ranked)
    agent_g.write_metrics(ranked)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nResults saved to: {RUNS_FOLDER}/")
    print(f"  - shortlist.csv")
    print(f"  - metrics.json")
    print(f"  - [candidate_id]/hiring_decision.json")
    print(f"  - [candidate_id]/audit_log.md")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nRun dashboard:")
    print("  python -m streamlit run dashboard/app.py")


if __name__ == "__main__":
    run_pipeline()
import os
import json
import shutil
from datetime import datetime
from agents.agent_h import AgentH
from agents.agent_g import AgentG

HIRING_BUNDLES_FOLDER = "hiring_bundles"
RUNS_FOLDER = "runs"

def prepare_run_folder(bundle_name):
    src = os.path.join(HIRING_BUNDLES_FOLDER, bundle_name)
    
    candidate_id = bundle_name.replace("candidate_0", "C0").replace("candidate_", "C")
    dst = os.path.join(RUNS_FOLDER, candidate_id)
    
    os.makedirs(dst, exist_ok=True)
    
    profile_src = os.path.join(src, "candidate_profile.json")
    profile_dst = os.path.join(dst, "candidate_profile.json")
    
    if os.path.exists(profile_src):
        shutil.copy2(profile_src, profile_dst)
        print(f"Copied profile for {candidate_id}")
    
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

    print("\n--- Running Agent H for all candidates ---")
    for bundle in bundles:
        candidate_id = prepare_run_folder(bundle)
        print(f"\nProcessing: {candidate_id}")

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
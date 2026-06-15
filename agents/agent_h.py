import json
import os
from datetime import datetime

class AgentH:
    
    def __init__(self, candidate_id, runs_folder="runs"):
        self.candidate_id = candidate_id
        self.runs_folder = runs_folder
        self.candidate_folder = os.path.join(runs_folder, candidate_id)
        self.data = {}
        self.warnings = []
    
    def load_file(self, filename):
        filepath = os.path.join(self.candidate_folder, filename)
        
        if not os.path.exists(filepath):
            warning = f"WARNING: {filename} not found for {self.candidate_id}"
            self.warnings.append(warning)
            print(warning)
            return None
        
        with open(filepath, "r") as f:
            return json.load(f)
    
    def load_all_outputs(self):
        print(f"\nAgent H loading data for candidate: {self.candidate_id}")
        
        self.data["profile"] = self.load_file("candidate_profile.json")
        self.data["match_scores"] = self.load_file("match_scores.json")
        self.data["compliance_flags"] = self.load_file("compliance_flags.json")
        self.data["credential_report"] = self.load_file("credential_report.json")
        
        print(f"Loaded {sum(1 for v in self.data.values() if v is not None)} out of 4 files")
        return self.data
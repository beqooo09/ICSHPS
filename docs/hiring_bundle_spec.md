# Hiring Bundle Specification

A **hiring bundle** is a folder under `hiring_bundles/` that contains everything Agent A and Agent B need to process one application.

## Layout

```text
hiring_bundles/<bundle_id>/
  manifest.yaml
  job/
    description.md
    requirements.yaml
  application/
    form.json
    cover_letter.txt          # optional
  resume/
    resume.pdf
  portfolio/                  # optional
```

## Pipeline outputs (written to `runs/<candidate_id>/`)

| File | Agent | Description |
|------|-------|-------------|
| `agent_a.json` | A | Intake package, context packet, evidence index, risk assessment |
| `candidate_profile.json` | B | Structured resume extraction (feeds Agents C–H) |

`candidate_id` is taken from `manifest.yaml` → `metadata.candidate_id` (e.g. `C001`).

## manifest.yaml

| Field | Required | Description |
|-------|----------|-------------|
| `bundle_id` | yes | Must match folder name |
| `source` | yes | `career_portal`, `email`, `linkedin`, `job_board`, or `referral` |
| `application_type` | yes | e.g. `standard`, `referral` |
| `candidate_category` | yes | e.g. `experienced`, `new_grad` |
| `job.role_title` | yes | Role title |
| `job.job_id` | yes | Job reference (used by Agent C) |
| `job.description` | yes | Relative path to JD markdown |
| `job.requirements` | yes | Relative path to requirements YAML |
| `files.resume` | yes | Relative path to resume PDF |
| `files.application_form` | yes | Relative path to form JSON |
| `files.cover_letter` | optional | Cover letter path |
| `files.portfolio` | optional | List of attachment paths |
| `metadata.candidate_id` | yes | Pipeline ID e.g. `C001` |
| `metadata.submitted_at` | yes | ISO-8601 timestamp |

## job/requirements.yaml

```yaml
required_skills:
  - Python
  - SQL
preferred_skills:
  - AWS
  - Git
experience_years_min: 2
location:
  city: Berlin
  country: DE
hiring_manager_preferences:
  - clean code
eeo_requirements:
  - collect_voluntary_self_id
```

## Legacy bundles

Folders with only `candidate_profile.json` (e.g. `candidate_001`) are pre-seeded samples for Agents C–H. New work should use the manifest-based layout above.

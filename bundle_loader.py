import json
import os

import jsonschema
import yaml
from PyPDF2 import PdfReader

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "manifest.schema.json")


class BundleValidationError(ValueError):
    pass


def _load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_manifest(bundle_root):
    manifest_path = os.path.join(bundle_root, "manifest.yaml")
    if not os.path.exists(manifest_path):
        raise BundleValidationError(f"Missing manifest.yaml in {bundle_root}")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    jsonschema.validate(instance=manifest, schema=_load_schema())

    folder_name = os.path.basename(os.path.normpath(bundle_root))
    if manifest["bundle_id"] != folder_name:
        raise BundleValidationError(
            f"bundle_id '{manifest['bundle_id']}' does not match folder '{folder_name}'"
        )

    return manifest


def _resolve(bundle_root, relative):
    return os.path.normpath(os.path.join(bundle_root, relative))


def collect_paths(bundle_root, manifest):
    files = manifest["files"]
    paths = {
        "resume": _resolve(bundle_root, files["resume"]),
        "application_form": _resolve(bundle_root, files["application_form"]),
        "job_description": _resolve(bundle_root, manifest["job"]["description"]),
        "job_requirements": _resolve(bundle_root, manifest["job"]["requirements"]),
    }
    if files.get("cover_letter"):
        paths["cover_letter"] = _resolve(bundle_root, files["cover_letter"])
    paths["portfolio"] = [_resolve(bundle_root, p) for p in files.get("portfolio") or []]
    return paths


def validate_files_exist(paths):
    for key in ("resume", "application_form", "job_description", "job_requirements"):
        if not os.path.exists(paths[key]):
            raise BundleValidationError(f"Missing required file: {paths[key]}")
    cover = paths.get("cover_letter")
    if cover and not os.path.exists(cover):
        raise BundleValidationError(f"Missing cover letter: {cover}")
    for portfolio_path in paths.get("portfolio", []):
        if not os.path.exists(portfolio_path):
            raise BundleValidationError(f"Missing portfolio file: {portfolio_path}")


def load_bundle(bundle_root, strict_files=True):
    bundle_root = os.path.normpath(bundle_root)
    if not os.path.isdir(bundle_root):
        raise BundleValidationError(f"Not a directory: {bundle_root}")

    manifest = load_manifest(bundle_root)
    paths = collect_paths(bundle_root, manifest)

    if strict_files:
        validate_files_exist(paths)

    return {
        "root": bundle_root,
        "manifest": manifest,
        "paths": paths,
        "candidate_id": manifest["metadata"]["candidate_id"],
    }


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_yaml(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise BundleValidationError(f"Expected YAML mapping in {path}")
    return data


def extract_pdf_text(path):
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()

import os

import pytest

from bundle_loader import BundleValidationError, load_bundle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAPPY = os.path.join(ROOT, "hiring_bundles", "synthetic_data_analyst_001")
MISSING = os.path.join(ROOT, "hiring_bundles", "synthetic_missing_resume_002")


def test_load_valid_bundle():
    bundle = load_bundle(HAPPY)
    assert bundle["manifest"]["bundle_id"] == "synthetic_data_analyst_001"
    assert bundle["candidate_id"] == "C101"
    assert os.path.exists(bundle["paths"]["resume"])


def test_missing_manifest():
    with pytest.raises(BundleValidationError, match="Missing manifest.yaml"):
        load_bundle(os.path.join(ROOT, "hiring_bundles", "candidate_001"))


def test_missing_resume_strict():
    with pytest.raises(BundleValidationError, match="Missing required file"):
        load_bundle(MISSING, strict_files=True)


def test_missing_resume_lenient():
    bundle = load_bundle(MISSING, strict_files=False)
    assert not os.path.exists(bundle["paths"]["resume"])

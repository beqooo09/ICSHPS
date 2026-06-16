import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session", autouse=True)
def generate_pdfs():
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "generate_synthetic_pdfs.py")],
        check=True,
        cwd=ROOT,
    )

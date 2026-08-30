import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import pytest


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parent.parent


def test_publish_script_dry_run(repo_root):
    ps_script = repo_root / "scripts" / "publish-pages.ps1"
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script), "-DryRun"]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert proc.returncode == 0
    assert "[DryRun OK]" in proc.stdout


def test_publish_script_local_bare_git(repo_root):
    ps_script = repo_root / "scripts" / "publish-pages.ps1"

    with tempfile.TemporaryDirectory() as tmp:
        bare_repo = Path(tmp) / "bare_remote.git"
        # Init bare repo
        subprocess.run(["git", "init", "--bare", str(bare_repo)], check=True, capture_output=True)

        # 1. First publish (orphan branch creation)
        cmd1 = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps_script),
            "-RemoteUrlOverride",
            str(bare_repo),
        ]
        proc1 = subprocess.run(
            cmd1,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        assert proc1.returncode == 0
        assert "[Publish SUCCESS]" in proc1.stdout

        # Verify gh-pages branch in bare repo
        heads = subprocess.run(
            ["git", "--git-dir", str(bare_repo), "branch", "-a"], check=True, capture_output=True, text=True
        )
        assert "gh-pages" in heads.stdout

        # 2. A second publish has a new generated_at and creates another commit
        proc2 = subprocess.run(
            cmd1,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        assert proc2.returncode == 0
        assert "[Publish SUCCESS]" in proc2.stdout

        commit_count = subprocess.run(
            ["git", "--git-dir", str(bare_repo), "rev-list", "--count", "gh-pages"],
            check=True,
            capture_output=True,
            text=True,
        )
        assert commit_count.stdout.strip() == "2"


def test_publish_script_invalid_remote_fails(repo_root):
    ps_script = repo_root / "scripts" / "publish-pages.ps1"
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps_script),
        "-RemoteUrlOverride",
        "https://invalid.example.com/non-existent.git",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert proc.returncode != 0
    assert "[Publish SUCCESS]" not in proc.stdout

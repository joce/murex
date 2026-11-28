"""The repository itself: its images, and the binary files among the
references of the media (papers, spectral libraries), are in Git LFS, as
.gitattributes says.

A machine without git-lfs commits an image as an ordinary file, and every
version of it then stays in the history that each clone downloads. These
tests read what git holds (the index, so an image staged but not yet
committed counts), not the working tree, which git-lfs fills in either way.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ("*.png", "*.jpg", "*.pdf", "*.sli", "*.xls", "*.zip")
POINTER = re.compile(rb"\Aversion https://git-lfs\.github\.com/spec/v1\n")


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=True
    ).stdout


def _in_a_checkout() -> bool:
    if shutil.which("git") is None:
        return False
    try:
        return _git("rev-parse", "--show-toplevel").strip() == str(ROOT).encode()
    except subprocess.CalledProcessError:
        return False


pytestmark = pytest.mark.skipif(
    not _in_a_checkout(), reason="needs git and a checkout of the repository"
)


def test_git_lfs_takes_the_images():
    attributes = (ROOT / ".gitattributes").read_text()
    for pattern in IMAGES:
        assert f"{pattern} filter=lfs diff=lfs merge=lfs -text" in attributes


def test_every_image_is_stored_in_git_lfs():
    staged = _git("ls-files", "--stage", "-z", "--", *IMAGES).split(b"\0")
    entries = [entry for entry in staged if entry]
    assert entries, "no image found: the patterns no longer match anything"
    not_in_lfs = []
    for entry in entries:
        meta, path = entry.split(b"\t", 1)
        blob = meta.split()[1].decode()
        if not POINTER.match(_git("cat-file", "-p", blob)):
            not_in_lfs.append(path.decode())
    assert not not_in_lfs, (
        "stored as ordinary files, not in Git LFS (install git-lfs, run "
        "'git lfs install', then 'git rm --cached' and 'git add' them again): "
        + ", ".join(not_in_lfs)
    )

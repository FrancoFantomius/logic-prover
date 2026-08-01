"""Utility script to remove all __pycache__ directories recursively."""

import os
import shutil
import sys
from pathlib import Path


def clean_pycache(start_dir: Path | str | None = None) -> list[Path]:
    """Recursively search for and delete all __pycache__ directories.

    Args:
        start_dir: Path to start searching from. Defaults to the project root directory.

    Returns:
        List of Path objects representing deleted __pycache__ directories.
    """
    if start_dir is None:
        # Default to project root (two levels up from solver/utils)
        start_dir = Path(__file__).resolve().parent.parent.parent
    else:
        start_dir = Path(start_dir).resolve()

    deleted_dirs: list[Path] = []

    if not start_dir.exists():
        print(f"Directory '{start_dir}' does not exist.", file=sys.stderr)
        return deleted_dirs

    # Walk directory tree bottom-up so nested caches are removed cleanly
    for root, dirs, _files in os.walk(start_dir, topdown=False):
        for d in dirs:
            if d == "__pycache__":
                pycache_path = Path(root) / d
                try:
                    shutil.rmtree(pycache_path)
                    deleted_dirs.append(pycache_path)
                    print(f"Removed: {pycache_path}")
                except Exception as e:
                    print(f"Failed to remove {pycache_path}: {e}", file=sys.stderr)

    return deleted_dirs


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    removed = clean_pycache(target)
    print(f"\nTotal __pycache__ directories removed: {len(removed)}")

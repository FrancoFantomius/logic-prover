"""Utility script to remove all gitignored files and directories."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _parse_gitignore_patterns(gitignore_path: Path) -> list[str]:
    """Parse patterns from a .gitignore file."""
    patterns = []
    if not gitignore_path.is_file():
        return patterns

    with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def clean_gitignore(
    start_dir: Path | str | None = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> list[Path]:
    """Recursively search for and delete all gitignored files and directories.

    Uses `git clean` when git is available, otherwise falls back to parsing
    the project's `.gitignore` file.

    Args:
        start_dir: Path to start searching from. Defaults to project root.
        dry_run: If True, list items that would be removed without deleting them.
        verbose: If True, print output for each removed item.

    Returns:
        List of Path objects representing deleted (or targeted) files/directories.
    """
    if start_dir is None:
        # Default to project root (two levels up from utils/clean.py)
        start_dir = Path(__file__).resolve().parent.parent
    else:
        start_dir = Path(start_dir).resolve()

    if not start_dir.exists():
        if verbose:
            print(f"Directory '{start_dir}' does not exist.", file=sys.stderr)
        return []

    removed_items: list[Path] = []

    # Check if git is installed and start_dir is in a git repository
    git_bin = shutil.which("git")
    is_git_repo = False
    if git_bin:
        try:
            res = subprocess.run(
                [git_bin, "rev-parse", "--is-inside-work-tree"],
                cwd=start_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            is_git_repo = res.returncode == 0 and res.stdout.strip() == "true"
        except Exception:
            is_git_repo = False

    if is_git_repo and git_bin:
        # Use git clean -Xdf -n to get dry run output
        cmd_dry = [git_bin, "clean", "-Xdf", "-n"]
        try:
            res = subprocess.run(
                cmd_dry,
                cwd=start_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            lines = res.stdout.splitlines()
            for line in lines:
                # Output pattern: "Would remove path/to/file"
                if line.startswith("Would remove "):
                    rel_path = line[len("Would remove ") :].strip()
                    target_path = start_dir / rel_path
                    removed_items.append(target_path)

            if not dry_run and removed_items:
                cmd_clean = [git_bin, "clean", "-Xdf"]
                subprocess.run(
                    cmd_clean,
                    cwd=start_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )

            if verbose:
                prefix = "Would remove: " if dry_run else "Removed: "
                for item in removed_items:
                    print(f"{prefix}{item}")

            return removed_items
        except subprocess.SubprocessError as e:
            if verbose:
                print(f"Git clean failed, falling back to manual clean: {e}", file=sys.stderr)

    # Fallback method: parse .gitignore and scan directory
    gitignore_path = start_dir / ".gitignore"
    patterns = _parse_gitignore_patterns(gitignore_path)

    # Default fallback patterns if .gitignore is missing
    default_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".coverage",
        "build",
        "dist",
        "*.egg-info",
        "*.db",
        "*.filter.json",
        "node_modules",
    ]
    for p in default_patterns:
        if p not in patterns:
            patterns.append(p)

    import fnmatch

    for root, dirs, files in os.walk(start_dir, topdown=False):
        root_path = Path(root)
        # Check files
        for f in files:
            file_path = root_path / f
            rel_str = str(file_path.relative_to(start_dir)).replace("\\", "/")
            if any(fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(rel_str, pat) for pat in patterns):
                removed_items.append(file_path)
                if not dry_run:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        if verbose:
                            print(f"Failed to remove {file_path}: {e}", file=sys.stderr)
                if verbose:
                    print(f"{'Would remove: ' if dry_run else 'Removed: '}{file_path}")

        # Check dirs
        for d in dirs:
            dir_path = root_path / d
            rel_str = str(dir_path.relative_to(start_dir)).replace("\\", "/")
            if any(fnmatch.fnmatch(d, pat) or fnmatch.fnmatch(rel_str, pat) for pat in patterns):
                removed_items.append(dir_path)
                if not dry_run:
                    try:
                        shutil.rmtree(dir_path)
                    except Exception as e:
                        if verbose:
                            print(f"Failed to remove {dir_path}: {e}", file=sys.stderr)
                if verbose:
                    print(f"{'Would remove: ' if dry_run else 'Removed: '}{dir_path}")

    return removed_items


clean_ignored = clean_gitignore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Utility to clean all gitignored files and directories."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target directory to clean (defaults to project root).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Perform a dry run without deleting files.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress verbose output.",
    )

    args = parser.parse_args()
    target_path = Path(args.target) if args.target else None
    removed = clean_gitignore(
        start_dir=target_path,
        dry_run=args.dry_run,
        verbose=not args.quiet,
    )
    if not args.quiet:
        action = "would be removed" if args.dry_run else "removed"
        print(f"\nTotal gitignored items {action}: {len(removed)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
github_sorter.py — Sort local folders into GitHub repositories.

Features:
  - Prompts you to name each folder (or skip it)
  - Creates the GitHub repo if it doesn't exist
  - Pushes to the existing repo if it does
  - Dry-run mode: previews all actions without doing anything
  - Recursive mode: walks subfolders too
"""

import os
import sys
import subprocess
import argparse
import requests

# ─── Config ────────────────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"


# ─── GitHub helpers ─────────────────────────────────────────────────────────────

def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_username(token: str) -> str:
    resp = requests.get(f"{GITHUB_API}/user", headers=get_headers(token))
    resp.raise_for_status()
    return resp.json()["login"]


def repo_exists(token: str, username: str, repo_name: str) -> bool:
    resp = requests.get(
        f"{GITHUB_API}/repos/{username}/{repo_name}",
        headers=get_headers(token),
    )
    return resp.status_code == 200


def create_repo(token: str, repo_name: str, private: bool = False, dry_run: bool = False) -> str:
    """Creates a GitHub repo and returns its clone URL."""
    if dry_run:
        print(f"    [dry-run] Would create GitHub repo: {repo_name!r} (private={private})")
        return f"https://github.com/YOU/{repo_name}.git"

    payload = {"name": repo_name, "private": private, "auto_init": False}
    resp = requests.post(f"{GITHUB_API}/user/repos", json=payload, headers=get_headers(token))
    resp.raise_for_status()
    return resp.json()["clone_url"]


def get_clone_url(token: str, username: str, repo_name: str) -> str:
    resp = requests.get(
        f"{GITHUB_API}/repos/{username}/{repo_name}",
        headers=get_headers(token),
    )
    resp.raise_for_status()
    return resp.json()["clone_url"]


# ─── Git helpers ────────────────────────────────────────────────────────────────

def run_git(args: list[str], cwd: str, dry_run: bool = False) -> bool:
    cmd = ["git"] + args
    if dry_run:
        print(f"    [dry-run] {' '.join(cmd)}  (in {cwd})")
        return True
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ✗ git error: {result.stderr.strip()}")
        return False
    return True


def is_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, ".git"))


def push_folder(folder_path: str, remote_url: str, dry_run: bool = False) -> None:
    """Initialises (if needed), commits everything, and pushes to remote_url."""
    if not is_git_repo(folder_path):
        run_git(["init", "-b", "main"], cwd=folder_path, dry_run=dry_run)

    # Set / update remote
    remotes_result = subprocess.run(
        ["git", "remote"], cwd=folder_path, capture_output=True, text=True
    )
    existing_remotes = remotes_result.stdout.split()

    if "origin" in existing_remotes:
        run_git(["remote", "set-url", "origin", remote_url], cwd=folder_path, dry_run=dry_run)
    else:
        run_git(["remote", "add", "origin", remote_url], cwd=folder_path, dry_run=dry_run)

    run_git(["add", "-A"], cwd=folder_path, dry_run=dry_run)

    # Only commit if there's something staged
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=folder_path, capture_output=True, text=True
    )
    if status.stdout.strip() or dry_run:
        run_git(
            ["commit", "-m", "chore: sync via github_sorter"],
            cwd=folder_path,
            dry_run=dry_run,
        )
    else:
        print("    (nothing new to commit)")

    run_git(["push", "-u", "origin", "main", "--force"], cwd=folder_path, dry_run=dry_run)


# ─── Folder discovery ───────────────────────────────────────────────────────────

def collect_folders(root: str, recursive: bool) -> list[str]:
    """Return a sorted list of folder paths to process."""
    folders = []
    if recursive:
        for dirpath, dirnames, _ in os.walk(root):
            # Skip hidden dirs and .git internals
            dirnames[:] = [d for d in sorted(dirnames) if not d.startswith(".")]
            for d in dirnames:
                folders.append(os.path.join(dirpath, d))
    else:
        for name in sorted(os.listdir(root)):
            full = os.path.join(root, name)
            if os.path.isdir(full) and not name.startswith("."):
                folders.append(full)
    return folders


# ─── Interactive prompt ─────────────────────────────────────────────────────────

def prompt_repo_name(folder_path: str) -> str | None:
    """Ask the user what repo name to use, or skip."""
    default = os.path.basename(folder_path)
    print(f"\n📁  {folder_path}")
    answer = input(
        f"    Repo name [default: {default!r}] (leave blank to accept, 's' to skip): "
    ).strip()

    if answer.lower() == "s":
        return None
    return answer if answer else default


# ─── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sort local folders into GitHub repositories."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root directory whose sub-folders you want to push (default: current dir)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview all actions without making any changes",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Walk subfolders recursively instead of only top-level folders",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create new repos as private (default: public)",
    )

    args = parser.parse_args()

    if not args.token:
        print("✗  No GitHub token found. Pass --token or set GITHUB_TOKEN.", file=sys.stderr)
        sys.exit(1)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"✗  {root!r} is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}github_sorter starting…")
    print(f"Root      : {root}")
    print(f"Recursive : {args.recursive}")
    print(f"Private   : {args.private}")

    # Authenticate
    try:
        username = get_username(args.token)
        print(f"GitHub    : @{username}\n")
    except Exception as e:
        print(f"✗  Failed to authenticate with GitHub: {e}", file=sys.stderr)
        sys.exit(1)

    folders = collect_folders(root, recursive=args.recursive)
    if not folders:
        print("No folders found. Exiting.")
        return

    print(f"Found {len(folders)} folder(s) to process.")
    results = {"pushed": [], "skipped": [], "failed": []}

    for folder in folders:
        repo_name = prompt_repo_name(folder)
        if repo_name is None:
            print("    ↩  Skipped.")
            results["skipped"].append(folder)
            continue

        try:
            exists = repo_exists(args.token, username, repo_name)
            if exists:
                print(f"    ✓ Repo '{repo_name}' already exists — pushing to it.")
                remote_url = get_clone_url(args.token, username, repo_name)
            else:
                print(f"    + Repo '{repo_name}' not found — creating it.")
                remote_url = create_repo(
                    args.token, repo_name, private=args.private, dry_run=args.dry_run
                )

            push_folder(folder, remote_url, dry_run=args.dry_run)
            print(f"    ✓ Done → {remote_url}")
            results["pushed"].append(folder)

        except Exception as e:
            print(f"    ✗ Error: {e}")
            results["failed"].append(folder)

    # Summary
    print("\n─── Summary ───────────────────────────────────────")
    print(f"  Pushed  : {len(results['pushed'])}")
    print(f"  Skipped : {len(results['skipped'])}")
    print(f"  Failed  : {len(results['failed'])}")
    if results["failed"]:
        print("\n  Failed folders:")
        for f in results["failed"]:
            print(f"    • {f}")
    print()


if __name__ == "__main__":
    main()
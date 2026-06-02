#!/usr/bin/env python3
"""
github_sorter — Bulk-push local folders to GitHub repositories.
"""

import os
import sys
import subprocess
import argparse

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box

console = Console()

__version__ = "1.0.0"

GITHUB_API = "https://api.github.com"


# ─── GitHub helpers ──────────────────────────────────────────────────────────────

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
        console.print(f"  [dim][dry-run] Would create GitHub repo: [bold]{repo_name!r}[/bold] (private={private})[/dim]")
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


# ─── Git helpers ─────────────────────────────────────────────────────────────────

def run_git(args: list[str], cwd: str, dry_run: bool = False) -> bool:
    cmd = ["git"] + args
    if dry_run:
        console.print(f"  [dim][dry-run] {' '.join(cmd)}[/dim]")
        return True
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"  [red]✗ git error:[/red] {result.stderr.strip()}")
        return False
    return True


def is_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, ".git"))


def push_folder(
    folder_path: str,
    remote_url: str,
    dry_run: bool = False,
    message: str = "chore: sync via github_sorter",
) -> None:
    """Initialises (if needed), commits everything, and force-pushes to remote_url."""
    if not is_git_repo(folder_path):
        run_git(["init", "-b", "main"], cwd=folder_path, dry_run=dry_run)

    remotes_result = subprocess.run(
        ["git", "remote"], cwd=folder_path, capture_output=True, text=True
    )
    existing_remotes = remotes_result.stdout.split()

    if "origin" in existing_remotes:
        run_git(["remote", "set-url", "origin", remote_url], cwd=folder_path, dry_run=dry_run)
    else:
        run_git(["remote", "add", "origin", remote_url], cwd=folder_path, dry_run=dry_run)

    run_git(["add", "-A"], cwd=folder_path, dry_run=dry_run)

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=folder_path, capture_output=True, text=True
    )
    if status.stdout.strip() or dry_run:
        run_git(["commit", "-m", message], cwd=folder_path, dry_run=dry_run)
    else:
        console.print("  [dim](nothing new to commit)[/dim]")

    run_git(["push", "-u", "origin", "main", "--force"], cwd=folder_path, dry_run=dry_run)


# ─── Folder discovery ────────────────────────────────────────────────────────────

def collect_folders(root: str, recursive: bool) -> list[str]:
    """Return a sorted list of folder paths to process."""
    folders = []
    if recursive:
        for dirpath, dirnames, _ in os.walk(root):
            dirnames[:] = [d for d in sorted(dirnames) if not d.startswith(".")]
            for d in dirnames:
                folders.append(os.path.join(dirpath, d))
    else:
        for name in sorted(os.listdir(root)):
            full = os.path.join(root, name)
            if os.path.isdir(full) and not name.startswith("."):
                folders.append(full)
    return folders


# ─── Interactive prompt ──────────────────────────────────────────────────────────

def prompt_repo_name(folder_path: str, auto_accept: bool = False) -> str | None:
    """Ask the user what repo name to use, or skip. Returns None to skip."""
    default = os.path.basename(folder_path)
    console.print(f"\n[bold cyan]📁  {folder_path}[/bold cyan]")
    if auto_accept:
        console.print(f"  [dim]Auto-accepting default name: [bold]{default!r}[/bold][/dim]")
        return default
    answer = Prompt.ask(
        f"  [dim]Repo name \\[default [bold]{default!r}[/bold], blank=accept, [bold]s[/bold]=skip][/dim]",
        default="",
        show_default=False,
    ).strip()
    if answer.lower() == "s":
        return None
    return answer if answer else default


# ─── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="github_sorter",
        description="Bulk-push local folders to GitHub repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  github_sorter                                  process current directory
  github_sorter ~/projects --token ghp_…         specify directory and token
  github_sorter ~/projects --dry-run             preview without making changes
  github_sorter ~/projects --recursive           walk all subfolders
  github_sorter ~/projects --yes --private       non-interactive, private repos
  github_sorter ~/projects -m "initial commit"   custom commit message
        """,
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview all actions without making any changes",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="walk subfolders recursively instead of only top-level folders",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="create new repos as private (default: public)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="auto-accept default repo names, skipping all interactive prompts",
    )
    parser.add_argument(
        "--message", "-m",
        default="chore: sync via github_sorter",
        metavar="MSG",
        help="git commit message (default: 'chore: sync via github_sorter')",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"github_sorter {__version__}",
    )

    args = parser.parse_args()

    # ── Banner ────────────────────────────────────────────────────────────────
    mode = "[yellow bold]DRY-RUN[/yellow bold]" if args.dry_run else "[green bold]LIVE[/green bold]"
    console.print(Panel.fit(
        f"[bold white]github_sorter[/bold white] [dim]v{__version__}[/dim]  ·  {mode}",
        border_style="bright_blue",
        padding=(0, 2),
    ))

    # ── Token check ──────────────────────────────────────────────────────────
    if not args.token:
        console.print(
            "\n[red]✗[/red]  No GitHub token found.\n"
            "    Pass [bold]--token ghp_...[/bold] or set the [bold]GITHUB_TOKEN[/bold] env var.\n"
            "    Get a token at: https://github.com/settings/tokens"
        )
        sys.exit(1)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        console.print(f"\n[red]✗[/red]  [bold]{root!r}[/bold] is not a directory.")
        sys.exit(1)

    # ── Authenticate ─────────────────────────────────────────────────────────
    try:
        username = get_username(args.token)
    except Exception as e:
        console.print(f"\n[red]✗[/red]  Failed to authenticate with GitHub: {e}")
        sys.exit(1)

    console.print(f"\n  Root      : [cyan]{root}[/cyan]")
    console.print(f"  GitHub    : [green]@{username}[/green]")
    console.print(f"  Recursive : {'[green]yes[/green]' if args.recursive else 'no'}")
    console.print(f"  Private   : {'[yellow]yes[/yellow]' if args.private else 'no'}")
    console.print(f"  Auto-yes  : {'[green]yes[/green]' if args.yes else 'no'}")

    # ── Discover folders ─────────────────────────────────────────────────────
    folders = collect_folders(root, recursive=args.recursive)
    if not folders:
        console.print("\n[yellow]No folders found in the specified directory.[/yellow] Exiting.")
        return

    console.print(f"\n[bold]Found {len(folders)} folder(s) to process.[/bold]")
    results: dict[str, list[str]] = {"pushed": [], "skipped": [], "failed": []}

    # ── Process each folder ──────────────────────────────────────────────────
    for folder in folders:
        repo_name = prompt_repo_name(folder, auto_accept=args.yes)
        if repo_name is None:
            console.print("  [yellow]↩  Skipped.[/yellow]")
            results["skipped"].append(folder)
            continue

        try:
            exists = repo_exists(args.token, username, repo_name)
            if exists:
                console.print(f"  [green]✓[/green] Repo [bold]{repo_name!r}[/bold] already exists — pushing to it.")
                remote_url = get_clone_url(args.token, username, repo_name)
            else:
                console.print(f"  [blue]+[/blue] Repo [bold]{repo_name!r}[/bold] not found — creating it.")
                remote_url = create_repo(
                    args.token, repo_name, private=args.private, dry_run=args.dry_run
                )

            push_folder(folder, remote_url, dry_run=args.dry_run, message=args.message)
            console.print(f"  [green]✓ Done[/green] → {remote_url}")
            results["pushed"].append(folder)

        except Exception as e:
            console.print(f"  [red]✗ Error:[/red] {e}")
            results["failed"].append(folder)

    # ── Summary ───────────────────────────────────────────────────────────────
    table = Table(
        title="Summary",
        box=box.ROUNDED,
        border_style="bright_blue",
        show_header=False,
        padding=(0, 2),
    )
    table.add_column("Result", style="bold")
    table.add_column("Count", justify="right", style="bold")
    table.add_row("[green]Pushed[/green]", str(len(results["pushed"])))
    table.add_row("[yellow]Skipped[/yellow]", str(len(results["skipped"])))
    table.add_row("[red]Failed[/red]", str(len(results["failed"])))
    console.print()
    console.print(table)

    if results["failed"]:
        console.print("\n[red bold]Failed folders:[/red bold]")
        for f in results["failed"]:
            console.print(f"  • {f}")

    console.print()


if __name__ == "__main__":
    main()

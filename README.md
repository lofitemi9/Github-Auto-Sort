# github_sorter 🗂️→🐙

Sort local root folders into GitHub repositories — interactively, with dry-run support.

## Features

- **Interactive prompts** — name each repo yourself, or skip folders you don't want
- **Create or push** — creates a new GitHub repo if it doesn't exist, pushes to the existing one if it does
- **Dry-run mode** — preview every action before anything actually happens
- **Recursive mode** — walk subfolders too, not just top-level directories

---

## Setup

```bash
pip install -r requirements.txt
```

You'll also need a **GitHub Personal Access Token** with the `repo` scope:  
→ https://github.com/settings/tokens

---

## Usage

```bash
# Basic — process top-level folders in current directory
GITHUB_TOKEN=ghp_xxx python github_sorter.py

# Specify a root directory
python github_sorter.py ~/projects --token ghp_xxx

# Dry-run: preview what would happen, no changes made
python github_sorter.py ~/projects --dry-run

# Recursive: walk all subfolders
python github_sorter.py ~/projects --recursive

# Create repos as private
python github_sorter.py ~/projects --private

# Combine flags
python github_sorter.py ~/projects --recursive --dry-run --private
```

---

## Interactive session example

```
📁  /home/you/projects/my-app
    Repo name [default: 'my-app'] (leave blank to accept, 's' to skip): 
    + Repo 'my-app' not found — creating it.
    ✓ Done → https://github.com/you/my-app.git

📁  /home/you/projects/old-stuff
    Repo name [default: 'old-stuff'] (leave blank to accept, 's' to skip): s
    ↩  Skipped.

📁  /home/you/projects/website
    Repo name [default: 'website'] (leave blank to accept, 's' to skip): my-portfolio
    ✓ Repo 'my-portfolio' already exists — pushing to it.
    ✓ Done → https://github.com/you/my-portfolio.git

─── Summary ───────────────────────────────────────
  Pushed  : 2
  Skipped : 1
  Failed  : 0
```

---

## Options

| Flag | Description |
|------|-------------|
| `root` | Root directory to scan (default: `.`) |
| `--token` | GitHub PAT (or use `GITHUB_TOKEN` env var) |
| `--dry-run` | Preview actions without making changes |
| `--recursive` | Walk subfolders recursively |
| `--private` | Create new repos as private |

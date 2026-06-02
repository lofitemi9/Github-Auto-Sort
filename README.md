<div align="center">

# github-sorter

**Bulk-push local folders to GitHub repositories — interactively, with a beautiful terminal UI.**

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/lofitemi9/-/pulls)

</div>

---

Got a folder full of projects that aren't on GitHub yet? `github-sorter` walks through them one by one, lets you name each repo, and pushes everything up — no manual `git init`, `git remote add`, or `gh repo create` needed.

```
╭─────────────────────────────────────╮
│  github_sorter  v1.0.0  ·  LIVE     │
╰─────────────────────────────────────╯

  Root      : /home/you/projects
  GitHub    : @you
  Recursive : no
  Private   : no
  Auto-yes  : no

Found 3 folder(s) to process.

📁  /home/you/projects/my-app
  Repo name [default 'my-app', blank=accept, s=skip]:
  + Repo 'my-app' not found — creating it.
  ✓ Done → https://github.com/you/my-app.git

📁  /home/you/projects/old-stuff
  Repo name [default 'old-stuff', blank=accept, s=skip]: s
  ↩  Skipped.

📁  /home/you/projects/website
  Repo name [default 'website', blank=accept, s=skip]: my-portfolio
  ✓ Repo 'my-portfolio' already exists — pushing to it.
  ✓ Done → https://github.com/you/my-portfolio.git

╭─ Summary ──╮
│ Pushed   2 │
│ Skipped  1 │
│ Failed   0 │
╰────────────╯
```

---

## Features

- **Interactive prompts** — name each repo yourself, or type `s` to skip folders you don't want
- **Smart create or push** — creates a new GitHub repo if it doesn't exist, pushes to the existing one if it does
- **Dry-run mode** — preview every action before anything actually happens on GitHub
- **Recursive mode** — walk subfolders too, not just top-level directories
- **Non-interactive mode** — `--yes` flag to auto-accept all default names (great for scripting)
- **Custom commit messages** — `--message` flag to set your own commit message
- **Beautiful output** — colour-coded terminal UI with a clean summary table

---

## Requirements

- Python 3.10 or newer
- `git` installed and on your `PATH`
- A GitHub account with a Personal Access Token

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/lofitemi9/-.git
cd github-sorter
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a GitHub Personal Access Token

Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens** (or classic tokens) and create a token with the **`repo`** scope.

→ https://github.com/settings/tokens

### 4. Set your token

The easiest way is to export it as an environment variable so you don't have to type it every time:

```bash
# macOS / Linux
export GITHUB_TOKEN=ghp_your_token_here

# Windows (PowerShell)
$env:GITHUB_TOKEN = "ghp_your_token_here"

# Windows (Command Prompt)
set GITHUB_TOKEN=ghp_your_token_here
```

Or pass it directly via `--token` on each run.

---

## Usage

```bash
python github_sorter.py [root] [options]
```

### Basic examples

```bash
# Process all folders in the current directory
python github_sorter.py

# Process a specific directory
python github_sorter.py ~/projects

# Pass your token inline
python github_sorter.py ~/projects --token ghp_your_token_here

# Preview what would happen — no changes made
python github_sorter.py ~/projects --dry-run

# Walk all nested subfolders, not just the top level
python github_sorter.py ~/projects --recursive

# Create repos as private instead of public
python github_sorter.py ~/projects --private

# Skip all prompts and auto-accept default repo names
python github_sorter.py ~/projects --yes

# Use a custom git commit message
python github_sorter.py ~/projects --message "feat: initial commit"

# Combine flags — private, recursive, no prompts, dry-run
python github_sorter.py ~/projects --recursive --private --yes --dry-run
```

### CLI reference

| Argument | Description |
|----------|-------------|
| `root` | Root directory to scan (default: `.`) |
| `--token TOKEN` | GitHub Personal Access Token (or set `GITHUB_TOKEN`) |
| `--dry-run` | Preview all actions without making any changes |
| `--recursive` | Walk subfolders recursively |
| `--private` | Create new repos as private (default: public) |
| `--yes`, `-y` | Auto-accept default repo names, no prompts |
| `--message MSG`, `-m MSG` | Custom git commit message |
| `--version` | Show version and exit |

---

## How it works

For each folder discovered in the root directory, the tool:

1. Prompts you to confirm or change the repo name (or skip it entirely)
2. Checks whether that repo already exists on your GitHub account
3. Creates the repo if it doesn't exist (respecting `--private`)
4. Runs `git init` on the folder if it isn't already a git repo
5. Stages all files, commits with the configured message, and force-pushes to `origin/main`

Hidden directories (those starting with `.`) are always skipped.

---

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to open a [pull request](https://github.com/lofitemi9/-/pulls) or file an [issue](https://github.com/lofitemi9/-/issues).

1. Fork the repo
2. Create a branch: `git checkout -b feat/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push and open a PR

---

## License

Distributed under the [MIT License](LICENSE).

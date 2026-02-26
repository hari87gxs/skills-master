---
name: gitlab-visual-docs
description: Connect to a GitLab repository and generate a beautiful, self-contained HTML visual documentation page. Use when the user provides a GitLab repo URL or asks to document, visualize, or explain a GitLab project. Produces architecture diagrams, module breakdowns, dependency graphs, and a visual project overview — all in a single HTML file opened in the browser.
license: MIT
compatibility: Requires git and optionally glab CLI. GitLab personal access token recommended for private repos.
metadata:
  author: custom
  version: "1.0.0"
---

# GitLab Visual Docs

Generate a stunning, self-contained HTML visual documentation page for any GitLab repository. The output is a single `.html` file that opens in the browser — no build step, no dependencies, no server required.

---

## When to use me

- User pastes a GitLab repo URL (e.g. `https://gitlab.com/org/repo`)
- User says "document this repo", "visualize this project", "generate docs for..."
- User wants to understand an unfamiliar codebase visually
- User wants shareable, browser-viewable documentation

---

## Workflow

### Step 1 — Clone or access the repo

**Option A: Clone (recommended for full analysis)**
```bash
# Clone to a temp location (shallow clone for speed)
git clone --depth=1 <repo_url> /tmp/gitlab-visual-docs-repo
```

If the clone fails due to auth, prompt the user:
> "This looks like a private repo. Please provide a GitLab personal access token, or run: `glab auth login` first."

For private repos with a token:
```bash
# Embed token in URL
git clone --depth=1 https://oauth2:<TOKEN>@gitlab.com/org/repo /tmp/gitlab-visual-docs-repo
```

**Option B: Use glab CLI (if available)**
```bash
which glab && glab repo view <namespace/repo> --web
```

After cloning, set the working path:
```
REPO_PATH=/tmp/gitlab-visual-docs-repo
```

---

### Step 2 — Explore the repository structure

Run these commands to gather intelligence about the repo. Adapt based on what you find:

```bash
# Top-level structure
ls -la $REPO_PATH

# Directory tree (max 3 levels deep, skip node_modules/.git/vendor)
find $REPO_PATH -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/vendor/*' -not -path '*/__pycache__/*' | sort

# Detect language/stack
ls $REPO_PATH/*.json $REPO_PATH/*.toml $REPO_PATH/*.yaml $REPO_PATH/*.yml $REPO_PATH/Makefile $REPO_PATH/Dockerfile 2>/dev/null

# Count files by extension (top languages)
find $REPO_PATH -not -path '*/.git/*' -not -path '*/node_modules/*' -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -15

# Read key files (prioritize in this order)
# 1. README.md / README.rst / README
# 2. package.json / pyproject.toml / Cargo.toml / go.mod / pom.xml
# 3. Architecture docs: docs/, architecture/, design/
# 4. Entry points: main.*, index.*, app.*, server.*, cmd/
# 5. CI/CD: .gitlab-ci.yml, .github/workflows/
```

Read the following files if they exist (use the Read tool):
- `README.md` — project description, goals, usage
- `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` — dependencies, scripts
- `.gitlab-ci.yml` — pipeline stages
- `docker-compose.yml` / `Dockerfile` — deployment topology
- Any file named `ARCHITECTURE.md`, `DESIGN.md`, `CONTRIBUTING.md`

---

### Step 3 — Analyze and extract documentation intelligence

From your exploration, extract:

**Project Identity**
- Name, description, version, license
- Primary language(s) and framework(s)
- What problem it solves (from README)

**Architecture**
- Top-level modules/packages and their purpose
- Entry points (how the app starts)
- Key abstractions (classes, services, components)
- External dependencies (APIs, databases, message queues)

**Data Flow** (if discernible)
- How a request/event flows through the system
- Key transformations or processing stages

**CI/CD Pipeline** (if `.gitlab-ci.yml` exists)
- Stages (build → test → deploy)
- Environments (staging, production)

**Developer Onboarding**
- How to install/run locally
- Key commands (from Makefile, package.json scripts, README)
- Environment variables needed

---

### Step 4 — Design the visual documentation page

**Think before writing HTML.** Commit to an aesthetic and structure:

**Aesthetic options** (pick one, vary across uses):
- Editorial light — serif headlines, cream background, ink-on-paper feel
- Terminal dark — monospace everything, green/amber on near-black
- Blueprint — grid lines, technical drawing feel, deep navy
- IDE-inspired — borrow a real theme: Nord, Catppuccin, Dracula, Gruvbox
- Modern SaaS — gradient mesh, glassmorphism, bold gradients
- Minimal ink — maximum whitespace, one accent color, Swiss design

**Page sections** (include all that are relevant):

1. **Hero** — Project name, one-line description, language badges, key stats (stars, last commit)
2. **Architecture Overview** — Mermaid diagram showing main components and how they connect
3. **Module Breakdown** — Card grid: one card per top-level module/package with its purpose
4. **Data Flow** — Mermaid sequence or flowchart diagram showing how data moves
5. **Tech Stack** — Visual table of languages, frameworks, databases, tools
6. **CI/CD Pipeline** — Mermaid diagram of pipeline stages (if `.gitlab-ci.yml` exists)
7. **Getting Started** — Copy-pasteable commands to clone, install, run
8. **Key Files Map** — Annotated tree of the most important files and what they do
9. **Dependencies** — Top external dependencies with their purpose

**Diagram rules:**
- Use Mermaid for anything with connections (flowcharts, sequences, pipelines, architecture topology)
- Use CSS Grid cards for module breakdowns (text-heavy, no routing needed)
- Always use `theme: 'base'` with custom `themeVariables` matching your palette
- Always add zoom controls (+/−/reset) to every Mermaid diagram
- Never define `.node` as a page-level CSS class (conflicts with Mermaid internals)

---

### Step 5 — Generate the HTML

Write a single self-contained HTML file. Every style and script must be inline — no external files except CDN links (Google Fonts, Mermaid.js).

**Required structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{Project Name} — Visual Documentation</title>
  <!-- Google Fonts: pick a distinctive pairing, never Inter/Roboto/Arial -->
  <link href="https://fonts.googleapis.com/css2?family=...&display=swap" rel="stylesheet">
  <style>
    /* CSS custom properties for full palette */
    :root {
      --bg: ...;
      --surface: ...;
      --border: ...;
      --text: ...;
      --text-dim: ...;
      --accent-1: ...;
      --accent-2: ...;
      /* etc */
    }
    @media (prefers-color-scheme: dark) { :root { /* alternate theme */ } }
    /* All layout, components, animations inline here */
  </style>
</head>
<body>
  <!-- Semantic HTML: header, main, sections -->
  <!-- Mermaid diagrams where needed -->
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true, theme: 'base', themeVariables: { ... } });
  </script>
  <!-- Zoom controls script if Mermaid diagrams are present -->
</body>
</html>
```

**Typography rules:**
- Use a distinctive Google Font pairing: a display/heading font + a mono font for code labels
- Never use Inter, Roboto, Arial, or system-ui as the primary heading font
- Load via `<link>` with a system font fallback stack

**Animation:**
- Staggered fade-in on page load for cards and sections (guides the eye)
- Always include `prefers-reduced-motion` media query to disable animations

**Quality checks before writing the file:**
- The squint test: blur your eyes — can you see hierarchy?
- The swap test: would replacing your fonts/colors with generic dark make it identical to a template? If yes, push further.
- Both themes: light and dark must both look intentional
- No overflow: every grid/flex child has `min-width: 0`
- Information completeness: does it actually explain the repo?

---

### Step 6 — Write and open the file

**Output location:** `~/.agent/diagrams/`

**Filename:** use the repo name — e.g. `my-project-visual-docs.html`

```bash
# Write the file (use the Write tool)
# Then open it
open ~/.agent/diagrams/{repo-name}-visual-docs.html        # macOS
# xdg-open ~/.agent/diagrams/{repo-name}-visual-docs.html  # Linux
```

**Tell the user:**
> "Visual documentation generated at `~/.agent/diagrams/{repo-name}-visual-docs.html` — opening in browser now."

---

### Step 7 — Cleanup (optional)

If you cloned to `/tmp/gitlab-visual-docs-repo`, offer to clean up:
```bash
rm -rf /tmp/gitlab-visual-docs-repo
```

---

## Error handling

| Situation | Action |
|---|---|
| Private repo, no auth | Ask user for GitLab token or `glab auth login` |
| Repo not found (404) | Confirm the URL is correct and the repo is accessible |
| No README | Infer project purpose from file structure and package manifest |
| Minimal codebase | Still generate a page — focus on structure and getting-started |
| Very large repo | Use `--depth=1` and limit `find` depth to 3; don't read every file |
| Binary/non-code repo | Note what the repo contains and document its structure |

---

## Output quality standards

The generated page must be:
- **Self-contained** — single `.html` file, opens offline (except CDN fonts/Mermaid)
- **Visually distinct** — not a generic dark template; has a deliberate aesthetic identity
- **Accurate** — reflects the actual repo structure, not generic boilerplate
- **Complete** — covers all major aspects: architecture, stack, getting started, key files
- **Shareable** — can be sent to a teammate to understand the project in 5 minutes

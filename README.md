# Skills Master — AI Coding Assistant Skills Collection

> A curated collection of powerful **AI coding assistant skills** for VS Code (GitHub Copilot) and OpenCode that automate complex workflows and generate beautiful visual outputs.

---

## 🎯 Available Skills

### 1. **Jira Progress Skill** — VS Code Extension
**Type:** GitHub Copilot Skill (VS Code Extension)  
**Purpose:** Fetches live Jira sprint data and renders a rich visual productivity dashboard directly inside VS Code Chat

📁 [View Skill](./src/) | 📖 [Documentation](#jira-progress-skill)

### 2. **GitLab Visual Docs Skill** — OpenCode Skill
**Type:** OpenCode Skill  
**Purpose:** Connects to private GitLab repositories, analyzes dbt projects, and generates beautiful standalone HTML visual documentation with interactive dependency maps

📁 [View Skill](./gitlab-visual-docs/) | 📖 [Documentation](./gitlab-visual-docs/README.md)

---

## 🚀 Quick Start

### For Jira Progress Skill (VS Code)
```bash
git clone https://github.com/hari87gxs/skills-master.git
cd skills-master
npm install
npm run compile
# Press F5 in VS Code to launch
```

### For GitLab Visual Docs Skill (OpenCode)
```bash
git clone https://github.com/hari87gxs/skills-master.git
cp -r skills-master/gitlab-visual-docs ~/.config/opencode/skills/
# Restart OpenCode or reload skills
```

---

# Jira Progress Skill — VS Code Extension

> A **GitHub Copilot Skill** that fetches live Jira sprint data and renders a rich visual productivity dashboard directly inside VS Code Chat — just like the RGDENG Weekly Productivity report.

---

## 🧠 What is a Skill?

A **Skill** (officially: *Language Model Tool*) is a function you register with VS Code that Copilot can call automatically when it decides live data is needed. The flow is:

```
User asks @jira "show me this week's team progress"
          ↓
Copilot reads your tool's description and decides to call it
          ↓
Your skill fetches live data from the Jira REST API
          ↓
Copilot renders a rich visual report in Chat
```

**Three files that make a skill:**

| File | Role |
|---|---|
| `package.json` → `languageModelTools` | Declares the skill to VS Code |
| `src/tools/jiraProgressTool.ts` | The skill logic (`prepareInvocation` + `invoke`) |
| `src/extension.ts` | Wires everything up at startup |

---

## ⚙️ Setup

### 1. Install dependencies

```bash
cd jira-progress-skill
npm install
```

### 2. Compile TypeScript

```bash
npm run compile
# or watch mode during development:
npm run watch
```

### 3. Open in VS Code & launch

Press **F5** — this opens a new *Extension Development Host* window with your skill loaded.

### 4. Configure credentials

In the Extension Development Host window:
1. Open **Settings** (`⌘,`)
2. Search for `jiraProgressSkill`
3. Fill in:
   - **Email** — your Atlassian account email
   - **API Token** — from https://id.atlassian.com/manage-profile/security/api-tokens
   - **Default Base URL** — e.g. `https://mycompany.atlassian.net`
   - **Default Project Key** — e.g. `RGDENG`
   - **Default Board ID** — find this in your board's URL: `.../boards/42` → `42`

---

## 💬 Usage

Open **Copilot Chat** and type:

```
@jira show me the team progress for board 3059 at gxsbank.atlassian.net
```

```
@jira RGDENG board 42 productivity report from mycompany.atlassian.net
```

```
@jira which engineers are blocked on board 3059?
```

**The skill will:**
1. Extract the board ID, project key, and Jira URL from your message
2. Fetch all issues from that board (works with both Scrum and Kanban)
3. Generate a **beautiful standalone HTML dashboard** that opens automatically in your browser
4. Show a summary in chat with key metrics and blocked items

**The HTML dashboard includes:**
- 📊 Top-level stat cards (Total / Done / In Progress / To Do / Completion %)
- 📈 Visual progress bar
- 📝 Progress narrative cards by theme (Completions, Active Work, Blockers, Top Contributor)
- 🚨 Blocked & stalled items section with action items
- 👥 Per-engineer collapsible breakdown with all their issues

**Example messages:**
- "show progress for board 3059" — uses your default URL from settings
- "RGDENG board at gxsbank.atlassian.net" — extracts both
- "team productivity dashboard" — uses all defaults from settings

---

## ⚙️ Settings (Optional Defaults)

You can save defaults so you don't have to type the board/URL every time:

1. Open **Settings** (`⌘,`)
2. Search for `jiraProgressSkill`
3. Fill in:
   - **Email** & **API Token** (required for authentication)
   - **Default Base URL**, **Project Key**, **Board ID** (optional — used when not specified in your message)

---

## 🏗️ Project Structure

```
jira-progress-skill/
├── package.json              ← Extension manifest + skill declaration
├── tsconfig.json             ← TypeScript config
├── src/
│   ├── extension.ts          ← activate() — registers skill + chat participant
│   └── tools/
│       └── jiraProgressTool.ts  ← The skill: prepareInvocation + invoke
└── out/                      ← Compiled JS (generated by tsc)
```

---

## 🔑 Key Concepts Quick Reference

### Skill = LanguageModelTool

```typescript
// Declare in package.json:
"languageModelTools": [{ "name": "jira_team_progress", ... }]

// Implement in TypeScript:
class MyTool implements vscode.LanguageModelTool<MyInput> {
  prepareInvocation(options, token) { /* loading message */ }
  invoke(options, token) { /* fetch data, return result */ }
}

// Register in activate():
vscode.lm.registerTool("jira_team_progress", new MyTool())
```

### Chat Participant = @mention handler

```typescript
// Declare in package.json:
"chatParticipants": [{ "id": "...", "name": "jira" }]

// Implement in TypeScript:
vscode.chat.createChatParticipant("...", handleRequest)

// In the handler, give the LLM your tools:
model.sendRequest(messages, { tools: [...] }, token)
```

### Tool Result

```typescript
// Return text:
return new vscode.LanguageModelToolResult([
  new vscode.LanguageModelTextPart("# My Report\n\n...")
])
```

---

## 🔒 Security Note

Never commit your API token. Use VS Code Settings (stored in `settings.json`, excluded from source control) or VS Code's SecretStorage API for production extensions.

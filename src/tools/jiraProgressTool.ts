/**
 * jiraProgressTool.ts
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * SKILL CONCEPT EXPLAINED
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * A "Skill" (Language Model Tool) has two lifecycle methods:
 *
 *  1. prepareInvocation()  — Called BEFORE the tool runs.
 *                            Use it to show the user a confirmation message
 *                            like "Fetching sprint data from RGDENG board…"
 *
 *  2. invoke()             — The actual skill logic.
 *                            Receives typed input (projectKey, boardId, etc.)
 *                            Returns a LanguageModelToolResult — which can
 *                            contain Markdown text or a PromptElementPart.
 *
 * Copilot calls your skill automatically when it decides the user's question
 * needs live Jira data. You never hard-code when to call it — the model reads
 * your `modelDescription` in package.json and decides.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { buildHTMLDashboard } from "./htmlBuilder";

// ─── Types ───────────────────────────────────────────────────────────────────

/** The input shape for our skill — mirrors the inputSchema in package.json */
export interface JiraProgressInput {
  jiraBaseUrl: string;
  projectKey: string;
  boardId: number;
  sprintName?: string;
}

/** A single Jira issue as we care about it */
export interface JiraIssue {
  key: string;
  summary: string;
  status: string; // "Done" | "In Progress" | "To Do" | "Blocked" | etc.
  assignee: string | null;
  priority: string;
  labels: string[];
  storyPoints?: number;
  updatedAt: string;
}

/** Per-engineer aggregated data */
export interface EngineerSummary {
  name: string;
  done: JiraIssue[];
  inProgress: JiraIssue[];
  toDo: JiraIssue[];
  blocked: JiraIssue[];
}

// ─── Jira API Client ──────────────────────────────────────────────────────────

/**
 * Thin wrapper around the Jira REST API v3.
 * We use VS Code's built-in fetch (Node 18+) — no extra dependencies needed.
 */
class JiraClient {
  private authHeader: string;

  constructor(
    private baseUrl: string,
    email: string,
    apiToken: string
  ) {
    // Jira uses HTTP Basic Auth: base64(email:token)
    this.authHeader =
      "Basic " + Buffer.from(`${email}:${apiToken}`).toString("base64");
  }

  private async get<T>(path: string): Promise<T> {
    const url = `${this.baseUrl}/rest/agile/1.0${path}`;
    const res = await fetch(url, {
      headers: {
        Authorization: this.authHeader,
        Accept: "application/json",
      },
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Jira API error ${res.status} at ${path}: ${body}`);
    }
    return res.json() as Promise<T>;
  }

  /**
   * Detect whether this board is 'scrum' or 'kanban'.
   * This is the key branch point — kanban boards have no sprints.
   */
  async getBoardInfo(boardId: number): Promise<{ type: "scrum" | "kanban"; name: string }> {
    const data = await this.get<{ type: string; name: string }>(`/board/${boardId}`);
    return {
      type: (data.type?.toLowerCase() === "scrum" ? "scrum" : "kanban") as "scrum" | "kanban",
      name: data.name,
    };
  }

  /** Get the active sprint for a SCRUM board only */
  async getActiveSprint(
    boardId: number
  ): Promise<{ id: number; name: string; startDate: string; endDate: string }> {
    const data = await this.get<{ values: any[] }>(
      `/board/${boardId}/sprint?state=active`
    );
    if (!data.values.length) {
      throw new Error(`No active sprint found for board ${boardId}`);
    }
    return data.values[0];
  }

  /** Get all issues in a sprint (SCRUM boards only) */
  async getSprintIssues(
    boardId: number,
    sprintId: number
  ): Promise<JiraIssue[]> {
    const allIssues: JiraIssue[] = [];
    let startAt = 0;
    const maxResults = 100;

    // Jira paginates results — loop until we have everything
    while (true) {
      const data = await this.get<{ issues: any[]; total: number }>(
        `/board/${boardId}/sprint/${sprintId}/issue?startAt=${startAt}&maxResults=${maxResults}`
      );

      for (const raw of data.issues) {
        allIssues.push(parseIssue(raw));
      }

      startAt += maxResults;
      if (startAt >= data.total) break;
    }

    return allIssues;
  }

  /**
   * Get all issues from a KANBAN board.
   * Kanban has no sprints — issues flow through columns directly.
   * We fetch everything on the board so we can show all columns:
   * Blocked / Ready / In Progress / In Review / For Deployment / Closed.
   */
  async getBoardIssues(boardId: number): Promise<JiraIssue[]> {
    const allIssues: JiraIssue[] = [];
    let startAt = 0;
    const maxResults = 100;

    while (true) {
      const data = await this.get<{ issues: any[]; total: number }>(
        `/board/${boardId}/issue?startAt=${startAt}&maxResults=${maxResults}`
      );

      for (const raw of data.issues) {
        allIssues.push(parseIssue(raw));
      }

      startAt += maxResults;
      if (startAt >= data.total) break;
    }

    return allIssues;
  }
}

/** Shared issue parser used by both Scrum and Kanban fetch methods */
function parseIssue(raw: any): JiraIssue {
  return {
    key: raw.key,
    summary: raw.fields.summary,
    status: raw.fields.status.name,
    assignee: raw.fields.assignee?.displayName ?? null,
    priority: raw.fields.priority?.name ?? "Medium",
    labels: raw.fields.labels ?? [],
    storyPoints:
      raw.fields.story_points ?? raw.fields.customfield_10016 ?? undefined,
    updatedAt: raw.fields.updated,
  };
}

// ─── Data Processing ──────────────────────────────────────────────────────────

function categoriseStatus(status: string): "done" | "inProgress" | "toDo" | "blocked" {
  const s = status.toLowerCase();
  // Terminal / done states
  if (s === "done" || s === "closed" || s === "resolved") return "done";
  // Formally blocked
  if (s.includes("block")) return "blocked";
  // Active work — includes Kanban columns: In Progress, In Review/Testing, For Deployment
  if (
    s.includes("progress") ||
    s.includes("review") ||
    s.includes("testing") ||
    s.includes("deployment") ||
    s.includes("deploy")
  ) return "inProgress";
  // Everything else: To Do, Backlog, Ready for Development, etc.
  return "toDo";
}

function groupByEngineer(issues: JiraIssue[]): Map<string, EngineerSummary> {
  const map = new Map<string, EngineerSummary>();

  const getOrCreate = (name: string): EngineerSummary => {
    if (!map.has(name)) {
      map.set(name, { name, done: [], inProgress: [], toDo: [], blocked: [] });
    }
    return map.get(name)!;
  };

  for (const issue of issues) {
    const name = issue.assignee ?? "Unassigned";
    const eng = getOrCreate(name);
    const cat = categoriseStatus(issue.status);
    eng[cat].push(issue);
  }

  return map;
}

// ─── Visual Report Builder ────────────────────────────────────────────────────

/**
 * CONCEPT: Skills return LanguageModelToolResult which can contain:
 *   - vscode.LanguageModelTextPart  → plain text / Markdown
 *   - An HTML string embedded in Markdown via a code fence
 *
 * Here we build a rich Markdown report. The @jira chat participant will also
 * render this as a VS Code Webview (HTML) for a richer visual.
 */
function buildMarkdownReport(
  projectKey: string,
  boardInfo: { type: "scrum" | "kanban"; name: string },
  sprint: { name: string; startDate: string; endDate: string } | null,
  issues: JiraIssue[],
  weekOf: string
): string {
  const total = issues.length;
  const done = issues.filter((i) => categoriseStatus(i.status) === "done");
  const inProgress = issues.filter(
    (i) => categoriseStatus(i.status) === "inProgress"
  );
  const toDo = issues.filter((i) => categoriseStatus(i.status) === "toDo");
  const blocked = issues.filter(
    (i) => categoriseStatus(i.status) === "blocked"
  );
  const completionRate =
    total > 0 ? Math.round((done.length / total) * 100) : 0;

  const engineers = groupByEngineer(issues);
  const activeEngineers = [...engineers.values()].filter(
    (e) => e.name !== "Unassigned"
  );

  // ── Stat bar ──────────────────────────────────────────────────────────────
  const boardLabel = sprint
    ? `**Sprint:** ${sprint.name}`
    : `**Board:** ${boardInfo.name} _(Kanban)_`;
  const statBar = `
## 📊 ${projectKey} Weekly Productivity
${boardLabel} · **Week of:** ${weekOf} · **${activeEngineers.length} engineers active** · **${total} issues active**

| 🔢 Total | ✅ Completed | 🔄 In Progress | 📋 To Do / Backlog | 👷 Engineers | 📈 Completion |
|---|---|---|---|---|---|
| **${total}** | **${done.length}** | **${inProgress.length}** | **${toDo.length}** | **${activeEngineers.length}** | **${completionRate}%** |

---
`;

  // ── Progress bar (text-based) ─────────────────────────────────────────────
  const barWidth = 40;
  const doneBlocks = Math.round((done.length / total) * barWidth);
  const inProgBlocks = Math.round((inProgress.length / total) * barWidth);
  const todoBlocks = barWidth - doneBlocks - inProgBlocks;
  const progressBar =
    "█".repeat(doneBlocks) +
    "▓".repeat(inProgBlocks) +
    "░".repeat(Math.max(0, todoBlocks));

  const progressSection = `
### ${sprint ? "Sprint" : "Board"} Progress
\`\`\`
${progressBar}  ${completionRate}%
✅ Done       ${"■".repeat(Math.min(doneBlocks, 20))} ${done.length}
🔄 In Progress ${"■".repeat(Math.min(inProgBlocks, 20))} ${inProgress.length}  
📋 To Do      ${"■".repeat(Math.min(todoBlocks, 20))} ${toDo.length}
\`\`\`
`;

  // ── Progress Narratives ───────────────────────────────────────────────────
  let narratives = "\n### 📝 Progress Narratives — Key Themes\n\n";

  // Group engineers into themed sections (completions, blockers, infra)
  const completers = activeEngineers.filter((e) => e.done.length >= 2);
  const blockedEngineers = activeEngineers.filter((e) => e.blocked.length > 0);
  const heavyInProgress = activeEngineers.filter(
    (e) => e.done.length === 0 && e.inProgress.length > 0
  );

  if (completers.length > 0) {
    narratives += `#### ✅ Completions This Sprint\n`;
    for (const eng of completers) {
      const topIssues = eng.done
        .slice(0, 3)
        .map((i) => `\`${i.key}\` ${i.summary}`)
        .join(", ");
      narratives += `- **${eng.name}** closed **${eng.done.length} issues** including ${topIssues}`;
      if (eng.inProgress.length > 0) {
        narratives += ` — still actively working ${eng.inProgress.length} in-progress items.`;
      }
      narratives += "\n";
    }
    narratives += "\n";
  }

  if (heavyInProgress.length > 0) {
    narratives += `#### 🔄 Active In-Progress Work\n`;
    for (const eng of heavyInProgress) {
      const items = eng.inProgress
        .slice(0, 3)
        .map((i) => `\`${i.key}\` ${i.summary}`)
        .join(", ");
      narratives += `- **${eng.name}** is driving ${items}\n`;
    }
    narratives += "\n";
  }

  // ── Blocked items ─────────────────────────────────────────────────────────
  let blockedSection = "";
  const allBlocked = issues.filter((i) => categoriseStatus(i.status) === "blocked");

  // Also flag long-running in-progress (updated > 7 days ago)
  const staleInProgress = issues.filter((i) => {
    if (categoriseStatus(i.status) !== "inProgress") return false;
    const updatedDaysAgo =
      (Date.now() - new Date(i.updatedAt).getTime()) / (1000 * 60 * 60 * 24);
    return updatedDaysAgo > 7;
  });

  if (allBlocked.length > 0 || staleInProgress.length > 0) {
    blockedSection = `\n### 🚨 Blocked Items — Action Needed\n\n`;
    if (allBlocked.length > 0) {
      blockedSection += `**Formally Blocked:**\n`;
      for (const issue of allBlocked) {
        blockedSection += `- **${issue.assignee ?? "Unassigned"}**'s \`${issue.key}\` — ${issue.summary}\n`;
      }
    }
    if (staleInProgress.length > 0) {
      blockedSection += `\n**⚠️ Stalled In-Progress (no update > 7 days):**\n`;
      for (const issue of staleInProgress) {
        const days = Math.round(
          (Date.now() - new Date(issue.updatedAt).getTime()) /
            (1000 * 60 * 60 * 24)
        );
        blockedSection += `- **${issue.assignee ?? "Unassigned"}**'s \`${issue.key}\` — ${issue.summary} _(${days} days stale)_\n`;
      }
    }
  }

  // ── Per-engineer detail ───────────────────────────────────────────────────
  let engineerDetail = "\n### 👥 Per-Engineer Breakdown\n\n";
  for (const eng of activeEngineers.sort(
    (a, b) => b.done.length - a.done.length
  )) {
    const total = eng.done.length + eng.inProgress.length + eng.toDo.length + eng.blocked.length;
    const pct = total > 0 ? Math.round((eng.done.length / total) * 100) : 0;
    engineerDetail += `<details>\n<summary><strong>${eng.name}</strong> — ✅ ${eng.done.length} done · 🔄 ${eng.inProgress.length} in progress · 📋 ${eng.toDo.length} to do · ${pct}% complete</summary>\n\n`;

    if (eng.inProgress.length > 0) {
      engineerDetail += `**In Progress:**\n`;
      eng.inProgress.forEach(
        (i) => (engineerDetail += `- \`${i.key}\` ${i.summary}\n`)
      );
    }
    if (eng.done.length > 0) {
      engineerDetail += `\n**Completed:**\n`;
      eng.done
        .slice(0, 5)
        .forEach((i) => (engineerDetail += `- \`${i.key}\` ${i.summary}\n`));
    }
    engineerDetail += `\n</details>\n\n`;
  }

  return statBar + progressSection + narratives + blockedSection + engineerDetail;
}

// ─── The Skill Class ──────────────────────────────────────────────────────────

/**
 * CONCEPT: This class IS the skill.
 *
 * It implements `vscode.LanguageModelTool<JiraProgressInput>`:
 *   • prepareInvocation() → shown to user before running (like a loading message)
 *   • invoke()            → the real work; returns the report
 *
 * VS Code + Copilot call these for you. You just register the class and the
 * platform handles everything else.
 */
export class JiraProgressTool
  implements vscode.LanguageModelTool<JiraProgressInput>
{
  // ── prepareInvocation ─────────────────────────────────────────────────────
  /**
   * Called before invoke(). Return a confirmationMessages object to show
   * a confirmation prompt, or just a loading message. Return undefined to
   * skip and invoke immediately.
   */
  async prepareInvocation(
    options: vscode.LanguageModelToolInvocationPrepareOptions<JiraProgressInput>,
    _token: vscode.CancellationToken
  ): Promise<vscode.PreparedToolInvocation> {
    const { projectKey, boardId, sprintName } = options.input;
    return {
      invocationMessage: `Fetching board data from ${projectKey} (board ${boardId})…`,
    };
  }

  // ── invoke ────────────────────────────────────────────────────────────────
  /**
   * The skill runs here. Steps:
   *   1. Read credentials from VS Code settings
   *   2. Create the Jira client
   *   3. Fetch the active sprint + all issues
   *   4. Build the visual Markdown report
   *   5. Return as LanguageModelToolResult
   */
  async invoke(
    options: vscode.LanguageModelToolInvocationOptions<JiraProgressInput>,
    token: vscode.CancellationToken
  ): Promise<vscode.LanguageModelToolResult> {
    const { jiraBaseUrl, projectKey, boardId, sprintName } = options.input;

    // ── Read credentials from VS Code settings ──────────────────────────────
    const config = vscode.workspace.getConfiguration("jiraProgressSkill");
    const email = config.get<string>("email") ?? "";
    const apiToken = config.get<string>("apiToken") ?? "";

    if (!email || !apiToken) {
      return new vscode.LanguageModelToolResult([
        new vscode.LanguageModelTextPart(
          "⚠️ **Setup required**: Please set your Jira credentials in VS Code Settings.\n\n" +
          "1. Open **Settings** (`⌘,`)\n" +
          "2. Search for `jiraProgressSkill`\n" +
          "3. Fill in your **email** and **API token**\n\n" +
          "Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens"
        ),
      ]);
    }

    // ── Cancelled? ──────────────────────────────────────────────────────────
    if (token.isCancellationRequested) {
      return new vscode.LanguageModelToolResult([
        new vscode.LanguageModelTextPart("Request cancelled."),
      ]);
    }

    try {
      const client = new JiraClient(jiraBaseUrl, email, apiToken);

      // Step 1: detect board type — this is the key fork between Scrum and Kanban
      const boardInfo = await client.getBoardInfo(boardId);

      if (token.isCancellationRequested) {
        return new vscode.LanguageModelToolResult([
          new vscode.LanguageModelTextPart("Request cancelled."),
        ]);
      }

      let issues: JiraIssue[];
      let sprint: { id: number; name: string; startDate: string; endDate: string } | null = null;

      if (boardInfo.type === "scrum") {
        // Scrum: issues are scoped to the active sprint
        sprint = await client.getActiveSprint(boardId);
        issues = await client.getSprintIssues(boardId, sprint.id);
      } else {
        // Kanban: no sprints — issues flow through columns on the board itself
        issues = await client.getBoardIssues(boardId);
      }

      // Build the week-of string (Monday of current week)
      const weekOf = getMonday(new Date()).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });

      // Build the Markdown report for chat
      const markdownReport = buildMarkdownReport(projectKey, boardInfo, sprint, issues, weekOf);

      // Build the beautiful HTML dashboard
      const engineers = groupByEngineer(issues);
      const activeEngineers = [...engineers.values()].filter(e => e.name !== "Unassigned");
      const html = buildHTMLDashboard(projectKey, boardInfo, sprint, issues, weekOf, engineers);

      // Calculate summary stats for the chat message
      const done = issues.filter(i => categoriseStatus(i.status) === "done");
      const inProgress = issues.filter(i => categoriseStatus(i.status) === "inProgress");
      const toDo = issues.filter(i => categoriseStatus(i.status) === "toDo");
      const completionRate = issues.length > 0 ? Math.round((done.length / issues.length) * 100) : 0;

      // Save to workspace or home directory for persistence
      const workspaceFolders = vscode.workspace.workspaceFolders;
      let saveDir: string;
      
      if (workspaceFolders && workspaceFolders.length > 0) {
        // Save to workspace folder in a "jira-reports" subdirectory
        saveDir = path.join(workspaceFolders[0].uri.fsPath, 'jira-reports');
      } else {
        // No workspace open — save to ~/Documents/jira-reports
        const homeDir = os.homedir();
        saveDir = path.join(homeDir, 'Documents', 'jira-reports');
      }

      // Create the directory if it doesn't exist
      if (!fs.existsSync(saveDir)) {
        fs.mkdirSync(saveDir, { recursive: true });
      }

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const fileName = `${projectKey}-board-${boardId}-${timestamp}.html`;
      const filePath = path.join(saveDir, fileName);
      
      // Write the file
      fs.writeFileSync(filePath, html, 'utf-8');

      // Open in browser
      vscode.env.openExternal(vscode.Uri.file(filePath));

      // Return summary + link to the HTML file
      return new vscode.LanguageModelToolResult([
        new vscode.LanguageModelTextPart(
          `✅ **Dashboard generated!** Opening in your browser...\n\n` +
          `📊 **Summary:**\n` +
          `- **${issues.length} total issues** (${done.length} done, ${inProgress.length} in progress, ${toDo.length} to do)\n` +
          `- **${completionRate}% completion rate**\n` +
          `- **${activeEngineers.length} engineers** actively working\n\n` +
          `💾 **Saved to:** \`${filePath}\`\n` +
          `📂 **Folder:** [Open Reports Folder](${vscode.Uri.file(saveDir).toString()})\n\n` +
          `You can now share this HTML file with your team!\n\n` +
          `---\n\n` +
          markdownReport
        ),
      ]);
    } catch (err: any) {
      return new vscode.LanguageModelToolResult([
        new vscode.LanguageModelTextPart(
          `❌ Error fetching Jira data: ${err.message}\n\n` +
          `**Tip:** Double-check your base URL (${jiraBaseUrl}), board ID (${boardId}), and API token in settings.`
        ),
      ]);
    }
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getMonday(d: Date): Date {
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // adjust for Sunday
  return new Date(d.setDate(diff));
}

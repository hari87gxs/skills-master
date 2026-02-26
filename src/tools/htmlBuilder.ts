/**
 * htmlBuilder.ts — Beautiful HTML dashboard generator
 * 
 * Builds a standalone HTML page matching the RGDENG Weekly Productivity style:
 * - Dark theme with gradient cards
 * - Top stat bar with 6 metrics
 * - Progress narratives with colored borders (blue/green/red/purple)
 * - Blocked items section
 * - Per-engineer collapsible cards
 */

import type { JiraIssue, EngineerSummary } from './jiraProgressTool';

interface BoardInfo {
  type: "scrum" | "kanban";
  name: string;
}

interface SprintInfo {
  name: string;
  startDate: string;
  endDate: string;
}

export function buildHTMLDashboard(
  projectKey: string,
  boardInfo: BoardInfo,
  sprint: SprintInfo | null,
  issues: JiraIssue[],
  weekOf: string,
  engineers: Map<string, EngineerSummary>
): string {
  const total = issues.length;
  const done = issues.filter(i => categoriseStatus(i.status) === "done");
  const inProgress = issues.filter(i => categoriseStatus(i.status) === "inProgress");
  const toDo = issues.filter(i => categoriseStatus(i.status) === "toDo");
  const blocked = issues.filter(i => categoriseStatus(i.status) === "blocked");
  const completionRate = total > 0 ? Math.round((done.length / total) * 100) : 0;

  const activeEngineers = [...engineers.values()].filter(e => e.name !== "Unassigned");

  const boardLabel = sprint ? sprint.name : `${boardInfo.name} (Kanban)`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${projectKey} Weekly Productivity</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
      color: #e8eaed;
      padding: 40px 20px;
      min-height: 100vh;
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
    }

    header {
      margin-bottom: 40px;
    }

    h1 {
      font-size: 2.5rem;
      font-weight: 700;
      background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 10px;
    }

    .meta {
      color: #9aa0a6;
      font-size: 0.95rem;
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }

    .meta span { display: inline-flex; align-items: center; gap: 8px; }

    /* Stat Cards */
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 20px;
      margin-bottom: 40px;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 24px;
      border-top: 3px solid;
      position: relative;
      overflow: hidden;
    }

    .stat-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
      opacity: 0;
      transition: opacity 0.3s;
    }

    .stat-card:hover::before { opacity: 1; }

    .stat-card.blue { border-top-color: #4fc3f7; }
    .stat-card.green { border-top-color: #66bb6a; }
    .stat-card.orange { border-top-color: #ffa726; }
    .stat-card.yellow { border-top-color: #ffee58; }
    .stat-card.purple { border-top-color: #ab47bc; }
    .stat-card.red { border-top-color: #ef5350; }

    .stat-value {
      font-size: 3rem;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 8px;
    }

    .stat-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #9aa0a6;
      font-weight: 600;
    }

    /* Progress Narratives */
    .narratives {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
      gap: 20px;
      margin-bottom: 40px;
    }

    .narrative-card {
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      padding: 24px;
      border-left: 4px solid;
    }

    .narrative-card.blue { border-left-color: #4fc3f7; }
    .narrative-card.green { border-left-color: #66bb6a; }
    .narrative-card.red { border-left-color: #ef5350; }
    .narrative-card.purple { border-left-color: #ab47bc; }

    .narrative-card h3 {
      font-size: 1.1rem;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .narrative-card p {
      line-height: 1.6;
      color: #bdc1c6;
      margin-bottom: 12px;
      font-size: 0.95rem;
    }

    .narrative-card strong {
      color: #e8eaed;
      font-weight: 600;
    }

    .tag {
      display: inline-block;
      background: rgba(79, 195, 247, 0.2);
      color: #4fc3f7;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 0.8rem;
      font-weight: 600;
      margin: 4px 4px 4px 0;
    }

    /* Blocked Section */
    .blocked-section {
      background: rgba(239, 83, 80, 0.1);
      border: 1px solid rgba(239, 83, 80, 0.3);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 40px;
    }

    .blocked-section h2 {
      color: #ef5350;
      font-size: 1.3rem;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .blocked-section ul {
      list-style: none;
    }

    .blocked-section li {
      padding: 12px;
      background: rgba(0, 0, 0, 0.2);
      margin-bottom: 8px;
      border-radius: 8px;
      border-left: 3px solid #ef5350;
    }

    .blocked-section code {
      background: rgba(255, 255, 255, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.9rem;
      color: #ffa726;
    }

    /* Engineer Cards */
    .engineers {
      display: grid;
      gap: 16px;
    }

    .engineer-card {
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .engineer-header {
      padding: 20px 24px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.02);
      transition: background 0.2s;
    }

    .engineer-header:hover {
      background: rgba(255, 255, 255, 0.05);
    }

    .engineer-name {
      font-size: 1.1rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .engineer-stats {
      display: flex;
      gap: 16px;
      font-size: 0.9rem;
      color: #9aa0a6;
    }

    .engineer-stats span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .engineer-body {
      padding: 0 24px 24px;
      display: none;
    }

    .engineer-card.open .engineer-body {
      display: block;
    }

    .issue-list {
      list-style: none;
      margin-top: 12px;
    }

    .issue-list li {
      padding: 10px;
      background: rgba(0, 0, 0, 0.2);
      margin-bottom: 6px;
      border-radius: 6px;
      font-size: 0.9rem;
    }

    .issue-list code {
      background: rgba(79, 195, 247, 0.2);
      color: #4fc3f7;
      padding: 2px 6px;
      border-radius: 4px;
      margin-right: 8px;
      font-weight: 600;
    }

    .section-title {
      font-size: 1.5rem;
      margin: 40px 0 20px;
      font-weight: 600;
    }

    .progress-bar {
      height: 24px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      overflow: hidden;
      margin: 20px 0;
      display: flex;
    }

    .progress-segment {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 600;
      transition: all 0.3s;
    }

    .progress-segment:hover { opacity: 0.8; }

    .progress-segment.done { background: #66bb6a; }
    .progress-segment.in-progress { background: #4fc3f7; }
    .progress-segment.todo { background: rgba(255, 255, 255, 0.1); color: #9aa0a6; }

    @media (max-width: 768px) {
      .stats { grid-template-columns: repeat(2, 1fr); }
      .narratives { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>${projectKey} Weekly Productivity</h1>
      <div class="meta">
        <span><strong>${boardLabel}</strong></span>
        <span>Week of ${weekOf}</span>
        <span>${activeEngineers.length} engineers active</span>
        <span>${total} issues active</span>
      </div>
    </header>

    <!-- Stats -->
    <div class="stats">
      <div class="stat-card blue">
        <div class="stat-value">${total}</div>
        <div class="stat-label">Total Issues Active</div>
      </div>
      <div class="stat-card green">
        <div class="stat-value">${done.length}</div>
        <div class="stat-label">Completed (Done)</div>
      </div>
      <div class="stat-card orange">
        <div class="stat-value">${inProgress.length}</div>
        <div class="stat-label">In Progress</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-value">${toDo.length}</div>
        <div class="stat-label">To Do / Backlog</div>
      </div>
      <div class="stat-card purple">
        <div class="stat-value">${activeEngineers.length}</div>
        <div class="stat-label">Engineers Active</div>
      </div>
      <div class="stat-card ${completionRate >= 50 ? 'green' : 'red'}">
        <div class="stat-value">${completionRate}%</div>
        <div class="stat-label">Completion Rate</div>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="progress-bar">
      ${done.length > 0 ? `<div class="progress-segment done" style="width: ${(done.length / total) * 100}%">${done.length} Done</div>` : ''}
      ${inProgress.length > 0 ? `<div class="progress-segment in-progress" style="width: ${(inProgress.length / total) * 100}%">${inProgress.length} In Progress</div>` : ''}
      ${toDo.length > 0 ? `<div class="progress-segment todo" style="width: ${(toDo.length / total) * 100}%">${toDo.length} To Do</div>` : ''}
    </div>

    ${buildNarratives(activeEngineers, issues)}

    ${buildBlockedSection(issues)}

    <h2 class="section-title">👥 Per-Engineer Breakdown</h2>
    <div class="engineers">
      ${buildEngineerCards(activeEngineers)}
    </div>
  </div>

  <script>
    document.querySelectorAll('.engineer-header').forEach(header => {
      header.addEventListener('click', () => {
        header.parentElement.classList.toggle('open');
      });
    });
  </script>
</body>
</html>`;
}

function buildNarratives(engineers: EngineerSummary[], issues: JiraIssue[]): string {
  const completers = engineers.filter(e => e.done.length >= 2);
  const heavyInProgress = engineers.filter(e => e.done.length === 0 && e.inProgress.length > 0);
  const blockedEngineers = engineers.filter(e => e.blocked.length > 0);

  let html = '<h2 class="section-title">📝 Progress Narratives — Key Themes</h2><div class="narratives">';

  if (completers.length > 0) {
    html += `<div class="narrative-card green">
      <h3>✅ Completions This Period</h3>`;
    for (const eng of completers.slice(0, 3)) {
      const topIssues = eng.done.slice(0, 2).map(i => `<code>${i.key}</code> ${i.summary}`).join(', ');
      html += `<p><strong>${eng.name}</strong> closed <strong>${eng.done.length} issues</strong> including ${topIssues}`;
      if (eng.inProgress.length > 0) {
        html += ` — still actively working ${eng.inProgress.length} in-progress items.`;
      }
      html += '</p>';
    }
    html += '</div>';
  }

  if (heavyInProgress.length > 0) {
    html += `<div class="narrative-card blue">
      <h3>🔄 Active In-Progress Work</h3>`;
    for (const eng of heavyInProgress.slice(0, 3)) {
      const items = eng.inProgress.slice(0, 2).map(i => `<code>${i.key}</code> ${i.summary}`).join(', ');
      html += `<p><strong>${eng.name}</strong> is driving ${items}</p>`;
    }
    html += '</div>';
  }

  if (blockedEngineers.length > 0) {
    html += `<div class="narrative-card red">
      <h3>🚨 Blocked Items Need Attention</h3>`;
    for (const eng of blockedEngineers) {
      html += `<p><strong>${eng.name}</strong> has <strong>${eng.blocked.length} blocked</strong> ${eng.blocked.length === 1 ? 'item' : 'items'}</p>`;
    }
    html += '</div>';
  }

  // Find top contributor
  const topContributor = [...engineers].sort((a, b) => b.done.length - a.done.length)[0];
  if (topContributor && topContributor.done.length >= 3) {
    html += `<div class="narrative-card purple">
      <h3>🏆 Top Contributor</h3>
      <p><strong>${topContributor.name}</strong> leads with <strong>${topContributor.done.length} completions</strong> this period, demonstrating strong momentum.</p>
    </div>`;
  }

  html += '</div>';
  return html;
}

function buildBlockedSection(issues: JiraIssue[]): string {
  const blocked = issues.filter(i => categoriseStatus(i.status) === "blocked");
  const stale = issues.filter(i => {
    if (categoriseStatus(i.status) !== "inProgress") return false;
    const daysAgo = (Date.now() - new Date(i.updatedAt).getTime()) / (1000 * 60 * 60 * 24);
    return daysAgo > 7;
  });

  if (blocked.length === 0 && stale.length === 0) return '';

  let html = '<div class="blocked-section"><h2>🚨 Blocked Items — Action Needed</h2><ul>';

  if (blocked.length > 0) {
    html += '<li><strong>Formally Blocked:</strong><ul style="margin-top: 8px; margin-left: 20px;">';
    blocked.forEach(i => {
      html += `<li><strong>${i.assignee ?? 'Unassigned'}</strong> — <code>${i.key}</code> ${i.summary}</li>`;
    });
    html += '</ul></li>';
  }

  if (stale.length > 0) {
    html += '<li><strong>⚠️ Stalled In-Progress (no update &gt; 7 days):</strong><ul style="margin-top: 8px; margin-left: 20px;">';
    stale.forEach(i => {
      const days = Math.round((Date.now() - new Date(i.updatedAt).getTime()) / (1000 * 60 * 60 * 24));
      html += `<li><strong>${i.assignee ?? 'Unassigned'}</strong> — <code>${i.key}</code> ${i.summary} <em>(${days} days stale)</em></li>`;
    });
    html += '</ul></li>';
  }

  html += '</ul></div>';
  return html;
}

function buildEngineerCards(engineers: EngineerSummary[]): string {
  const sorted = [...engineers].sort((a, b) => b.done.length - a.done.length);
  
  return sorted.map(eng => {
    const total = eng.done.length + eng.inProgress.length + eng.toDo.length + eng.blocked.length;
    const pct = total > 0 ? Math.round((eng.done.length / total) * 100) : 0;

    return `<div class="engineer-card">
      <div class="engineer-header">
        <div class="engineer-name">${eng.name}</div>
        <div class="engineer-stats">
          <span>✅ ${eng.done.length}</span>
          <span>🔄 ${eng.inProgress.length}</span>
          <span>📋 ${eng.toDo.length}</span>
          <span>${pct}% complete</span>
        </div>
      </div>
      <div class="engineer-body">
        ${eng.inProgress.length > 0 ? `
          <h4 style="margin-top: 16px; margin-bottom: 8px; color: #4fc3f7;">In Progress</h4>
          <ul class="issue-list">
            ${eng.inProgress.map(i => `<li><code>${i.key}</code>${i.summary}</li>`).join('')}
          </ul>
        ` : ''}
        ${eng.done.length > 0 ? `
          <h4 style="margin-top: 16px; margin-bottom: 8px; color: #66bb6a;">Completed</h4>
          <ul class="issue-list">
            ${eng.done.slice(0, 5).map(i => `<li><code>${i.key}</code>${i.summary}</li>`).join('')}
          </ul>
        ` : ''}
      </div>
    </div>`;
  }).join('');
}

function categoriseStatus(status: string): "done" | "inProgress" | "toDo" | "blocked" {
  const s = status.toLowerCase();
  if (s === "done" || s === "closed" || s === "resolved") return "done";
  if (s.includes("block")) return "blocked";
  if (
    s.includes("progress") ||
    s.includes("review") ||
    s.includes("testing") ||
    s.includes("deployment") ||
    s.includes("deploy")
  ) return "inProgress";
  return "toDo";
}

/**
 * extension.ts  —  VS Code Extension Entry Point
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * CONCEPT: Extension Lifecycle
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *  activate()   → Called once when VS Code loads your extension
 *                 (triggered by activationEvents in package.json)
 *                 This is where you register all your skills and participants.
 *
 *  deactivate() → Called when the extension is disabled/uninstalled.
 *                 Clean up resources here.
 *
 * The context.subscriptions array is key: anything you push there gets
 * automatically disposed when the extension is deactivated.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import * as vscode from "vscode";
import { JiraProgressTool } from "./tools/jiraProgressTool";

// ─────────────────────────────────────────────────────────────────────────────
// activate()
// ─────────────────────────────────────────────────────────────────────────────
export function activate(context: vscode.ExtensionContext) {
  console.log("Jira Progress Skill is now active");

  // ── STEP 1: Register the Skill (Language Model Tool) ─────────────────────
  //
  // CONCEPT: vscode.lm.registerTool() is the core API.
  //   - First arg: the tool name — MUST match the "name" in package.json
  //                languageModelTools contribution point
  //   - Second arg: an instance of your LanguageModelTool class
  //
  // Once registered, Copilot can see this tool and call it automatically
  // when it decides live Jira data would help answer the user's question.
  //
  context.subscriptions.push(
    vscode.lm.registerTool("jira_team_progress", new JiraProgressTool())
  );

  // ── STEP 2: Register the @jira Chat Participant ───────────────────────────
  //
  // CONCEPT: A Chat Participant is the @mention handler in Copilot Chat.
  //   - When the user types "@jira show me the team progress", this runs.
  //   - It can directly call the tool, or let the model decide.
  //   - The participant acts as an intelligent router + UI layer.
  //
  const participant = vscode.chat.createChatParticipant(
    "jira-progress-skill.dashboard",
    handleChatRequest
  );

  // Give the participant a friendly icon in chat
  participant.iconPath = new vscode.ThemeIcon("graph");

  context.subscriptions.push(participant);

  // ── STEP 3: Register the setup command ───────────────────────────────────
  //
  // A convenience command to open Settings pre-filtered to our extension
  //
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "jiraProgressSkill.openSettings",
      () => {
        vscode.commands.executeCommand(
          "workbench.action.openSettings",
          "jiraProgressSkill"
        );
      }
    )
  );

  // Welcome message on first activation
  vscode.window.showInformationMessage(
    "Jira Progress Skill activated! Type @jira in Copilot Chat to get started.",
    "Open Settings",
    "Open Chat"
  ).then((choice) => {
    if (choice === "Open Settings") {
      vscode.commands.executeCommand("jiraProgressSkill.openSettings");
    } else if (choice === "Open Chat") {
      vscode.commands.executeCommand("workbench.panel.chat.view.copilot.focus");
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Chat Participant Handler
// ─────────────────────────────────────────────────────────────────────────────
//
// CONCEPT: This function handles every message the user sends to @jira.
//   - `request.prompt` is what the user typed
//   - `stream` lets you stream responses back in real time (like ChatGPT)
//   - We pass our tool to the language model so it can call it automatically
//
async function handleChatRequest(
  request: vscode.ChatRequest,
  context: vscode.ChatContext,
  stream: vscode.ChatResponseStream,
  token: vscode.CancellationToken
): Promise<void> {
  // Read defaults from settings so the user doesn't have to type them every time
  const config = vscode.workspace.getConfiguration("jiraProgressSkill");
  const defaultBaseUrl = config.get<string>("defaultBaseUrl") ?? "";
  const defaultProjectKey = config.get<string>("defaultProjectKey") ?? "";
  const defaultBoardId = config.get<number>("defaultBoardId") ?? 0;

  const hasDefaults = defaultBaseUrl && defaultProjectKey && defaultBoardId;

  // ── Guard: no credentials configured ────────────────────────────────────
  const email = config.get<string>("email") ?? "";
  const apiToken = config.get<string>("apiToken") ?? "";

  if (!email || !apiToken) {
    stream.markdown(
      "⚠️ **Setup required before we can fetch your Jira data!**\n\n" +
      "Please configure your credentials:\n" +
      "1. Run the command **Jira Progress Skill: Open Settings** (`⌘⇧P`)\n" +
      "2. Set your **email** and **API token**\n\n" +
      "_Get your API token from:_ https://id.atlassian.com/manage-profile/security/api-tokens"
    );
    stream.button({
      command: "jiraProgressSkill.openSettings",
      title: "$(gear) Open Settings",
    });
    return;
  }

  // ── Build the system prompt ───────────────────────────────────────────────
  //
  // CONCEPT: We craft a system prompt that tells the model:
  //   a) what tools are available
  //   b) what context we already know (defaults from settings)
  //   c) how to respond
  //
  const systemPrompt = vscode.LanguageModelChatMessage.User(
    `You are a Jira productivity analyst integrated into VS Code.
You have access to the tool \`jira_team_progress\` which fetches live board data and generates a beautiful HTML dashboard.

**IMPORTANT:** Always extract Jira parameters from the user's message:
  - If the user mentions a board ID (e.g., "board 3059"), use it as boardId
  - If the user mentions a URL or domain (e.g., "gxsbank.atlassian.net" or "abc.com"), construct jiraBaseUrl as "https://<domain>"
  - If the user mentions a project key (e.g., "RGDENG"), use it as projectKey
  - Parse natural language: "show progress for RGDENG board 3059 at gxsbank.atlassian.net" → {projectKey: "RGDENG", boardId: 3059, jiraBaseUrl: "https://gxsbank.atlassian.net"}

${hasDefaults
  ? `The user has saved defaults in settings (use these ONLY if the user doesn't provide specific values):
   - Base URL: ${defaultBaseUrl}
   - Project: ${defaultProjectKey}  
   - Board ID: ${defaultBoardId}`
  : "The user hasn't saved defaults. You MUST extract all three parameters (jiraBaseUrl, projectKey, boardId) from their message. If any are missing, ask the user for them before calling the tool."
}

When the user asks for a team report, sprint status, or productivity dashboard:
1. Extract jiraBaseUrl, projectKey, and boardId from their message (or use defaults if not specified)
2. Call the jira_team_progress tool with those parameters
3. The tool will generate an HTML dashboard and open it in the browser automatically
4. Summarize the key metrics in chat (total issues, completion rate, blockers)
5. Highlight any blocked items or stalled work that needs attention`
  );

  const userMessage = vscode.LanguageModelChatMessage.User(request.prompt);

  try {
    // ── Select the language model ────────────────────────────────────────────
    //
    // CONCEPT: vscode.lm.selectChatModels() finds available LLMs.
    //   We ask for a "copilot" family model (GPT-4o or similar).
    //   The user's active Copilot subscription determines what's available.
    //
    const [model] = await vscode.lm.selectChatModels({
      vendor: "copilot",
      family: "gpt-4o",
    });

    if (!model) {
      stream.markdown(
        "❌ No language model available. Please make sure GitHub Copilot is installed and signed in."
      );
      return;
    }

    // ── Get all registered tools that match our skill ────────────────────────
    //
    // CONCEPT: vscode.lm.tools contains ALL registered tools across all extensions.
    //   We filter to just our jira_team_progress tool and pass it to the model.
    //   The model will decide when to call it based on the conversation.
    //
    const tools = vscode.lm.tools.filter(
      (t) => t.name === "jira_team_progress"
    );

    // ── Send the request to the LLM ──────────────────────────────────────────
    const response = await model.sendRequest(
      [systemPrompt, userMessage],
      {
        tools: tools.map((t) => ({
          name: t.name,
          description: t.description,
          inputSchema: t.inputSchema,
        })),
      },
      token
    );

    // ── Stream the response back to the user ─────────────────────────────────
    //
    // CONCEPT: The model's response is a stream. It can contain:
    //   - LanguageModelTextPart: regular text to show the user
    //   - LanguageModelToolCallPart: a request to invoke one of your tools
    //
    // When we see a tool call, we invoke it ourselves and feed the result
    // back to the model in a follow-up message.
    //
    for await (const chunk of response.stream) {
      if (chunk instanceof vscode.LanguageModelTextPart) {
        // Regular text — stream it directly to the chat window
        stream.markdown(chunk.value);
      } else if (chunk instanceof vscode.LanguageModelToolCallPart) {
        // The model wants to call our tool!
        // Show a progress indicator while fetching
        stream.progress(`Fetching Jira data from board ${(chunk.input as any).boardId ?? ""}…`);

        try {
          // ── Invoke the tool ──────────────────────────────────────────────
          //
          // CONCEPT: vscode.lm.invokeTool() runs your tool's invoke() method.
          //   - toolInvocationToken comes from the request context
          //   - input is the typed parameters the model generated
          //
          const toolResult = await vscode.lm.invokeTool(
            chunk.name,
            {
              toolInvocationToken: request.toolInvocationToken,
              input: chunk.input,
            },
            token
          );

          // The tool result contains our Markdown report — stream it out
          for (const part of toolResult.content) {
            if (part instanceof vscode.LanguageModelTextPart) {
              stream.markdown(part.value);
            }
          }
        } catch (toolErr: any) {
          stream.markdown(`\n❌ Tool error: ${toolErr.message}`);
        }
      }
    }
  } catch (err: any) {
    if (err?.code === vscode.LanguageModelError.NotFound().code) {
      stream.markdown("❌ Language model not found. Please check your Copilot subscription.");
    } else {
      stream.markdown(`❌ Unexpected error: ${err.message}`);
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// deactivate()
// ─────────────────────────────────────────────────────────────────────────────
export function deactivate() {
  // VS Code automatically disposes everything in context.subscriptions
  // Nothing extra needed here for this extension
}

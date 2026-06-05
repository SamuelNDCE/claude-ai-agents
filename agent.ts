// agent.ts — Vercel AI SDK + Composio

import { anthropic } from "@ai-sdk/anthropic";
import { Composio } from "@composio/core";
import { VercelProvider } from "@composio/vercel";
import { stepCountIs, streamText } from "ai";

// API key is read from the environment (.env), never hardcoded.
// Composio also auto-reads COMPOSIO_API_KEY; passing it explicitly is clearer.
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY;
if (!COMPOSIO_API_KEY) {
  throw new Error(
    "COMPOSIO_API_KEY is not set. Add it to your .env file (see .env.example)."
  );
}

const composio = new Composio({
  apiKey: COMPOSIO_API_KEY,
  provider: new VercelProvider(),
});
const userId = "user_ym8ng9";

// Create a tool router session
const session = await composio.create(userId);
const tools = await session.tools();

const stream = await streamText({
  model: anthropic("claude-sonnet-4-6"), // verified: current latest Sonnet (Claude Sonnet 4.6)
  prompt: "Star the composiohq/composio repo on GitHub",
  stopWhen: stepCountIs(10),
  tools,
});

for await (const textPart of stream.textStream) {
  process.stdout.write(textPart);
}

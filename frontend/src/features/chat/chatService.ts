// src/features/chat/chatService.ts
// Calls FastAPI RAG: POST /api/rag/ask and returns ONLY the natural text in `answer.summary`.

import { api } from "@/lib/api";
import type { ChatMessage, ChatRequest } from "./types";

export interface ChatAdapter {
  ask(req: ChatRequest): Promise<string>;
}

/** Last user message text (no findLast needed) */
function lastUserText(messages: ChatMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.role === "user" && typeof m.content === "string") {
      return m.content.trim();
    }
  }
  return "";
}

type RagAskResponse = {
  answer?:
    | string
    | {
        summary?: string;
        text?: string;
        // other fields like rows/count may exist but we ignore them
        [k: string]: unknown;
      };
  citations?: unknown;
  meta?: unknown;
};

export class RestAdapter implements ChatAdapter {
  async ask(req: ChatRequest): Promise<string> {
    const question = lastUserText(req.messages);
    if (!question) throw new Error("Please type a question.");

    try {
      // Correct path under /api
      const res = await api.post<RagAskResponse>("/api/rag/ask", { question });
      const data = res.data ?? {};

      // ✅ Show ONLY the natural-language summary
      const ans = data.answer as any;

      if (ans && typeof ans === "object" && typeof ans.summary === "string") {
        return ans.summary; // exact summary from backend
      }

      // sensible fallbacks if summary isn't present
      if (typeof data.answer === "string") return data.answer;
      if (ans && typeof ans.text === "string") return ans.text;

      return "No summary was returned for this question.";
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ??
        err?.message ??
        "Chat API error";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
  }
}

/** Mock adapter (optional offline dev) */
export class MockAdapter implements ChatAdapter {
  async ask(req: ChatRequest): Promise<string> {
    const q = lastUserText(req.messages);
    await new Promise((r) => setTimeout(r, 300));
    return `Mock summary for: ${q}`;
  }
}

export function createChatAdapter(): ChatAdapter {
  const useMock = import.meta.env.VITE_CHAT_USE_MOCK === "1";
  return useMock ? new MockAdapter() : new RestAdapter();
}

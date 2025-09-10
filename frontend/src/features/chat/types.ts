export type ChatRole = "user" | "assistant" | "system" | "tool";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt?: string;
};

export type ChatRequest = {
  messages: ChatMessage[];
  sessionId?: string;
  stream?: boolean;
};

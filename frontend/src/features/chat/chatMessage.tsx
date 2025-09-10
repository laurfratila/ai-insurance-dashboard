import type { ChatMessage as Msg } from "./types";
import { Bot, User } from "lucide-react";

export default function ChatMessage({ m }: { m: Msg }) {
  const mine = m.role === "user";
  return (
    <div className={`flex gap-3 ${mine ? "flex-row-reverse" : ""}`}>
      <div className={`shrink-0 mt-1 rounded-full p-1.5 ${mine ? "bg-slate-900" : "bg-slate-200"}`}>
        {mine ? <User size={14} color="#fff" /> : <Bot size={14} />}
      </div>
      <div className="max-w-[85%] rounded-2xl px-3.5 py-2 text-[14px] leading-6 shadow-soft border bg-white border-slate-200">
        {m.content}
      </div>
    </div>
  );
}

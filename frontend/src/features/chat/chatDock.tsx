import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createChatAdapter } from "./chatService";
import type { ChatMessage } from "./types";
import ChatMessageBubble from "./ChatMessage";
import { Bot, SendHorizonal, Trash2, PanelRightOpen, PanelRightClose } from "lucide-react";

const adapter = createChatAdapter();

export default function ChatDock({
  initialWidth = 360,                 // <— a bit less than 420
  visible,
  onToggle,
}: {
  initialWidth?: number;
  visible: boolean;
  onToggle: () => void;
}) {
  const [width, setWidth] = useState(initialWidth);
  const [drag, setDrag] = useState<null | { startX: number; startW: number }>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([{
    id: crypto.randomUUID(),
    role: "assistant",
    content:
      "Hi, I’m the EnsuraX assistant. Ask me natural questions about GWP, loss ratio, claims, or operations.\n\nExamples:\n• “What’s our loss ratio trend YTD?”\n• “Top products by claims frequency last 6 months”\n• “Why did LR increase in August?”",
    createdAt: new Date().toISOString(),
  }]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, visible]);

  function startDrag(e: React.MouseEvent) {
    setDrag({ startX: e.clientX, startW: width });
  }
  function onMove(e: MouseEvent) {
    if (!drag) return;
    const next = Math.max(320, Math.min(720, drag.startW - (drag.startX - e.clientX)));
    setWidth(next);
  }
  function onUp() { setDrag(null); }
  useEffect(() => {
    if (!drag) return;
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp, { once: true });
    return () => { window.removeEventListener("mousemove", onMove); };
  }, [drag]);

  async function send() {
    const text = input.trim();
    if (!text) return;
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text, createdAt: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);
    try {
      const reply = await adapter.ask({ messages: [...messages, userMsg], sessionId: getSessionId() });
      const botMsg: ChatMessage = { id: crypto.randomUUID(), role: "assistant", content: reply, createdAt: new Date().toISOString() };
      setMessages((m) => [...m, botMsg]);
    } catch (err: any) {
      const botMsg: ChatMessage = { id: crypto.randomUUID(), role: "assistant", content: `⚠️ ${err?.message ?? "Chat error"}`, createdAt: new Date().toISOString() };
      setMessages((m) => [...m, botMsg]);
    } finally {
      setSending(false);
    }
  }

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function clearChat() {
    setMessages([{
      id: crypto.randomUUID(), role: "assistant",
      content: "Conversation cleared. How can I help next?",
      createdAt: new Date().toISOString(),
    }]);
  }

  if (!visible) {
    return (
      <div className="flex items-center justify-end pr-2">
        <Button variant="secondary" size="sm" onClick={onToggle} className="gap-2">
          <PanelRightOpen size={16} /> Assistant
        </Button>
      </div>
    );
  }

  return (
    <aside style={{ width }} className="h-full pl-2 select-none relative">
      <div className="h-full grid grid-rows-[auto_1fr_auto]">
        {/* Header */}
        <Card className="p-3 rounded-xl border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <Bot size={18} /> Assistant <span className="text-xs font-normal text-slate-500 ml-2">beta</span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={clearChat} title="Clear conversation">
                <Trash2 size={16} />
              </Button>
              <Button variant="outline" size="sm" onClick={onToggle} title="Collapse">
                <PanelRightClose size={16} />
              </Button>
            </div>
          </div>
        </Card>

        {/* Messages */}
        <Card className="mt-2 overflow-hidden border-slate-200">
          <div ref={scrollRef} className="h-full overflow-y-auto p-3 space-y-3 bg-white">
            {messages.map((m) => (
              <ChatMessageBubble key={m.id} m={m} />
            ))}
          </div>
        </Card>

        {/* Composer */}
        <div className="mt-2">
          <div className="flex gap-2">
            <Input
              placeholder={sending ? "Thinking…" : "Ask about KPIs, claims, risk… (Enter to send)"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              disabled={sending}
            />
            <Button onClick={send} disabled={sending || !input.trim()} className="gap-2">
              <SendHorizonal size={16} /> Send
            </Button>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Shift+Enter for newline · Each turn is sent with your session</div>
        </div>
      </div>

      {/* Resizer handle */}
      <div onMouseDown={startDrag} className="absolute top-0 left-[-6px] h-full w-[6px] cursor-col-resize" />
    </aside>
  );
}

function getSessionId(): string {
  const k = "ensurax_chat_session";
  let id = localStorage.getItem(k);
  if (!id) { id = crypto.randomUUID(); localStorage.setItem(k, id); }
  return id;
}

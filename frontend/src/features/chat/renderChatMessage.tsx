import ChatMessageBubble from "./chatMessage";
import ForecastCard from "./ForecastCard";

export function renderChatMessage(m: any) {
  // Only check startsWith if m.content is a string
  if (
    m.role === "assistant" &&
    typeof m.content === "string" &&
    m.content.startsWith('{"type":"forecast"')
  ) {
    try {
      const forecast = JSON.parse(m.content);
      return (
        <ForecastCard
          key={m.id}
          rows={forecast.rows || []}
          summary={forecast.summary}
          question={forecast.question}
        />
      );
    } catch {
      return <ChatMessageBubble key={m.id} m={m} />;
    }
  }
  return <ChatMessageBubble key={m.id} m={m} />;
}

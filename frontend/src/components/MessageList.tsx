import { Bot, CircleHelp, History, PencilLine, RotateCcw, Trash2, UserRound } from "lucide-react";
import { useEffect, useRef } from "react";
import type { ClarificationRequest, Message, WorkflowResultMetadata } from "../types";
import { PromptResult } from "./PromptResult";

function clarificationFor(message: Message): ClarificationRequest | null {
  const result = message.metadata?.workflow_result as WorkflowResultMetadata | undefined;
  const request = result?.clarification_request;
  if (request?.question) {
    return {
      question: request.question,
      options: Array.isArray(request.options) ? request.options.filter(Boolean) : [],
    };
  }
  const prefix = "需要确认：";
  if (message.content.startsWith(prefix)) {
    return { question: message.content.slice(prefix.length).trim(), options: [] };
  }
  return null;
}

export function MessageList({
  messages,
  pending,
  onRewind,
  onDeleteLatestTurn,
  onClarificationReply,
  onClarificationRetry,
  onClarificationExplain,
}: {
  messages: Message[];
  pending: boolean;
  onRewind?: (message: Message) => void;
  onDeleteLatestTurn?: () => void;
  onClarificationReply?: (reply: string) => void;
  onClarificationRetry?: () => void;
  onClarificationExplain?: () => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const latestUserMessageId = [...messages].reverse().find((message) => message.role === "user")?.id;
  const latestAssistantMessageId = [...messages].reverse().find((message) => message.role === "assistant")?.id;
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  if (!messages.length && !pending) {
    return (
      <div className="message-list">
        <div className="empty-workspace">
          <Bot size={28} strokeWidth={1.6} />
          <strong>描述你想生成的画面</strong>
          <p>工作流会理解上下文、验证标签并按目标模型整理 Prompt。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message) => {
        const user = message.role === "user";
        const clarification = user ? null : clarificationFor(message);
        const clarificationActive = message.id === latestAssistantMessageId && !pending;
        return (
          <article className={`message ${user ? "user" : "assistant"}`} key={message.id}>
            <div className="message-author">
              {user ? <UserRound size={15} /> : <Bot size={15} />}
              <span>{user ? "你" : "工作流结果"}</span>
            </div>
            <div className="message-surface">
              {user ? (
                <div className="message-text">{message.content}</div>
              ) : clarification ? (
                <div className="clarification-card">
                  <header><CircleHelp size={16} /><strong>需要确认本轮修改</strong></header>
                  <p>{clarification.question}</p>
                  {clarificationActive && (
                    <div className="clarification-actions">
                      {clarification.options.map((option) => (
                        <button key={option} onClick={() => onClarificationReply?.(option)} type="button">
                          {option}
                        </button>
                      ))}
                      {!clarification.options.length && (
                        <button onClick={onClarificationRetry} type="button"><RotateCcw size={14} />重新尝试</button>
                      )}
                      <button className="secondary" onClick={onClarificationExplain} type="button"><PencilLine size={14} />补充说明</button>
                      <button className="secondary danger" onClick={onDeleteLatestTurn} type="button"><Trash2 size={14} />取消本轮</button>
                    </div>
                  )}
                </div>
              ) : (
                <PromptResult content={message.content} />
              )}
            </div>
            {user && onRewind && !message.id.startsWith("local-") && (
              <div className="message-actions" aria-label="消息操作">
                <button onClick={() => onRewind(message)} title="回溯到这里并重新编辑" type="button">
                  <History size={14} /><span>回溯</span>
                </button>
                {message.id === latestUserMessageId && onDeleteLatestTurn && (
                  <button className="danger" onClick={onDeleteLatestTurn} title="删除这一轮" type="button">
                    <Trash2 size={14} /><span>删除本轮</span>
                  </button>
                )}
              </div>
            )}
          </article>
        );
      })}
      {pending && (
        <article className="message assistant pending-message">
          <div className="message-author"><Bot size={15} /><span>工作流处理中</span></div>
          <div className="typing-indicator"><i /><i /><i /></div>
        </article>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

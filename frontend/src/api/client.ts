import type { Conversation, Crew, DslData, DslKind, DslSummary, Message, StreamProtocolEvent, Workflow, WorkflowInputs } from "../types";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `${response.status} ${response.statusText}`);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export const api = {
  workflows: () => request<Workflow[]>("/api/workflows/"),
  crews: () => request<Crew[]>("/api/crews/"),
  conversations: (userId: string, crewId: string) => {
    const query = new URLSearchParams({ user_id: userId, crew_id: crewId });
    return request<Conversation[]>(`/api/conversations/?${query}`);
  },
  messages: (conversationId: string) =>
    request<Message[]>(`/api/conversations/${conversationId}/messages`),
  createSampleCrew: (workflowName: string) =>
    request<Crew>(`/api/workflows/${workflowName}/sample-crew`, {
      method: "POST",
      body: "{}",
    }),
  updateCrewWorkflow: (crew: Crew, workflowName: string) =>
    request<Crew>(`/api/crews/${crew.id}`, {
      method: "PUT",
      body: JSON.stringify({
        workflow_type: workflowName,
      }),
    }),
  deleteCrew: (crewId: string) =>
    request<void>(`/api/crews/${crewId}`, { method: "DELETE" }),
  createConversation: (userId: string, crewId: string, title: string) =>
    request<Conversation>("/api/conversations/", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, crew_id: crewId, title }),
    }),
  deleteConversation: (conversationId: string) =>
    request<void>(`/api/conversations/${conversationId}`, { method: "DELETE" }),
  deleteLatestTurn: (conversationId: string) =>
    request<void>(`/api/conversations/${conversationId}/turns/latest`, {
      method: "DELETE",
    }),
  rewindConversation: (conversationId: string, messageId: string) =>
    request<{ deleted_messages: number }>(`/api/conversations/${conversationId}/turns/from/${messageId}`, {
      method: "DELETE",
    }),
  dslList: (kind: DslKind) => request<DslSummary[]>(`/api/dsl/${kind}`),
  dsl: (kind: DslKind, name: string) =>
    request<{ kind: DslKind; name: string; data: DslData }>(`/api/dsl/${kind}/${name}`),
  validateDsl: (kind: DslKind, data: DslData) =>
    request<{ kind: DslKind; name: string; nodes: string[]; entrypoint: string }>(`/api/dsl/${kind}/validate`, {
      method: "POST",
      body: JSON.stringify({ data }),
    }),
  saveDsl: (kind: DslKind, name: string, data: DslData) =>
    request<{ path: string }>(`/api/dsl/${kind}/${name}`, {
      method: "PUT",
      body: JSON.stringify({ data }),
    }),
  generateDsl: (kind: DslKind, name: string, data: DslData) =>
    request<{ generated_files: string[]; restart_required: boolean }>(`/api/dsl/${kind}/${name}/generate`, {
      method: "POST",
      body: JSON.stringify({ data }),
    }),
};

export async function streamChat(
  conversationId: string,
  message: string,
  workflowInputs: WorkflowInputs,
  onEvent: (event: Record<string, unknown>) => void,
  signal?: AbortSignal,
  resume = false,
  onDelta?: (delta: string, event: StreamProtocolEvent | null) => void,
): Promise<string> {
  const response = await fetch(`/api/conversations/${conversationId}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, workflow_inputs: workflowInputs, resume }),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error((await response.text()) || response.statusText);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let content = "";
  let structuredProtocol = false;
  let streamError = "";
  let doneReceived = false;

  const consumeBlock = (block: string) => {
    const data = block
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (!data) return false;
    if (data === "[DONE]") {
      doneReceived = true;
      return true;
    }
    const event = JSON.parse(data) as Record<string, unknown>;
    onEvent(event);
    if (event.object === "agent.workflow.stream") {
      structuredProtocol = true;
      const protocolEvent = event as StreamProtocolEvent;
      if (protocolEvent.type === "run.failed") {
        streamError = protocolEvent.error || "工作流执行失败";
      }
      if (protocolEvent.type === "message.delta" && protocolEvent.delta) {
        content += protocolEvent.delta;
        onDelta?.(protocolEvent.delta, protocolEvent);
      }
    } else if (!structuredProtocol && event.object === "chat.completion.chunk") {
      const choices = event.choices as Array<{ delta?: { content?: string } }> | undefined;
      const delta = choices?.[0]?.delta?.content ?? "";
      content += delta;
      if (delta) onDelta?.(delta, null);
    }
    return false;
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replaceAll("\r\n", "\n");
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      if (consumeBlock(block)) {
        if (streamError) throw new Error(streamError);
        return content;
      }
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) consumeBlock(buffer);
  if (streamError) throw new Error(streamError);
  if (!doneReceived && !signal?.aborted) {
    throw new Error("工作流流式连接意外结束");
  }
  return content;
}

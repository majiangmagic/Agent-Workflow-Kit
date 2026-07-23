import { useCallback, useEffect, useRef, useState } from "react";
import { streamChat } from "../api/client";
import type { EdgeSelection, NodeStatus, RuntimeEvent, WorkflowEvent, WorkflowInputs } from "../types";

function runtimeEventLabel(type: string, node?: string) {
  const target = node ? ` · ${node}` : "";
  if (type === "run.started") return "开始执行工作流";
  if (type === "run.completed") return "工作流执行完成";
  if (type === "run.failed") return "工作流执行失败";
  if (type === "run.cancelled") return "工作流已停止";
  if (type === "message.started") return "创建助手消息";
  if (type === "message.completed") return "助手消息已完成";
  if (type === "workflow.node.started") return `节点开始${target}`;
  if (type === "workflow.node.completed") return `节点完成${target}`;
  if (type === "workflow.node.error") return `节点失败${target}`;
  if (type === "workflow.edge.selected") return "选择下一条工作流路径";
  return type;
}

export function useWorkflowStream() {
  const [running, setRunning] = useState(false);
  const [runStatus, setRunStatus] = useState<"idle" | "running" | "completed" | "failed" | "cancelled">("idle");
  const [runError, setRunError] = useState("");
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, NodeStatus>>({});
  const [nodeDurations, setNodeDurations] = useState<Record<string, number>>({});
  const [selectedEdges, setSelectedEdges] = useState<Record<string, EdgeSelection>>({});
  const [runtimeEvents, setRuntimeEvents] = useState<RuntimeEvent[]>([]);
  const controllerRef = useRef<AbortController | null>(null);
  const nodeStartedAt = useRef<Record<string, number>>({});
  const structuredProtocolRef = useRef(false);

  useEffect(() => () => {
    controllerRef.current?.abort();
  }, []);

  const clear = useCallback(() => {
    setNodeStatuses({});
    setNodeDurations({});
    setSelectedEdges({});
    setRuntimeEvents([]);
    setRunStatus("idle");
    setRunError("");
    nodeStartedAt.current = {};
    structuredProtocolRef.current = false;
  }, []);
  const cancel = useCallback(() => controllerRef.current?.abort(), []);

  const run = useCallback(
    async (
      conversationId: string,
      message: string,
      inputs: WorkflowInputs,
      resume = false,
      handlers?: { onDelta?: (delta: string) => void },
    ) => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;
      setRunning(true);
      setRunStatus("running");
      setRunError("");
      setNodeStatuses({});
      setNodeDurations({});
      setSelectedEdges({});
      setRuntimeEvents([]);
      nodeStartedAt.current = {};
      structuredProtocolRef.current = false;
      try {
        const result = await streamChat(
          conversationId,
          message,
          inputs,
          (rawEvent) => {
            const protocolEvent = rawEvent.object === "agent.workflow.stream"
              ? rawEvent
              : null;
            if (protocolEvent) structuredProtocolRef.current = true;
            if (!protocolEvent && structuredProtocolRef.current && rawEvent.object === "workflow.event") {
              return;
            }
            if (protocolEvent && protocolEvent.type !== "workflow.progress" && protocolEvent.type !== "message.delta") {
              const type = String(protocolEvent.type || "stream.event");
              setRuntimeEvents((current) => [...current, {
                id: String(protocolEvent.id || crypto.randomUUID()),
                type,
                label: runtimeEventLabel(type),
                timestamp: Date.now(),
              }].slice(-100));
            }
            if (protocolEvent?.type === "run.failed") {
              setRunStatus("failed");
              setRunError(String(protocolEvent.error || "工作流执行失败"));
            }
            const workflowEvent = protocolEvent?.type === "workflow.progress"
              ? protocolEvent.event
              : rawEvent.object === "workflow.event"
                ? rawEvent
                : null;
            if (!workflowEvent) return;
            const event = workflowEvent as unknown as WorkflowEvent;
            setRuntimeEvents((current) => [...current, {
              id: crypto.randomUUID(),
              type: event.type,
              node: event.node,
              label: runtimeEventLabel(event.type, event.node),
              timestamp: Date.now(),
            }].slice(-100));
            if (event.type === "workflow.edge.selected" && event.from && event.to && event.branch) {
              const edgeKey = `${event.from}->${event.to}`;
              setSelectedEdges((current) => ({
                ...current,
                [edgeKey]: {
                  from: event.from!,
                  to: event.to!,
                  branch: event.branch!,
                  iteration: event.iteration ?? 0,
                  maxIterations: event.max_iterations,
                },
              }));
              return;
            }
            const node = event.node;
            if (!node) return;
            const status: NodeStatus = event.type.includes("error")
              ? "error"
              : event.type.includes("completed")
                ? "completed"
                : event.type.includes("started") || event.type.includes("assigned")
                  ? "running"
                  : "idle";
            if (status === "running") nodeStartedAt.current[node] = performance.now();
            if (status === "completed" || status === "error") {
              const startedAt = nodeStartedAt.current[node];
              if (startedAt !== undefined) {
                setNodeDurations((current) => ({
                  ...current,
                  [node]: performance.now() - startedAt,
                }));
              }
            }
            setNodeStatuses((current) => ({ ...current, [node]: status }));
          },
          controller.signal,
          resume,
          (delta) => handlers?.onDelta?.(delta),
        );
        setRunStatus("completed");
        return result;
      } catch (reason) {
        if (reason instanceof DOMException && reason.name === "AbortError") {
          setRunStatus("cancelled");
        } else {
          setRunStatus("failed");
          setRunError(reason instanceof Error ? reason.message : String(reason));
        }
        throw reason;
      } finally {
        if (controllerRef.current === controller) {
          controllerRef.current = null;
          setRunning(false);
        }
      }
    },
    [],
  );

  return {
    running,
    runStatus,
    runError,
    nodeStatuses,
    nodeDurations,
    selectedEdges,
    runtimeEvents,
    run,
    clear,
    cancel,
  };
}

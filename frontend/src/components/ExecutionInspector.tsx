import { Activity, Check, Circle, Clock3, LoaderCircle, RotateCcw, TriangleAlert, Workflow as WorkflowIcon, X } from "lucide-react";
import { useState } from "react";
import type { EdgeSelection, NodeStatus, RuntimeEvent, Workflow } from "../types";
import { Pipeline } from "./Pipeline";

type Props = {
  open: boolean;
  dark: boolean;
  runStatus: "idle" | "running" | "completed" | "failed" | "cancelled";
  runError: string;
  workflow?: Workflow;
  statuses: Record<string, NodeStatus>;
  durations: Record<string, number>;
  selectedEdges: Record<string, EdgeSelection>;
  events: RuntimeEvent[];
  onClear: () => void;
  onClose: () => void;
};

function statusLabel(status: NodeStatus) {
  if (status === "running") return "执行中";
  if (status === "completed") return "已完成";
  if (status === "error") return "失败";
  return "等待";
}

function runStatusLabel(status: Props["runStatus"]) {
  if (status === "running") return "执行中";
  if (status === "completed") return "已完成";
  if (status === "failed") return "执行失败";
  if (status === "cancelled") return "已停止";
  return "等待执行";
}

function StatusIcon({ status }: { status: NodeStatus }) {
  if (status === "running") return <LoaderCircle className="spin" size={14} />;
  if (status === "completed") return <Check size={14} />;
  if (status === "error") return <TriangleAlert size={14} />;
  return <Circle size={10} />;
}

function durationLabel(duration?: number) {
  if (duration === undefined) return "";
  return duration < 1000 ? `${Math.round(duration)} ms` : `${(duration / 1000).toFixed(1)} s`;
}

export function ExecutionInspector(props: Props) {
  const [tab, setTab] = useState<"topology" | "activity">("topology");
  const completed = Object.values(props.statuses).filter((status) => status === "completed").length;

  return (
    <aside className={`execution-inspector ${props.open ? "open" : ""}`} aria-label="运行检查器">
      {props.open && <>
        <header className="inspector-header">
        <div>
          <strong>运行检查器</strong>
          <span className={`inspector-run-state ${props.runStatus}`} title={props.runError || undefined}>
            <i />{runStatusLabel(props.runStatus)}
            {props.workflow ? ` · ${completed}/${props.workflow.nodes.length} 个节点` : " · 未选择工作流"}
          </span>
        </div>
        <button className="icon-button light" onClick={props.onClose} title="关闭检查器" type="button"><X size={16} /></button>
        </header>

        <div className="runtime-tabs" role="tablist" aria-label="检查器视图">
          <button className={tab === "topology" ? "active" : ""} onClick={() => setTab("topology")} role="tab" type="button"><WorkflowIcon size={14} />拓扑</button>
          <button className={tab === "activity" ? "active" : ""} onClick={() => setTab("activity")} role="tab" type="button"><Activity size={14} />运行</button>
        </div>

        {tab === "topology" ? (
          <Pipeline dark={props.dark} durations={props.durations} embedded onClear={props.onClear} selectedEdges={props.selectedEdges} statuses={props.statuses} workflow={props.workflow} />
        ) : (
          <div className="runtime-activity">
          <div className="runtime-activity-toolbar">
            <span>节点执行状态</span>
            <button className="quiet-button" onClick={props.onClear} type="button"><RotateCcw size={13} />清空</button>
          </div>
          <div className="runtime-node-list">
            {props.workflow?.nodes.map((node) => {
              const status = props.statuses[node.name] ?? "idle";
              return (
                <div className={`runtime-list-item ${status}`} key={node.name}>
                  <StatusIcon status={status} />
                  <div><strong>{node.display_name ?? node.name.replaceAll("_", " ")}</strong><span>{node.agent}</span></div>
                  <small>{durationLabel(props.durations[node.name]) || statusLabel(status)}</small>
                </div>
              );
            })}
            {!props.workflow && <div className="pipeline-empty">选择工作流后显示节点状态</div>}
          </div>
          <div className="runtime-event-section">
            <div className="runtime-activity-toolbar">
              <span><Clock3 size={13} />事件时间线</span>
              <small>{props.events.length}</small>
            </div>
            <div className="runtime-event-list">
              {[...props.events].reverse().map((event) => (
                <div className={`runtime-event ${event.type.includes("failed") || event.type.includes("error") ? "error" : ""}`} key={event.id}>
                  <i />
                  <div>
                    <strong>{event.label}</strong>
                    <span>{new Date(event.timestamp).toLocaleTimeString("zh-CN", { hour12: false })}</span>
                  </div>
                </div>
              ))}
              {!props.events.length && <div className="pipeline-empty">执行后将在这里显示事件</div>}
            </div>
          </div>
          </div>
        )}
      </>}
    </aside>
  );
}

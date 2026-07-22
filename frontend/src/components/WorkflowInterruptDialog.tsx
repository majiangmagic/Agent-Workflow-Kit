import { CircleHelp, CornerDownLeft, X } from "lucide-react";
import { useEffect, useState } from "react";
import type { WorkflowInterrupt } from "../types";

export function WorkflowInterruptDialog({
  interrupt,
  busy,
  onClose,
  onSubmit,
}: {
  interrupt: WorkflowInterrupt | null;
  busy: boolean;
  onClose: () => void;
  onSubmit: (response: string) => void;
}) {
  const [response, setResponse] = useState("");

  useEffect(() => setResponse(""), [interrupt?.id, interrupt?.question]);

  if (!interrupt) return null;
  const submit = (value: string) => {
    const answer = value.trim();
    if (answer && !busy) onSubmit(answer);
  };

  return (
    <div className="dialog-backdrop workflow-interrupt-backdrop" role="presentation">
      <section
        aria-labelledby="workflow-interrupt-title"
        aria-modal="true"
        className="workflow-interrupt-dialog"
        role="dialog"
      >
        <header>
          <div className="workflow-interrupt-heading">
            <span className="workflow-interrupt-icon"><CircleHelp size={18} /></span>
            <div>
              <span>工作流已暂停</span>
              <h2 id="workflow-interrupt-title">需要补充信息</h2>
            </div>
          </div>
          <button className="icon-button" disabled={busy} onClick={onClose} title="暂时关闭" type="button">
            <X size={17} />
          </button>
        </header>

        <p className="workflow-interrupt-question">{interrupt.question}</p>
        {interrupt.context && <p className="workflow-interrupt-context">{interrupt.context}</p>}

        {Boolean(interrupt.options.length) && (
          <div className="workflow-interrupt-options">
            {interrupt.options.map((option) => (
              <button disabled={busy} key={option} onClick={() => submit(option)} type="button">
                {option}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={(event) => { event.preventDefault(); submit(response); }}>
          <label htmlFor="workflow-interrupt-response">补充说明</label>
          <textarea
            autoFocus
            disabled={busy}
            id="workflow-interrupt-response"
            onChange={(event) => setResponse(event.target.value)}
            placeholder="输入监管者继续执行所需的信息……"
            rows={4}
            value={response}
          />
          <footer>
            <span>提交后从当前暂停位置继续</span>
            <button className="send-button" disabled={busy || !response.trim()} type="submit">
              继续执行 <CornerDownLeft size={15} />
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

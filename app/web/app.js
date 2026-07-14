const state = {
  workflows: [],
  crews: [],
  conversations: [],
  currentConversationId: null,
  workflowInputs: {},
};

const els = Object.fromEntries([
  "status", "workflowSelect", "crewSelect", "userIdInput", "createCrewButton",
  "deleteCrewButton", "newChatButton", "refreshButton", "conversationList",
  "chatTitle", "chatMeta", "deleteLastTurnButton", "deleteConversationButton", "workflowControls",
  "clearProgressButton", "progressList", "messageList", "chatForm",
  "messageInput", "inputHint", "sendButton",
].map((id) => [id, document.querySelector(`#${id}`)]));

function setStatus(text, active = false) {
  els.status.innerHTML = `<span class="status-dot"></span>${escapeHtml(text)}`;
  els.status.querySelector(".status-dot").style.background = active ? "#e3b34c" : "#8de0b7";
}

function selectedCrew() {
  return state.crews.find((crew) => crew.id === els.crewSelect.value) || null;
}

function selectedWorkflow() {
  return state.workflows.find((workflow) => workflow.name === els.workflowSelect.value) || null;
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) throw new Error((await response.text()) || `${response.status} ${response.statusText}`);
  return response.status === 204 ? null : response.json();
}

function renderSelect(select, items, labelOf, valueOf) {
  select.replaceChildren();
  if (!items.length) {
    select.append(new Option("暂无可选项", ""));
    return;
  }
  items.forEach((item) => select.append(new Option(labelOf(item), valueOf(item))));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function renderConversations() {
  els.conversationList.replaceChildren();
  els.deleteLastTurnButton.disabled = !state.currentConversationId;
  els.deleteConversationButton.disabled = !state.currentConversationId;
  if (!state.conversations.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "暂无历史会话";
    els.conversationList.append(empty);
    return;
  }
  state.conversations.forEach((conversation) => {
    const row = document.createElement("div");
    row.className = `conversation-row${conversation.id === state.currentConversationId ? " active" : ""}`;
    const openButton = document.createElement("button");
    openButton.type = "button";
    openButton.className = "conversation-item";
    openButton.innerHTML = `<span class="conversation-title">${escapeHtml(conversation.title || "未命名会话")}</span><span class="conversation-time">${formatTime(conversation.updated_at || conversation.created_at)}</span>`;
    openButton.addEventListener("click", () => openConversation(conversation.id));
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "delete-mini";
    deleteButton.title = "删除会话";
    deleteButton.textContent = "×";
    deleteButton.addEventListener("click", async (event) => {
      event.stopPropagation();
      await deleteConversation(conversation.id, { confirmDelete: true });
    });
    row.append(openButton, deleteButton);
    els.conversationList.append(row);
  });
}

function roleLabel(role) {
  return ({ user: "你", assistant: "PROMPT RESULT", agent: "AGENT" })[String(role).toLowerCase()] || "消息";
}

function appendMessage(role, content) {
  const item = document.createElement("article");
  item.className = `message ${String(role).toLowerCase()}`;
  item.innerHTML = `<div class="message-role">${roleLabel(role)}</div><div class="message-bubble">${escapeHtml(content)}</div>`;
  els.messageList.append(item);
  els.messageList.scrollTop = els.messageList.scrollHeight;
}

function renderMessages(messages) {
  els.messageList.replaceChildren();
  if (!messages.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "输入一段画面描述，工作流会拆分人物、场景与额外视觉控制，查询 Danbooru 标签后生成目标模型可用的 Prompt。";
    els.messageList.append(empty);
    return;
  }
  messages.forEach((message) => appendMessage(message.role, message.content));
}

function clearProgress() {
  els.progressList.querySelectorAll(".stage").forEach((stage) => stage.classList.remove("running", "completed", "error"));
}

function workflowLevels(workflow) {
  const nodes = workflow?.nodes || [];
  const names = new Set(nodes.map((node) => node.name));
  const ranks = Object.fromEntries(nodes.map((node) => [node.name, 0]));
  for (let pass = 0; pass < nodes.length; pass += 1) {
    for (const edge of workflow?.edges || []) {
      if (edge.to === "END" || !names.has(edge.to)) continue;
      const sources = Array.isArray(edge.from) ? edge.from : [edge.from];
      const sourceRank = Math.max(0, ...sources.map((source) => ranks[source] ?? 0));
      ranks[edge.to] = Math.max(ranks[edge.to] ?? 0, sourceRank + 1);
    }
  }
  const groups = [];
  nodes.forEach((node) => {
    const rank = ranks[node.name] ?? 0;
    if (!groups[rank]) groups[rank] = [];
    groups[rank].push(node);
  });
  return groups.filter(Boolean);
}

function renderWorkflowPipeline() {
  const levels = workflowLevels(selectedWorkflow());
  els.progressList.replaceChildren();
  els.progressList.style.setProperty("--pipeline-columns", String(Math.max(levels.length, 1)));
  let sequence = 1;
  levels.forEach((nodes) => {
    const column = document.createElement("div");
    column.className = "stage-column";
    nodes.forEach((node) => {
      const stage = document.createElement("div");
      stage.className = "stage";
      stage.dataset.node = node.name;
      const number = document.createElement("b");
      number.textContent = String(sequence).padStart(2, "0");
      const label = document.createElement("span");
      label.textContent = node.display_name || node.name.replaceAll("_", " ");
      stage.append(number, label);
      column.append(stage);
      sequence += 1;
    });
    els.progressList.append(column);
  });
  if (!levels.length) {
    const empty = document.createElement("div");
    empty.className = "pipeline-empty";
    empty.textContent = "该工作流未提供拓扑元数据";
    els.progressList.append(empty);
  }
}

function applyWorkflowUi() {
  const workflow = selectedWorkflow();
  const ui = workflow?.ui || {};
  const legacyModels = Array.isArray(ui.target_models) ? ui.target_models : [];
  const controls = Array.isArray(ui.controls) ? ui.controls : (
    legacyModels.length
      ? [{
          key: "target_model",
          label: "目标模型",
          type: "select",
          options: legacyModels,
          default: ui.default_target_model,
        }]
      : []
  );
  renderWorkflowControls(controls);
  els.messageInput.placeholder = ui.input_placeholder || "输入要交给工作流处理的任务……";
  els.inputHint.textContent = ui.input_hint || "消息将按当前工作流执行";
  if (!state.currentConversationId) {
    els.chatTitle.textContent = ui.title || workflow?.name || "新建任务";
    els.chatMeta.textContent = ui.description || selectedCrew()?.name || "选择 Crew 后开始";
  }
  renderWorkflowPipeline();
}

function renderWorkflowControls(controls) {
  els.workflowControls.replaceChildren();
  const nextInputs = {};
  controls.forEach((control) => {
    const key = String(control.key || "").trim();
    const options = Array.isArray(control.options) ? control.options : [];
    if (!key || !options.length) return;
    const values = options.map((option) => String(option.value));
    const previous = state.workflowInputs[key];
    const defaultValue = String(control.default ?? options[0].value);
    const selected = values.includes(String(previous)) ? String(previous) : defaultValue;
    nextInputs[key] = selected;

    const wrapper = document.createElement("label");
    wrapper.className = "workflow-control";
    const title = document.createElement("span");
    title.textContent = control.label || key.replaceAll("_", " ");
    wrapper.append(title);

    if (control.type === "segmented") {
      const segmented = document.createElement("div");
      segmented.className = "segmented-control";
      options.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = option.label || option.value;
        button.dataset.value = String(option.value);
        button.classList.toggle("active", button.dataset.value === selected);
        button.addEventListener("click", () => {
          state.workflowInputs[key] = button.dataset.value;
          segmented.querySelectorAll("button").forEach((item) => {
            item.classList.toggle("active", item === button);
          });
        });
        segmented.append(button);
      });
      wrapper.append(segmented);
    } else {
      const select = document.createElement("select");
      renderSelect(
        select,
        options,
        (option) => option.label || option.value,
        (option) => option.value,
      );
      select.value = selected;
      select.addEventListener("change", () => {
        state.workflowInputs[key] = select.value;
      });
      wrapper.append(select);
    }
    els.workflowControls.append(wrapper);
  });
  state.workflowInputs = nextInputs;
  els.workflowControls.hidden = els.workflowControls.childElementCount === 0;
}

function appendProgress(event) {
  const node = event.node || event.agent_name || "";
  const stage = els.progressList.querySelector(`[data-node="${CSS.escape(node)}"]`);
  if (!stage) return;
  if (String(event.type).includes("error")) {
    stage.classList.add("error");
    if (event.error) stage.title = event.error;
  }
  else if (String(event.type).includes("completed")) {
    stage.classList.remove("running");
    stage.classList.add("completed");
  } else if (String(event.type).includes("started") || String(event.type).includes("assigned")) {
    stage.classList.add("running");
  }
}

async function loadWorkflows() {
  state.workflows = await requestJson("/api/workflows/");
  renderSelect(els.workflowSelect, state.workflows, (item) => item.is_default ? `${item.name} · 默认` : item.name, (item) => item.name);
  applyWorkflowUi();
}

function syncWorkflowFromCrew() {
  const workflow = selectedCrew()?.settings?.workflow_type;
  if (workflow) els.workflowSelect.value = workflow;
  applyWorkflowUi();
}

async function loadCrews() {
  const selectedId = els.crewSelect.value;
  state.crews = await requestJson("/api/crews/");
  renderSelect(els.crewSelect, state.crews, (crew) => crew.name, (crew) => crew.id);
  if (state.crews.some((crew) => crew.id === selectedId)) els.crewSelect.value = selectedId;
  syncWorkflowFromCrew();
  const unavailable = !state.crews.length;
  els.sendButton.disabled = unavailable;
  els.deleteCrewButton.disabled = unavailable;
}

async function loadConversations() {
  const crew = selectedCrew();
  const userId = els.userIdInput.value.trim();
  state.conversations = crew && userId
    ? await requestJson(`/api/conversations/?${new URLSearchParams({ user_id: userId, crew_id: crew.id })}`)
    : [];
  renderConversations();
}

async function openConversation(id) {
  state.currentConversationId = id;
  els.deleteLastTurnButton.disabled = false;
  els.deleteConversationButton.disabled = false;
  const conversation = state.conversations.find((item) => item.id === id);
  els.chatTitle.textContent = conversation?.title || "未命名会话";
  els.chatMeta.textContent = id;
  renderConversations();
  renderMessages(await requestJson(`/api/conversations/${id}/messages`));
}

function resetChat() {
  state.currentConversationId = null;
  els.deleteLastTurnButton.disabled = true;
  els.deleteConversationButton.disabled = true;
  els.chatTitle.textContent = "新建提示词任务";
  els.chatMeta.textContent = selectedCrew()?.name || "选择 Crew 后开始";
  renderConversations();
  renderMessages([]);
  clearProgress();
  applyWorkflowUi();
  els.messageInput.focus();
}

async function updateCrewWorkflow() {
  const crew = selectedCrew();
  const workflowType = els.workflowSelect.value;
  if (!crew || !workflowType) return;
  const updated = await requestJson(`/api/crews/${crew.id}`, {
    method: "PUT",
    body: JSON.stringify({ settings: { ...(crew.settings || {}), workflow_type: workflowType } }),
  });
  state.crews = state.crews.map((item) => item.id === updated.id ? updated : item);
}

async function streamChat(conversationId, message, workflowInputs = {}) {
  const response = await fetch(`/api/conversations/${conversationId}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, workflow_inputs: workflowInputs }),
  });
  if (!response.ok || !response.body) throw new Error((await response.text()) || response.statusText);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalContent = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((part) => part.startsWith("data: "));
      if (!line) continue;
      const raw = line.slice(6);
      if (raw === "[DONE]") return finalContent;
      const event = JSON.parse(raw);
      if (event.object === "workflow.event") appendProgress(event);
      if (event.object === "chat.completion.chunk") finalContent += event.choices?.[0]?.delta?.content || "";
    }
  }
  return finalContent;
}

async function createSampleCrew() {
  if (!els.workflowSelect.value) return;
  els.createCrewButton.disabled = true;
  setStatus("正在创建 Crew", true);
  try {
    const crew = await requestJson(`/api/workflows/${els.workflowSelect.value}/sample-crew`, { method: "POST", body: "{}" });
    await loadCrews();
    els.crewSelect.value = crew.id;
    await loadConversations();
    resetChat();
    setStatus("已就绪");
  } catch (error) {
    appendMessage("assistant", `创建失败：${error.message}`);
    setStatus("发生错误");
  } finally {
    els.createCrewButton.disabled = false;
  }
}

async function deleteSelectedCrew() {
  const crew = selectedCrew();
  if (!crew || !confirm(`确定删除 Crew“${crew.name}”？`)) return;
  await requestJson(`/api/crews/${crew.id}`, { method: "DELETE" });
  await loadCrews();
  await loadConversations();
  resetChat();
}

async function deleteConversation(id, { confirmDelete = false } = {}) {
  if (confirmDelete && !confirm("确定删除这个会话？")) return;
  await requestJson(`/api/conversations/${id}`, { method: "DELETE" });
  if (state.currentConversationId === id) resetChat();
  await loadConversations();
}

async function deleteCurrentConversation() {
  if (!state.currentConversationId) return;
  await deleteConversation(state.currentConversationId, { confirmDelete: true });
}

async function deleteLastTurn() {
  if (!state.currentConversationId) return;
  if (!confirm("确定删除当前会话的最后一轮问答？")) return;
  const conversationId = state.currentConversationId;
  await requestJson(`/api/conversations/${conversationId}/turns/latest`, { method: "DELETE" });
  await loadConversations();
  if (state.conversations.some((conversation) => conversation.id === conversationId)) {
    await openConversation(conversationId);
  } else {
    resetChat();
  }
}

async function sendMessage(message) {
  els.sendButton.disabled = true;
  try {
    const crew = selectedCrew();
    const userId = els.userIdInput.value.trim();
    if (!crew) throw new Error("请先创建或选择 Crew");
    if (!userId) throw new Error("请输入用户标识");
    appendMessage("user", message);
    clearProgress();
    setStatus("工作流运行中", true);
    let conversationId = state.currentConversationId;
    if (!conversationId) {
      await updateCrewWorkflow();
      const conversation = await requestJson("/api/conversations/", {
        method: "POST",
        body: JSON.stringify({ user_id: userId, crew_id: crew.id, title: message.slice(0, 40) }),
      });
      conversationId = conversation.id;
      state.currentConversationId = conversationId;
      els.deleteLastTurnButton.disabled = false;
      els.deleteConversationButton.disabled = false;
      state.conversations.unshift(conversation);
      els.chatTitle.textContent = conversation.title;
      els.chatMeta.textContent = conversationId;
      renderConversations();
    }
    const result = await streamChat(
      conversationId,
      message,
      { ...state.workflowInputs },
    );
    appendMessage("assistant", result || "工作流已完成，但没有返回提示词。");
    await loadConversations();
    setStatus("已完成");
  } catch (error) {
    appendMessage("assistant", `请求失败：${error.message}`);
    setStatus("发生错误");
  } finally {
    els.sendButton.disabled = false;
  }
}

els.crewSelect.addEventListener("change", async () => { syncWorkflowFromCrew(); resetChat(); await loadConversations(); });
els.workflowSelect.addEventListener("change", resetChat);
els.userIdInput.addEventListener("change", loadConversations);
els.createCrewButton.addEventListener("click", createSampleCrew);
els.deleteCrewButton.addEventListener("click", deleteSelectedCrew);
els.deleteLastTurnButton.addEventListener("click", deleteLastTurn);
els.deleteConversationButton.addEventListener("click", deleteCurrentConversation);
els.newChatButton.addEventListener("click", resetChat);
els.refreshButton.addEventListener("click", loadConversations);
els.clearProgressButton.addEventListener("click", clearProgress);
els.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = els.messageInput.value.trim();
  if (!message) return;
  els.messageInput.value = "";
  await sendMessage(message);
});

(async function boot() {
  try {
    await loadWorkflows();
    await loadCrews();
    await loadConversations();
    resetChat();
    setStatus("已就绪");
  } catch (error) {
    setStatus("初始化失败");
    renderMessages([{ role: "assistant", content: error.message }]);
  }
})();

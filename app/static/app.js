"use strict";

const ALLOWED_TYPES = [".pdf", ".md", ".txt", ".csv"];
const MAX_BYTES = 5 * 1024 * 1024;
const MODE_HINTS = {
  auto: "Personal data stays on your device. Everything else uses the cloud agent.",
  local: "Everything runs on this laptop - works offline and costs nothing.",
  cloud: "Uses Microsoft Foundry. Personal data from documents is redacted first.",
};

const SVG = (paths) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
const ICONS = {
  plus: SVG('<path d="M12 5v14M5 12h14"/>'),
  file: SVG('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>'),
  x: SVG('<path d="M18 6 6 18M6 6l12 12"/>'),
  copy: SVG('<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'),
  tool: SVG('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'),
  trash: SVG('<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>'),
  paperclip: SVG('<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>'),
  send: SVG('<path d="M12 19V5M5 12l7-7 7 7"/>'),
  upload: SVG('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>'),
  sun: SVG('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'),
  moon: SVG('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
  menu: SVG('<path d="M3 6h18M3 12h18M3 18h18"/>'),
  currency: SVG('<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'),
  clock: SVG('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'),
  leaf: SVG('<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>'),
  shield: SVG('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'),
};

const state = { history: [], mode: "auto", busy: false, pending: [], docs: [] };
const $ = (sel) => document.querySelector(sel);
const thread = $("#thread");
const input = $("#input");
const heroTemplate = $("#hero").cloneNode(true);

// `html` is only ever given trusted icon markup or escaped markdown.
function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") el.className = value;
    else if (key === "html") el.innerHTML = value;
    else if (key.startsWith("on")) el.addEventListener(key.slice(2), value);
    else el.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child !== null && child !== undefined && child !== false) el.append(child);
  }
  return el;
}

function fillIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => (el.innerHTML = ICONS[el.dataset.icon] || ""));
}

/* ---------- Markdown (escape first, then a small safe subset) ---------- */
const escapeHtml = (s) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function inline(s) {
  return s
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\[(\d+)\]/g, '<span class="cite">$1</span>');
}

function renderBlocks(text) {
  let html = "";
  let list = null;
  const close = () => {
    if (list) html += `</${list}>`;
    list = null;
  };
  for (const line of text.split("\n")) {
    let m;
    if ((m = line.match(/^(#{1,3})\s+(.*)/))) {
      close();
      const level = m[1].length + 2;
      html += `<h${level}>${inline(m[2])}</h${level}>`;
    } else if ((m = line.match(/^\s*[-*]\s+(.*)/))) {
      if (list !== "ul") { close(); html += "<ul>"; list = "ul"; }
      html += `<li>${inline(m[1])}</li>`;
    } else if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) {
      if (list !== "ol") { close(); html += "<ol>"; list = "ol"; }
      html += `<li>${inline(m[1])}</li>`;
    } else if (line.trim()) {
      close();
      html += `<p>${inline(line)}</p>`;
    }
  }
  close();
  return html;
}

function renderMarkdown(src) {
  const parts = escapeHtml(src).split(/```([\w+-]*)\n?([\s\S]*?)```/g);
  let html = "";
  for (let i = 0; i < parts.length; i += 3) {
    html += renderBlocks(parts[i]);
    if (i + 2 < parts.length) {
      html +=
        `<div class="codeblock"><div class="codeblock-head"><span>${parts[i + 1] || "code"}</span>` +
        `<button type="button" class="copy-code">Copy</button></div><pre><code>${parts[i + 2]}</code></pre></div>`;
    }
  }
  return html;
}

/* ---------- UI helpers ---------- */
function toast(text, type = "info") {
  const el = h("div", { class: `toast ${type}` }, text);
  $("#toasts").append(el);
  setTimeout(() => {
    el.classList.add("hide");
    setTimeout(() => el.remove(), 300);
  }, 3800);
}

async function copyText(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    if (button.classList.contains("copy-code")) {
      button.textContent = "Copied";
      setTimeout(() => (button.textContent = "Copy"), 1200);
    } else {
      button.classList.add("done");
      button.innerHTML = SVG('<path d="M20 6 9 17l-5-5"/>');
      setTimeout(() => { button.classList.remove("done"); button.innerHTML = ICONS.copy; }, 1200);
    }
  } catch {
    toast("Could not copy to clipboard", "error");
  }
}

const scrollToBottom = () => $("#scroller").scrollTo({ top: $("#scroller").scrollHeight, behavior: "smooth" });
const errorText = (data) => (typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.");
const pretty = (s) => { try { return JSON.stringify(JSON.parse(s), null, 2); } catch { return s; } };
const fileChip = (name) => h("span", { class: "chip", html: ICONS.file }, h("span", { class: "chip-name", title: name }, name));
const avatar = () => h("div", { class: "avatar" }, "M");

/* ---------- Messages ---------- */
function addUserMessage(text, attachments) {
  $("#hero")?.remove();
  thread.append(
    h("div", { class: "msg user" },
      h("div", { class: "msg-body" },
        attachments.length ? h("div", { class: "attach-row" }, attachments.map(fileChip)) : null,
        h("div", { class: "bubble" }, text)))
  );
  scrollToBottom();
}

function addThinking() {
  const el = h("div", { class: "msg assistant" }, avatar(),
    h("div", { class: "msg-body" },
      h("div", { class: "thinking" },
        h("span", { class: "shimmer" }, "Thinking"),
        h("span", { class: "dots", html: "<i></i><i></i><i></i>" }))));
  thread.append(el);
  scrollToBottom();
  return el;
}

function renderStep(call) {
  return h("details", { class: "step" },
    h("summary", {}, h("span", { class: "step-icon", html: ICONS.tool }), "Used ", h("strong", {}, call.name)),
    h("div", { class: "step-body" },
      h("div", { class: "step-label" }, "Input"), h("pre", {}, pretty(call.arguments)),
      h("div", { class: "step-label" }, "Result"), h("pre", {}, pretty(call.result))));
}

function renderFooter(data) {
  const isLocal = data.provider !== "foundry";
  return h("div", { class: "msg-footer" },
    h("span", { class: `badge ${isLocal ? "local" : "cloud"}` }, isLocal ? "Local" : "Cloud"),
    h("span", {}, data.model), "·", h("span", {}, `${data.latency_s}s`), "·",
    h("span", {}, isLocal ? "free" : `KES ${data.cost_kes.toFixed(4)}`),
    h("span", { class: "reason", title: data.route_reason }, data.route_reason),
    h("button", {
      class: "icon-btn sm", type: "button", title: "Copy answer", "aria-label": "Copy answer",
      html: ICONS.copy, onclick: (e) => copyText(data.reply, e.currentTarget),
    }));
}

function addAssistantMessage(data) {
  thread.append(
    h("div", { class: "msg assistant" }, avatar(),
      h("div", { class: "msg-body" },
        data.tools.length ? h("div", { class: "steps" }, data.tools.map(renderStep)) : null,
        h("div", { class: "markdown", html: renderMarkdown(data.reply || "") }),
        renderFooter(data)))
  );
  scrollToBottom();
}

function addError(text) {
  thread.append(h("div", { class: "msg assistant" }, avatar(), h("div", { class: "msg-body" }, h("div", { class: "error-card" }, text))));
  scrollToBottom();
}

/* ---------- Chat ---------- */
function setBusy(busy) {
  state.busy = busy;
  $("#send").disabled = busy;
}

async function send(text) {
  text = text.trim();
  if (state.busy || !text) return;
  if (state.pending.some((p) => p.status === "uploading")) {
    toast("Please wait for the upload to finish", "info");
    return;
  }
  const attachments = state.pending.filter((p) => p.status === "ready").map((p) => p.name);
  state.pending = [];
  renderPending();
  setBusy(true);
  addUserMessage(text, attachments);
  input.value = "";
  autoGrow();
  const thinking = addThinking();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history: state.history.slice(-20), mode: state.mode, attachments }),
    });
    const data = await res.json().catch(() => ({}));
    thinking.remove();
    if (!res.ok) {
      addError(errorText(data));
      return;
    }
    addAssistantMessage(data);
    state.history.push({ role: "user", content: text }, { role: "assistant", content: data.reply.slice(0, 8000) });
  } catch {
    thinking.remove();
    addError("Could not reach the server. Is it running?");
  } finally {
    setBusy(false);
    input.focus();
  }
}

function newChat() {
  state.history = [];
  state.pending = [];
  renderPending();
  const hero = heroTemplate.cloneNode(true);
  thread.replaceChildren(hero);
  closeSidebar();
  input.focus();
}

/* ---------- Documents ---------- */
function renderPending() {
  const wrap = $("#attachments");
  wrap.replaceChildren(
    ...state.pending.map((item) =>
      h("span", { class: "chip", html: item.status === "uploading" ? '<span class="spinner"></span>' : ICONS.file },
        h("span", { class: "chip-name", title: item.name }, item.name),
        h("button", {
          class: "chip-x", type: "button", "aria-label": `Remove ${item.name}`, html: ICONS.x,
          onclick: () => { state.pending = state.pending.filter((p) => p !== item); renderPending(); },
        })))
  );
  wrap.hidden = state.pending.length === 0;
}

async function uploadFiles(files, attach) {
  for (const file of files) {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) { toast(`${file.name}: only PDF, MD, TXT and CSV are supported`, "error"); continue; }
    if (file.size > MAX_BYTES) { toast(`${file.name}: larger than 5 MB`, "error"); continue; }

    const item = { name: file.name, status: "uploading" };
    if (attach) { state.pending.push(item); renderPending(); }
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/documents", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(errorText(data));
      item.name = data.name;
      item.status = "ready";
      const note = data.pii ? " - personal data will be redacted for the cloud" : "";
      toast(`Added ${data.name} (${data.chunks} chunk${data.chunks === 1 ? "" : "s"})${note}`, "success");
      loadDocs();
    } catch (err) {
      state.pending = state.pending.filter((p) => p !== item);
      toast(`${file.name}: ${err.message}`, "error");
    }
    renderPending();
  }
}

async function loadDocs() {
  try {
    state.docs = await (await fetch("/api/documents")).json();
  } catch {
    return;
  }
  $("#doc-count").textContent = state.docs.length;
  $("#doc-list").replaceChildren(
    ...state.docs.map((doc) =>
      h("li", { class: "doc" },
        h("span", { class: "doc-icon", html: ICONS.file }),
        h("div", { class: "doc-info" },
          h("div", { class: "doc-name", title: doc.name }, doc.name),
          h("div", { class: "doc-meta" },
            `${doc.chunks} chunk${doc.chunks === 1 ? "" : "s"}`,
            doc.builtin ? h("span", { class: "tag" }, "sample") : null,
            doc.pii ? h("span", { class: "tag warn", title: "Personal data is redacted before it reaches the cloud" }, "PII") : null)),
        doc.builtin ? null : h("button", {
          class: "icon-btn sm", type: "button", title: "Remove", "aria-label": `Remove ${doc.name}`,
          html: ICONS.trash, onclick: () => removeDoc(doc),
        })))
  );
}

async function removeDoc(doc) {
  const res = await fetch(`/api/documents/${encodeURIComponent(doc.id)}`, { method: "DELETE" });
  if (res.ok) { toast(`Removed ${doc.name}`, "info"); loadDocs(); }
  else toast("Could not remove the document", "error");
}

/* ---------- Status, mode, theme ---------- */
function setModel(key, info) {
  const card = $(`#${key}-card`);
  card.classList.toggle("on", info.available);
  card.classList.toggle("off", !info.available);
  $(`#${key}-name`).textContent = info.model;
  $(`#${key}-sub`).textContent =
    key === "local"
      ? `${info.name} · ${info.available ? "ready" : "not found"}`
      : `Microsoft Foundry · ${info.available ? "online" : "offline"}`;
}

async function refreshStatus() {
  try {
    const status = await (await fetch("/api/status")).json();
    setModel("local", status.local);
    setModel("cloud", status.cloud);
  } catch {
    for (const key of ["local", "cloud"]) {
      $(`#${key}-card`).className = "model-card off";
      $(`#${key}-sub`).textContent = "server unreachable";
    }
  }
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll("#mode button").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  $("#mode-hint").textContent = MODE_HINTS[mode];
  $("#mode-pill").textContent = mode[0].toUpperCase() + mode.slice(1);
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("theme", theme);
  $("#theme-toggle").innerHTML = theme === "dark" ? ICONS.sun : ICONS.moon;
}

const closeSidebar = () => { $("#sidebar").classList.remove("open"); $("#backdrop").classList.remove("show"); };

function autoGrow() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 200)}px`;
}

/* ---------- Events ---------- */
$("#composer").addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
input.addEventListener("input", autoGrow);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(input.value); }
});
thread.addEventListener("click", (e) => {
  const card = e.target.closest(".card");
  if (card) send(card.dataset.prompt);
});
document.addEventListener("click", (e) => {
  const button = e.target.closest(".copy-code");
  if (button) copyText(button.closest(".codeblock").querySelector("code").textContent, button);
});
document.querySelectorAll("#mode button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
$("#new-chat").addEventListener("click", newChat);
$("#theme-toggle").addEventListener("click", () =>
  applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
$("#menu-btn").addEventListener("click", () => { $("#sidebar").classList.add("open"); $("#backdrop").classList.add("show"); });
$("#backdrop").addEventListener("click", closeSidebar);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSidebar(); });

$("#attach-btn").addEventListener("click", () => $("#attach-input").click());
$("#attach-input").addEventListener("change", (e) => { uploadFiles([...e.target.files], true); e.target.value = ""; });
$("#file-input").addEventListener("change", (e) => { uploadFiles([...e.target.files], false); e.target.value = ""; });

let dragDepth = 0;
const hasFiles = (e) => [...(e.dataTransfer?.types || [])].includes("Files");
window.addEventListener("dragenter", (e) => { if (hasFiles(e)) { dragDepth++; $("#drop-overlay").classList.add("show"); } });
window.addEventListener("dragleave", (e) => { if (hasFiles(e) && --dragDepth <= 0) { dragDepth = 0; $("#drop-overlay").classList.remove("show"); } });
window.addEventListener("dragover", (e) => { if (hasFiles(e)) e.preventDefault(); });
window.addEventListener("drop", (e) => {
  if (!hasFiles(e)) return;
  e.preventDefault();
  dragDepth = 0;
  $("#drop-overlay").classList.remove("show");
  uploadFiles([...e.dataTransfer.files], true);
});

/* ---------- Start ---------- */
fillIcons();
fillIcons(heroTemplate);
applyTheme(document.documentElement.dataset.theme);
setMode("auto");
refreshStatus();
loadDocs();
setInterval(refreshStatus, 30000);
input.focus();

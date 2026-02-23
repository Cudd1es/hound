import {
  buildEndpoint,
  defaultEndpoint,
  focusPostingText,
  requestPostingTextFromContentScript
} from "./sidepanel_helpers.js";

const apiUrlInput = document.getElementById("api-url");
const resumeFileInput = document.getElementById("resume-file");
const parseResumeFileBtn = document.getElementById("parse-resume-file");
const resumeJsonInput = document.getElementById("resume-json");
const postingTextInput = document.getElementById("posting-text");
const saveResumeBtn = document.getElementById("save-resume");
const extractPostingBtn = document.getElementById("extract-posting");
const analyzeBtn = document.getElementById("analyze");
const clearLogsBtn = document.getElementById("clear-logs");
const statusEl = document.getElementById("status");
const resultCard = document.getElementById("result-card");
const overallEl = document.getElementById("overall");
const rowsEl = document.getElementById("rows");
const suggestionsEl = document.getElementById("suggestions");
const logsEl = document.getElementById("logs");

const MAX_LOG_LINES = 200;
const logLines = [];

function formatNow() {
  return new Date().toLocaleTimeString("zh-CN", { hour12: false });
}

function appendLog(level, message) {
  const line = `[${formatNow()}] [${level.toUpperCase()}] ${message}`;
  logLines.push(line);
  if (logLines.length > MAX_LOG_LINES) logLines.shift();
  logsEl.textContent = logLines.join("\n");
  logsEl.scrollTop = logsEl.scrollHeight;

  if (level === "error") console.error(line);
  else if (level === "warn") console.warn(line);
  else console.log(line);
}

function setStatus(message, level = "info") {
  statusEl.textContent = message;
  appendLog(level, message);
}

function parseErrorDetail(defaultMessage, responseBody, responseStatus) {
  if (responseStatus === 404) {
    return `${defaultMessage}: 接口不存在，请确认后端已更新并重启`;
  }
  if (responseBody?.detail) {
    return `${defaultMessage}: ${responseBody.detail}`;
  }
  return `${defaultMessage}: ${responseStatus}`;
}

function extractPostingTextInPage() {
  const headings = [
    "about the job",
    "overview",
    "responsibilities",
    "qualifications",
    "required qualifications",
    "preferred qualifications",
    "other requirements"
  ];
  const stopMarkers = [
    "about the company",
    "more jobs",
    "looking for talent",
    "linkedin corporation",
    "select language",
    "job search smarter with premium"
  ];

  function injectLineBreaksByMarkers(text, markers) {
    let output = text;
    for (const marker of markers) {
      const escaped = marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      output = output.replace(new RegExp(`\\b${escaped}\\b`, "gi"), `\n${marker}\n`);
    }
    return output;
  }

  function focusText(rawText) {
    const lines = injectLineBreaksByMarkers(rawText, [...headings, ...stopMarkers])
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
    if (!lines.length) return "";

    let start = 0;
    for (let i = 0; i < lines.length; i += 1) {
      const lowered = lines[i].toLowerCase();
      if (headings.some((heading) => lowered.includes(heading))) {
        start = i;
        break;
      }
    }

    let end = lines.length;
    for (let i = start; i < lines.length; i += 1) {
      const lowered = lines[i].toLowerCase();
      if (stopMarkers.some((marker) => lowered.includes(marker))) {
        end = i;
        break;
      }
    }

    const focused = lines.slice(start, end).join("\n").trim();
    const result = focused || lines.join("\n");
    return result.length > 12000 ? result.slice(0, 12000) : result;
  }

  const selectors = [
    "[data-test-job-description]",
    ".jobs-box__html-content",
    ".jobs-description__content",
    ".jobs-description-content__text",
    ".description",
    "main"
  ];

  for (const selector of selectors) {
    const node = document.querySelector(selector);
    if (node && node.textContent && node.textContent.trim().length > 120) {
      const focused = focusText(node.textContent.trim());
      if (focused.length > 120) return focused;
    }
  }

  return focusText((document.body?.innerText || "").trim());
}

async function loadPersistedInputs() {
  const saved = await chrome.storage.local.get(["resumeJson", "apiUrl"]);
  if (saved.resumeJson) resumeJsonInput.value = saved.resumeJson;
  apiUrlInput.value = saved.apiUrl || defaultEndpoint("analyze");
  appendLog("info", `当前分析接口: ${apiUrlInput.value}`);
}

async function saveInputs() {
  await chrome.storage.local.set({
    resumeJson: resumeJsonInput.value,
    apiUrl: apiUrlInput.value
  });
  setStatus("已保存配置");
}

function createResumeFormData(file) {
  const formData = new FormData();
  formData.append("file", file, file.name);
  return formData;
}

async function requestResumeParse(file, endpoint) {
  return fetch(endpoint, {
    method: "POST",
    body: createResumeFormData(file)
  });
}

async function parseResumeFileUpload() {
  const file = resumeFileInput.files?.[0];
  if (!file) {
    setStatus("请先选择 PDF 或 DOCX 文件", "warn");
    return;
  }

  if (!/\.(pdf|docx)$/i.test(file.name)) {
    setStatus("仅支持 PDF 或 DOCX", "warn");
    return;
  }

  setStatus("简历解析中...");

  const primaryEndpoint = buildEndpoint(apiUrlInput.value, "resume_parse");
  appendLog("info", `简历解析请求: ${primaryEndpoint}`);

  let endpoint = primaryEndpoint;
  let response = await requestResumeParse(file, endpoint);

  if (response.status === 404) {
    const fallbackEndpoint = defaultEndpoint("resume_parse");
    if (fallbackEndpoint !== primaryEndpoint) {
      appendLog("warn", `主解析接口返回404，回退到 ${fallbackEndpoint}`);
      endpoint = fallbackEndpoint;
      response = await requestResumeParse(file, endpoint);
    }
  }

  if (!response.ok) {
    let body = null;
    try {
      body = await response.json();
    } catch (_error) {
      // Keep empty body.
    }
    setStatus(parseErrorDetail("简历解析失败", body, response.status), "error");
    appendLog("error", `解析接口失败: ${endpoint}`);
    return;
  }

  const body = await response.json();
  resumeJsonInput.value = JSON.stringify(body.profile || {}, null, 2);
  await chrome.storage.local.set({
    resumeJson: resumeJsonInput.value
  });
  if (body.cache_hit) {
    appendLog("info", "后端简历解析缓存命中");
  }
  setStatus("简历解析完成，已填入 JSON");
}

function renderResult(report) {
  resultCard.hidden = false;
  overallEl.textContent = `总匹配度: ${report.overall_score}`;

  rowsEl.innerHTML = "";
  for (const row of report.rows || []) {
    const div = document.createElement("div");
    div.className = "row-item";
    div.innerHTML = `
      <div class="head">
        <strong>${row.requirement_text || row.requirement_id}</strong>
        <span class="verdict-${row.verdict}">${row.verdict}</span>
      </div>
      <div>confidence: ${row.confidence}</div>
      <div>evidence: ${(row.evidence || []).join("; ") || "(none)"}</div>
      <div>gap: ${row.gap_reason || "-"}</div>
    `;
    rowsEl.appendChild(div);
  }

  suggestionsEl.innerHTML = "";
  for (const item of report.suggestions || []) {
    const li = document.createElement("li");
    li.textContent = `[${item.priority}] ${item.message}`;
    suggestionsEl.appendChild(li);
  }
}

async function extractFromContentScript(tabId) {
  const response = await requestPostingTextFromContentScript({
    tabId,
    sendMessage: async (targetTabId, message) => chrome.tabs.sendMessage(targetTabId, message),
    injectScript: async (targetTabId) =>
      chrome.scripting.executeScript({
        target: { tabId: targetTabId },
        files: ["content.js"]
      })
  });
  if (response?.postingText?.trim()) return focusPostingText(response.postingText.trim());
  throw new Error("content script returned empty posting text");
}

async function extractViaScripting(tabId) {
  const result = await chrome.scripting.executeScript({
    target: { tabId },
    func: extractPostingTextInPage
  });

  const text = result?.[0]?.result;
  if (typeof text === "string" && text.trim()) return focusPostingText(text.trim());
  throw new Error("scripting extraction returned empty posting text");
}

async function extractFromActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    setStatus("未找到活动标签页", "error");
    return;
  }

  try {
    const postingText = await extractFromContentScript(tab.id);
    postingTextInput.value = postingText;
    setStatus("已提取页面岗位描述");
    return;
  } catch (error) {
    appendLog("warn", `content script 提取失败，开始 fallback: ${error.message}`);
  }

  try {
    const postingText = await extractViaScripting(tab.id);
    postingTextInput.value = postingText;
    setStatus("已提取页面岗位描述（fallback）");
  } catch (error) {
    setStatus(`提取失败: ${error.message}`, "error");
  }
}

async function analyze() {
  let profile;
  try {
    profile = JSON.parse(resumeJsonInput.value);
  } catch (_error) {
    setStatus("简历 JSON 解析失败", "error");
    return;
  }

  const postingText = postingTextInput.value.trim();
  if (!postingText) {
    setStatus("岗位描述为空", "warn");
    return;
  }

  setStatus("分析中...");
  const analyzeEndpoint = buildEndpoint(apiUrlInput.value, "analyze");
  appendLog("info", `分析请求: ${analyzeEndpoint}`);

  const response = await fetch(analyzeEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile, posting_text: postingText })
  });

  if (!response.ok) {
    setStatus(`API 错误: ${response.status}`, "error");
    return;
  }

  const report = await response.json();
  renderResult(report);
  setStatus("分析完成");
}

saveResumeBtn.addEventListener("click", saveInputs);
parseResumeFileBtn.addEventListener("click", () => {
  parseResumeFileUpload().catch((error) => setStatus(`解析异常: ${error.message}`, "error"));
});
extractPostingBtn.addEventListener("click", () => {
  extractFromActiveTab().catch((error) => setStatus(`提取异常: ${error.message}`, "error"));
});
analyzeBtn.addEventListener("click", () => {
  analyze().catch((error) => setStatus(`分析异常: ${error.message}`, "error"));
});
clearLogsBtn.addEventListener("click", () => {
  logLines.length = 0;
  logsEl.textContent = "";
  appendLog("info", "日志已清空");
});

loadPersistedInputs().catch((error) => setStatus(`初始化异常: ${error.message}`, "error"));

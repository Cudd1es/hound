const apiUrlInput = document.getElementById("api-url");
const resumeJsonInput = document.getElementById("resume-json");
const postingTextInput = document.getElementById("posting-text");
const saveResumeBtn = document.getElementById("save-resume");
const extractPostingBtn = document.getElementById("extract-posting");
const analyzeBtn = document.getElementById("analyze");
const statusEl = document.getElementById("status");
const resultCard = document.getElementById("result-card");
const overallEl = document.getElementById("overall");
const rowsEl = document.getElementById("rows");
const suggestionsEl = document.getElementById("suggestions");

function setStatus(message) {
  statusEl.textContent = message;
}

async function loadPersistedInputs() {
  const saved = await chrome.storage.local.get(["resumeJson", "apiUrl"]);
  if (saved.resumeJson) resumeJsonInput.value = saved.resumeJson;
  if (saved.apiUrl) apiUrlInput.value = saved.apiUrl;
}

async function saveInputs() {
  await chrome.storage.local.set({
    resumeJson: resumeJsonInput.value,
    apiUrl: apiUrlInput.value
  });
  setStatus("已保存配置");
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

async function extractFromActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    setStatus("未找到活动标签页");
    return;
  }

  const response = await chrome.tabs.sendMessage(tab.id, { type: "hound-extract-posting" });
  if (response?.postingText) {
    postingTextInput.value = response.postingText;
    setStatus("已提取页面岗位描述");
  } else {
    setStatus("提取失败，请手动粘贴");
  }
}

async function analyze() {
  let profile;
  try {
    profile = JSON.parse(resumeJsonInput.value);
  } catch (_error) {
    setStatus("简历 JSON 解析失败");
    return;
  }

  const postingText = postingTextInput.value.trim();
  if (!postingText) {
    setStatus("岗位描述为空");
    return;
  }

  setStatus("分析中...");
  const response = await fetch(apiUrlInput.value, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile, posting_text: postingText })
  });

  if (!response.ok) {
    setStatus(`API 错误: ${response.status}`);
    return;
  }

  const report = await response.json();
  renderResult(report);
  setStatus("分析完成");
}

saveResumeBtn.addEventListener("click", saveInputs);
extractPostingBtn.addEventListener("click", () => {
  extractFromActiveTab().catch((error) => setStatus(`提取异常: ${error.message}`));
});
analyzeBtn.addEventListener("click", () => {
  analyze().catch((error) => setStatus(`分析异常: ${error.message}`));
});

loadPersistedInputs().catch((error) => setStatus(`初始化异常: ${error.message}`));

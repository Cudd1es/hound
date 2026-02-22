const FOCUS_HEADINGS = [
  "about the job",
  "overview",
  "responsibilities",
  "qualifications",
  "required qualifications",
  "preferred qualifications",
  "other requirements"
];
const FOCUS_STOP_MARKERS = [
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

function focusPostingText(rawText) {
  if (typeof rawText !== "string") return "";
  const lines = injectLineBreaksByMarkers(rawText, [...FOCUS_HEADINGS, ...FOCUS_STOP_MARKERS])
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  if (!lines.length) return "";

  let startIndex = 0;
  for (let i = 0; i < lines.length; i += 1) {
    const lowered = lines[i].toLowerCase();
    if (FOCUS_HEADINGS.some((heading) => lowered.includes(heading))) {
      startIndex = i;
      break;
    }
  }

  let endIndex = lines.length;
  for (let i = startIndex; i < lines.length; i += 1) {
    const lowered = lines[i].toLowerCase();
    if (FOCUS_STOP_MARKERS.some((marker) => lowered.includes(marker))) {
      endIndex = i;
      break;
    }
  }

  const focused = lines.slice(startIndex, endIndex).join("\n").trim();
  const result = focused || lines.join("\n");
  return result.length > 12000 ? result.slice(0, 12000) : result;
}

function extractPostingText() {
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
      const focused = focusPostingText(node.textContent.trim());
      if (focused.length > 120) return focused;
    }
  }

  return focusPostingText((document.body?.innerText || "").trim());
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "hound-extract-posting") {
    sendResponse({ postingText: extractPostingText() });
  }
});

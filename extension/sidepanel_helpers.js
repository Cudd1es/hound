const DEFAULT_API_ORIGIN = "http://127.0.0.1:8000";
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
const FOCUS_NOISE_KEYWORDS = [
  "reactivate premium",
  "premium",
  "easy apply",
  "followers",
  "questions? visit our help center"
];

function splitPath(pathname) {
  return pathname
    .split("/")
    .map((segment) => segment.trim())
    .filter((segment) => segment.length > 0);
}

function normalizePrefix(pathname) {
  const segments = splitPath(pathname);
  if (segments.length > 0 && segments[segments.length - 1].toLowerCase() === "analyze") {
    return segments.slice(0, -1);
  }
  return segments;
}

function targetSegments(kind) {
  if (kind === "resume_parse") return ["resume", "parse"];
  return ["analyze"];
}

export function buildEndpoint(apiUrl, kind) {
  const fallback = new URL(DEFAULT_API_ORIGIN);
  fallback.pathname = `/${targetSegments(kind).join("/")}`;

  try {
    const url = new URL((apiUrl || "").trim());
    const prefix = normalizePrefix(url.pathname);

    url.pathname = `/${[...prefix, ...targetSegments(kind)].join("/")}`;
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch (_error) {
    return fallback.toString();
  }
}

export function defaultEndpoint(kind) {
  return buildEndpoint(DEFAULT_API_ORIGIN, kind);
}

function injectLineBreaksByMarkers(text, markers) {
  let output = text;
  for (const marker of markers) {
    const escaped = marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    output = output.replace(new RegExp(`\\b${escaped}\\b`, "gi"), `\n${marker}\n`);
  }
  return output;
}

function normalizeLines(text) {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

export function focusPostingText(rawText) {
  if (typeof rawText !== "string") return "";
  const text = injectLineBreaksByMarkers(rawText, [...FOCUS_HEADINGS, ...FOCUS_STOP_MARKERS]);
  const lines = normalizeLines(text);
  if (!lines.length) return "";

  let startIndex = 0;
  for (let idx = 0; idx < lines.length; idx += 1) {
    const lowered = lines[idx].toLowerCase();
    if (FOCUS_HEADINGS.some((heading) => lowered.includes(heading))) {
      startIndex = idx;
      break;
    }
  }

  let endIndex = lines.length;
  for (let idx = startIndex; idx < lines.length; idx += 1) {
    const lowered = lines[idx].toLowerCase();
    if (FOCUS_STOP_MARKERS.some((marker) => lowered.includes(marker))) {
      endIndex = idx;
      break;
    }
  }

  const focused = [];
  for (const line of lines.slice(startIndex, endIndex)) {
    const lowered = line.toLowerCase();
    if (FOCUS_NOISE_KEYWORDS.some((keyword) => lowered.includes(keyword))) continue;
    focused.push(line);
  }

  const merged = focused.join("\n").trim();
  const result = merged || lines.join("\n");
  return result.length > 12000 ? result.slice(0, 12000) : result;
}

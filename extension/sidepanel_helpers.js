const DEFAULT_API_ORIGIN = "http://127.0.0.1:8000";

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

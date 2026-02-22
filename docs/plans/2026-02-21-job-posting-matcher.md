# Job Posting Matcher Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a privacy-aware Chrome extension plus local CLI that scores fit between a resume profile and a job posting, including per-requirement pass/fail evidence and actionable suggestions.

**Architecture:** Use a shared TypeScript core package for parsing, requirement normalization, scoring, and report generation. Add one Chrome extension frontend (side panel + content script) and one local CLI wrapper that reuses the same analysis engine for batch runs. LLM is optional but supported through a provider adapter with strict JSON schema output.

**Tech Stack:** TypeScript, Node.js, Chrome Extension Manifest V3, React (side panel), Vitest, Zod, Playwright (optional E2E), OpenAI-compatible API (optional)

---

## Approach Options (Brainstorming Output)

### Option A (Recommended): Hybrid shared-core architecture
- Chrome extension for in-browser extraction + instant analysis.
- Local CLI for offline/batch analysis and reproducible reports.
- One shared engine (`packages/core`) to avoid duplicate logic.
- Tradeoff: Slightly higher initial setup cost, best long-term maintainability.

### Option B: Extension-only
- Fastest path to MVP in browser.
- No CLI, all analysis tied to live page context.
- Tradeoff: Harder to batch compare many jobs and harder to automate in CI.

### Option C: Local desktop/web app only
- Strongest control and observability.
- Manual copy/paste or URL ingestion needed.
- Tradeoff: Loses seamless “browse and analyze now” user experience.

Recommendation: Start with Option A and ship in slices: core engine -> extension MVP -> CLI wrapper.

## Scope (MVP)

- Input: one resume profile (structured JSON) + one job posting text.
- Output:
  - Overall match score (0-100).
  - Requirement-level table (`met` / `partial` / `not_met` / `unknown`).
  - Evidence per row (resume bullet, skill, years, or missing proof).
  - Suggestions grouped by priority (`high`, `medium`, `low`).
- Extraction:
  - Content script gets visible posting content.
  - Fallback manual paste in side panel.
- Non-goals for MVP:
  - Auto-apply workflows.
  - ATS keyword gaming.
  - Multi-language semantic parsing beyond Chinese/English basics.

## Data Contracts

Use Zod schemas in shared core:

```ts
// packages/core/src/schema.ts
export const RequirementSchema = z.object({
  id: z.string(),
  text: z.string(),
  category: z.enum(["must", "preferred", "responsibility", "other"]),
  weight: z.number().min(0).max(1),
});

export const MatchRowSchema = z.object({
  requirementId: z.string(),
  verdict: z.enum(["met", "partial", "not_met", "unknown"]),
  confidence: z.number().min(0).max(1),
  evidence: z.array(z.string()),
  gapReason: z.string().optional(),
});
```

## Task 1: Scaffold Monorepo and Tooling

**Files:**
- Create: `package.json`
- Create: `tsconfig.base.json`
- Create: `vitest.workspace.ts`
- Create: `packages/core/package.json`
- Create: `apps/extension/package.json`
- Create: `apps/cli/package.json`
- Test: `packages/core/src/__tests__/sanity.test.ts`

**Step 1: Write the failing test**

```ts
// packages/core/src/__tests__/sanity.test.ts
import { describe, it, expect } from "vitest";
import { version } from "../version";

describe("core sanity", () => {
  it("exports version string", () => {
    expect(version).toMatch(/^0\./);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test --workspace @hound/core`
Expected: FAIL with module/file not found.

**Step 3: Write minimal implementation**

```ts
// packages/core/src/version.ts
export const version = "0.1.0";
```

**Step 4: Run test to verify it passes**

Run: `npm run test --workspace @hound/core`
Expected: PASS with `1 passed`.

**Step 5: Commit**

```bash
git add package.json tsconfig.base.json vitest.workspace.ts packages/core apps/extension apps/cli
git commit -m "chore: scaffold monorepo for core extension and cli"
```

## Task 2: Resume Profile Schema + Loader

**Files:**
- Create: `packages/core/src/schema.ts`
- Create: `packages/core/src/resume/loadResumeProfile.ts`
- Test: `packages/core/src/__tests__/loadResumeProfile.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { loadResumeProfile } from "../resume/loadResumeProfile";

describe("loadResumeProfile", () => {
  it("normalizes resume skills and experiences", () => {
    const profile = loadResumeProfile({
      basics: { name: "A" },
      skills: ["TypeScript", "React"],
      experiences: [{ title: "Engineer", years: 3 }],
    });
    expect(profile.skills).toContain("typescript");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test --workspace @hound/core -- loadResumeProfile`
Expected: FAIL with function/schema missing.

**Step 3: Write minimal implementation**

```ts
export function loadResumeProfile(input: any) {
  return {
    ...input,
    skills: (input.skills ?? []).map((s: string) => s.toLowerCase()),
  };
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test --workspace @hound/core -- loadResumeProfile`
Expected: PASS.

**Step 5: Commit**

```bash
git add packages/core/src/schema.ts packages/core/src/resume/loadResumeProfile.ts packages/core/src/__tests__/loadResumeProfile.test.ts
git commit -m "feat(core): add resume schema and normalization loader"
```

## Task 3: Job Requirement Extraction (Rule-Based MVP + LLM Hook)

**Files:**
- Create: `packages/core/src/requirements/extractRequirements.ts`
- Create: `packages/core/src/requirements/llmProvider.ts`
- Test: `packages/core/src/__tests__/extractRequirements.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { extractRequirements } from "../requirements/extractRequirements";

describe("extractRequirements", () => {
  it("extracts bullet requirements with category", async () => {
    const text = "Requirements:\n- 3+ years with React\n- Strong SQL";
    const rows = await extractRequirements(text);
    expect(rows.length).toBe(2);
    expect(rows[0].category).toBe("must");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test --workspace @hound/core -- extractRequirements`
Expected: FAIL with missing extractor.

**Step 3: Write minimal implementation**

```ts
export async function extractRequirements(text: string) {
  return text
    .split("\n")
    .filter((line) => line.trim().startsWith("-"))
    .map((line, i) => ({
      id: `req-${i + 1}`,
      text: line.replace(/^-/, "").trim(),
      category: "must" as const,
      weight: 1,
    }));
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test --workspace @hound/core -- extractRequirements`
Expected: PASS.

**Step 5: Commit**

```bash
git add packages/core/src/requirements packages/core/src/__tests__/extractRequirements.test.ts
git commit -m "feat(core): implement requirement extraction with provider hook"
```

## Task 4: Matching Engine and Scoring

**Files:**
- Create: `packages/core/src/match/scoreRequirement.ts`
- Create: `packages/core/src/match/generateReport.ts`
- Test: `packages/core/src/__tests__/generateReport.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { generateReport } from "../match/generateReport";

describe("generateReport", () => {
  it("returns overall score and requirement rows", () => {
    const report = generateReport(
      { skills: ["react", "sql"] },
      [{ id: "r1", text: "React", category: "must", weight: 1 }]
    );
    expect(report.overallScore).toBeGreaterThan(0);
    expect(report.rows[0].verdict).toBe("met");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test --workspace @hound/core -- generateReport`
Expected: FAIL with missing generator.

**Step 3: Write minimal implementation**

```ts
export function generateReport(profile: any, requirements: any[]) {
  const rows = requirements.map((r) => {
    const matched = profile.skills?.some((s: string) =>
      r.text.toLowerCase().includes(s)
    );
    return {
      requirementId: r.id,
      verdict: matched ? "met" : "not_met",
      confidence: matched ? 0.8 : 0.6,
      evidence: matched ? ["skill match"] : [],
    };
  });
  const overallScore = Math.round(
    (rows.filter((r) => r.verdict === "met").length / Math.max(rows.length, 1)) * 100
  );
  return { overallScore, rows };
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test --workspace @hound/core -- generateReport`
Expected: PASS.

**Step 5: Commit**

```bash
git add packages/core/src/match packages/core/src/__tests__/generateReport.test.ts
git commit -m "feat(core): add requirement scoring and report generation"
```

## Task 5: Suggestion Engine

**Files:**
- Create: `packages/core/src/suggestions/generateSuggestions.ts`
- Test: `packages/core/src/__tests__/generateSuggestions.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { generateSuggestions } from "../suggestions/generateSuggestions";

describe("generateSuggestions", () => {
  it("prioritizes missing must-have requirements", () => {
    const result = generateSuggestions([
      { requirementId: "r1", verdict: "not_met", confidence: 0.9, evidence: [] },
    ]);
    expect(result[0].priority).toBe("high");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test --workspace @hound/core -- generateSuggestions`
Expected: FAIL.

**Step 3: Write minimal implementation**

```ts
export function generateSuggestions(rows: any[]) {
  return rows
    .filter((r) => r.verdict === "not_met" || r.verdict === "partial")
    .map((r) => ({
      priority: "high",
      message: `Add evidence for ${r.requirementId} in resume bullets.`,
    }));
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test --workspace @hound/core -- generateSuggestions`
Expected: PASS.

**Step 5: Commit**

```bash
git add packages/core/src/suggestions packages/core/src/__tests__/generateSuggestions.test.ts
git commit -m "feat(core): add actionable suggestion generation"
```

## Task 6: Chrome Extension (Content Script + Side Panel)

**Files:**
- Create: `apps/extension/manifest.json`
- Create: `apps/extension/src/content/extractPosting.ts`
- Create: `apps/extension/src/content/index.ts`
- Create: `apps/extension/src/sidepanel/App.tsx`
- Create: `apps/extension/src/background/index.ts`
- Test: `apps/extension/src/__tests__/extractPosting.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { extractPostingText } from "../content/extractPosting";

describe("extractPostingText", () => {
  it("extracts section text from job detail container", () => {
    document.body.innerHTML = `<div class="description">React and SQL required</div>`;
    expect(extractPostingText()).toContain("React");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test --workspace @hound/extension -- extractPosting`
Expected: FAIL.

**Step 3: Write minimal implementation**

```ts
export function extractPostingText() {
  const node =
    document.querySelector(".description") ||
    document.querySelector("[data-test-job-description]") ||
    document.body;
  return node?.textContent?.trim() ?? "";
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test --workspace @hound/extension -- extractPosting`
Expected: PASS.

**Step 5: Commit**

```bash
git add apps/extension
git commit -m "feat(extension): add posting extraction and side panel shell"
```

## Task 7: Local CLI Wrapper

**Files:**
- Create: `apps/cli/src/index.ts`
- Create: `apps/cli/src/runAnalysis.ts`
- Test: `apps/cli/src/__tests__/runAnalysis.test.ts`

**Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { runAnalysis } from "../runAnalysis";

describe("runAnalysis", () => {
  it("returns report with score", async () => {
    const report = await runAnalysis({
      resumePath: "fixtures/resume.json",
      postingPath: "fixtures/posting.txt",
    });
    expect(report.overallScore).toBeTypeOf("number");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm run test --workspace @hound/cli -- runAnalysis`
Expected: FAIL.

**Step 3: Write minimal implementation**

```ts
export async function runAnalysis(_: { resumePath: string; postingPath: string }) {
  return { overallScore: 0, rows: [], suggestions: [] };
}
```

**Step 4: Run test to verify it passes**

Run: `npm run test --workspace @hound/cli -- runAnalysis`
Expected: PASS.

**Step 5: Commit**

```bash
git add apps/cli
git commit -m "feat(cli): add local analysis command wrapper"
```

## Task 8: End-to-End Verification and Docs

**Files:**
- Create: `docs/usage/extension.md`
- Create: `docs/usage/cli.md`
- Create: `docs/fixtures/sample-resume.json`
- Create: `docs/fixtures/sample-posting.txt`
- Modify: `README.md`

**Step 1: Write the failing test/check**

```md
Manual check list:
1) Load unpacked extension in Chrome.
2) Open a LinkedIn job page.
3) Open side panel and click Analyze.
4) Verify score + requirement rows + suggestions render.
5) Run CLI with sample files and compare JSON output shape.
```

**Step 2: Run check to verify it fails before docs/setup**

Run: `npm run lint && npm run test`
Expected: FAIL if scripts/docs links are missing.

**Step 3: Write minimal implementation**

- Add scripts in root `package.json`:
  - `test`, `lint`, `build`, `build:extension`, `analyze:cli`
- Document setup and API key flow.

**Step 4: Run verification to confirm passing state**

Run: `npm run test && npm run build`
Expected: PASS for all packages and build artifacts generated.

**Step 5: Commit**

```bash
git add README.md docs package.json
git commit -m "docs: add usage guide and verification checklist"
```

## Error Handling Strategy

- If posting extraction returns empty text, UI prompts manual paste input.
- If LLM provider fails, fallback to deterministic rule parser and mark confidence lower.
- If schema validation fails, show actionable UI error with raw field names.
- If API key missing, show setup panel instead of hard failure.

## Testing Strategy

- Unit: schema validation, requirement extractor, scoring, suggestions.
- Integration: full `analyze(posting, resume)` happy path and fallback path.
- Extension smoke test: one fixture HTML from LinkedIn-like layout.
- CLI snapshot test: stable JSON report fields.

## Milestones (Execution Order)

1. `core` package complete and fully tested.
2. Extension can extract posting and render first real report.
3. CLI outputs JSON report with same schema.
4. Docs + verification complete; ready for code review.

## Open Product Decisions (answer before implementation starts)

1. Match verdict levels keep 4 states (`met`, `partial`, `not_met`, `unknown`) or simplify to 3?
2. Resume source for MVP:
   - A) JSON profile form in extension
   - B) Upload PDF/Docx and parse
   - C) Paste plain text only
3. LLM default mode:
   - A) Optional (recommended) with rule-based fallback
   - B) Always-on model call
   - C) Fully local deterministic only

# Current Architecture & Flow / 当前架构与流程

## 中文

### 架构图（核心组件）

```mermaid
graph TD
  U["用户 / User"] --> E["Chrome Extension Side Panel"]
  E --> CS["Content Script"]
  E --> SC["Scripting Fallback"]
  E --> API["FastAPI Backend"]

  API --> RP["/resume/parse"]
  API --> AN["/analyze"]

  RP --> CACHE["Resume Cache (hash-keyed, multi-entry)"]
  RP --> PARSER["Resume Parser (PDF/DOCX text extraction)"]
  PARSER --> RUNTIME["LLM Runtime Factory"]

  AN --> REQ["Requirements Extraction"]
  AN --> MATCH["Matching + Scoring"]
  AN --> SUG["Suggestion Generator"]

  REQ --> RUNTIME
  MATCH --> RUNTIME
  RUNTIME --> OLLAMA["Ollama Provider"]
  RUNTIME --> OPENAI["OpenAI-Compatible Provider"]
  REQ --> RULE_REQ["Rule Fallback"]
  MATCH --> RULE_MATCH["Rule Fallback"]
```

### 流程图（一次分析请求）

```mermaid
flowchart TD
  A["上传简历 + 打开 JD 页面"] --> B["扩展提取 JD 文本"]
  B --> C{"Content Script 成功?"}
  C -->|Yes| D["focusPostingText 清洗/聚焦"]
  C -->|No| E["chrome.scripting fallback"]
  E --> D

  A --> F["POST /resume/parse"]
  F --> G{"后端缓存命中?"}
  G -->|Yes| H["返回缓存 profile + cache_hit=true"]
  G -->|No| I["解析 PDF/DOCX 文本"]
  I --> J{"LLM provider 可用?"}
  J -->|Yes| K["LLM 语义抽取 profile"]
  J -->|No| L["规则抽取（技能/摘要）"]
  K --> M["写入内容哈希缓存"]
  L --> M

  D --> N["POST /analyze"]
  H --> N
  M --> N
  N --> O["JD requirements 抽取（先清洗后抽取）"]
  O --> P{"LLM requirements 可用?"}
  P -->|Yes| Q["LLM requirements"]
  P -->|No| R["规则 bullet requirements"]

  Q --> S["matching"]
  R --> S
  S --> T{"LLM matching 开启?"}
  T -->|Yes| U["LLM requirement-level match"]
  T -->|No| V["规则匹配"]
  U --> W["维度降权评分 + 建议"]
  V --> W
  W --> X["返回 overall_score / rows / suggestions"]
```

### 核心机制细节

- 统一 LLM 入口：`backend/src/hound_core/llm_runtime.py`。
- Provider 选择：`HOUND_LLM_PROVIDER=rule|ollama|openai|auto`。
- 统一 API 形态：OpenAI-compatible chat/completions；本地 LLM（如 Ollama）也走 API。
- 简历缓存：按文件内容 SHA-256；多条目（默认 8，`HOUND_RESUME_CACHE_MAX_ENTRIES`）。
- JD 聚焦：优先 `Overview/Responsibilities/Qualifications`，截断 `About the company/More jobs` 等噪声段。
- 评分口径：`technical=1.0`、`soft=0.45`、`compliance=0.2`、`other=0.65`；`unknown` 不计分母。

---

## English

### Architecture Diagram (Core Components)

```mermaid
graph TD
  U["User"] --> E["Chrome Extension Side Panel"]
  E --> CS["Content Script"]
  E --> SC["Scripting Fallback"]
  E --> API["FastAPI Backend"]

  API --> RP["/resume/parse"]
  API --> AN["/analyze"]

  RP --> CACHE["Resume Cache (hash-keyed, multi-entry)"]
  RP --> PARSER["Resume Parser (PDF/DOCX text extraction)"]
  PARSER --> RUNTIME["LLM Runtime Factory"]

  AN --> REQ["Requirements Extraction"]
  AN --> MATCH["Matching + Scoring"]
  AN --> SUG["Suggestion Generator"]

  REQ --> RUNTIME
  MATCH --> RUNTIME
  RUNTIME --> OLLAMA["Ollama Provider"]
  RUNTIME --> OPENAI["OpenAI-Compatible Provider"]
  REQ --> RULE_REQ["Rule Fallback"]
  MATCH --> RULE_MATCH["Rule Fallback"]
```

### Flow Diagram (Single End-to-End Analysis)

```mermaid
flowchart TD
  A["Upload resume + open JD page"] --> B["Extension extracts JD text"]
  B --> C{"Content script works?"}
  C -->|Yes| D["focusPostingText cleanup/focus"]
  C -->|No| E["chrome.scripting fallback"]
  E --> D

  A --> F["POST /resume/parse"]
  F --> G{"Backend cache hit?"}
  G -->|Yes| H["Return cached profile + cache_hit=true"]
  G -->|No| I["Parse PDF/DOCX text"]
  I --> J{"LLM provider available?"}
  J -->|Yes| K["LLM semantic profile extraction"]
  J -->|No| L["Rule-based extraction"]
  K --> M["Persist hash-keyed cache"]
  L --> M

  D --> N["POST /analyze"]
  H --> N
  M --> N
  N --> O["Extract JD requirements (sanitized input)"]
  O --> P{"LLM requirements available?"}
  P -->|Yes| Q["LLM requirements"]
  P -->|No| R["Rule bullet requirements"]

  Q --> S["Matching"]
  R --> S
  S --> T{"LLM matching enabled?"}
  T -->|Yes| U["LLM requirement-level matching"]
  T -->|No| V["Rule matching"]
  U --> W["Dimension-weighted scoring + suggestions"]
  V --> W
  W --> X["Return overall_score / rows / suggestions"]
```

### Core Mechanisms

- Unified LLM runtime entry: `backend/src/hound_core/llm_runtime.py`.
- Provider switch: `HOUND_LLM_PROVIDER=rule|ollama|openai|auto`.
- Unified API style: OpenAI-compatible chat/completions; local LLM APIs are treated similarly.
- Resume cache: SHA-256 content hash, bounded multi-entry cache (`HOUND_RESUME_CACHE_MAX_ENTRIES`, default 8).
- JD focus extraction: keeps requirement sections and removes company/promotional noise sections.
- Scoring: dimension multiplier (`technical=1.0`, `soft=0.45`, `compliance=0.2`, `other=0.65`); `unknown` excluded from denominator.

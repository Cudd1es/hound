# Project Review Report / 项目开发审查报告 (2026-02-22)

## 中文

### 审查范围
- 后端：API、简历解析、JD 抽取、匹配评分、LLM provider 架构
- 前端扩展：页面抓取、JD 聚焦清洗、调用 API 流程
- 配置与文档：LLM 配置入口、运行时缓存策略、测试覆盖

### 验证基线
- Python：`PYTHONPATH=backend/src conda run -n hound pytest backend/tests -q` -> 31 passed
- Extension：`node --test tests/endpoint-builder.test.mjs` -> 4 passed
- JS 语法检查：`node --check content.js sidepanel.js sidepanel_helpers.js`

### 本轮已修复项
- P1：运行时缓存文件未忽略
  - 已在 `.gitignore` 增加 `logs/*.json`、`extension.crx`、`extension.pem`、`.idea/`
- P2：扩展端简历缓存误命中风险
  - 已移除扩展端本地元数据缓存短路，统一依赖后端内容哈希缓存
- P2：后端仅单条简历缓存
  - 已改为多条目缓存（默认 8 条，可配置 `HOUND_RESUME_CACHE_MAX_ENTRIES`）
- LLM 接口分散
  - 已新增统一配置/工厂模块 `llm_runtime.py`
  - 已支持 `openai` 与 `ollama` 两类 API provider

### 当前架构结论
- 系统稳定性：良好（回归测试全部通过）
- 可配置性：显著提升（统一 LLM 配置入口，旧变量兼容）
- 风险等级：中低

### 剩余建议（非阻断）
1. 为缓存文件增加 file lock（并发进程写入场景更稳）。
2. 增加端到端 LinkedIn DOM fixture 测试，避免页面结构变化回归。
3. 为 OpenAI provider 增加超时重试与限流退避策略。

---

## English

### Scope
- Backend: API, resume parsing, JD extraction, matching/scoring, LLM provider architecture
- Extension: page extraction, JD-focused cleaning, API orchestration
- Config/docs: unified LLM configuration, runtime cache strategy, test coverage

### Validation Baseline
- Python: `PYTHONPATH=backend/src conda run -n hound pytest backend/tests -q` -> 31 passed
- Extension: `node --test tests/endpoint-builder.test.mjs` -> 4 passed
- JS syntax: `node --check content.js sidepanel.js sidepanel_helpers.js`

### Fixed in this iteration
- P1: runtime cache files not ignored
  - Added `.gitignore` rules for `logs/*.json`, `extension.crx`, `extension.pem`, `.idea/`
- P2: extension resume cache false-hit risk
  - Removed extension-side metadata cache shortcut; now relying on backend content-hash cache
- P2: backend cache only supported one resume
  - Migrated to bounded multi-entry cache (default 8 via `HOUND_RESUME_CACHE_MAX_ENTRIES`)
- Scattered LLM interface
  - Added unified runtime config/factory module `llm_runtime.py`
  - Added support for both `openai` and `ollama` API providers

### Current Assessment
- Stability: good (all regression tests green)
- Configurability: significantly improved (single LLM config surface + legacy compatibility)
- Risk level: medium-low

### Remaining Recommendations (non-blocking)
1. Add file locking for cache writes (better multi-process safety).
2. Add end-to-end fixture tests with real LinkedIn-like DOM snapshots.
3. Add retry/backoff and throttling controls for OpenAI provider.

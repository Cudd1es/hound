# LLM Configuration & Provider Guide / LLM 配置与 Provider 指南

## 中文

### 1) 统一配置入口（推荐）

统一配置入口在：
- 脚本入口：`/Users/ansel/coding/codex_proj/hound/scripts/start_backend.sh`
- 运行时配置与 provider 选择：`/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_runtime.py`

核心环境变量：
- `HOUND_LLM_PROVIDER=rule|ollama|openai|auto`
- `HOUND_LLM_BASE_URL`
- `HOUND_LLM_MODEL`
- `HOUND_LLM_API_KEY`
- `HOUND_LLM_TIMEOUT_SECONDS`
- `HOUND_LLM_MATCHING=auto|true|false`

兼容旧变量（仍支持）：
- `HOUND_OLLAMA_URL`, `HOUND_OLLAMA_MODEL`, `HOUND_OLLAMA_TIMEOUT_SECONDS`
- `HOUND_OPENAI_BASE_URL`, `HOUND_OPENAI_MODEL`, `HOUND_OPENAI_API_KEY`

### 2) 快速切换示例

OpenAI API：
```bash
HOUND_LLM_PROVIDER=openai \
HOUND_LLM_BASE_URL=https://api.openai.com/v1 \
HOUND_LLM_MODEL=gpt-4o-mini \
HOUND_LLM_API_KEY=YOUR_KEY \
./scripts/start_backend.sh
```

本地 LLM API（如 Ollama）：
```bash
HOUND_LLM_PROVIDER=ollama \
HOUND_LLM_BASE_URL=http://127.0.0.1:11434 \
HOUND_LLM_MODEL=gemma3:27b \
./scripts/start_backend.sh
```

关闭匹配阶段 LLM（提速）：
```bash
HOUND_LLM_MATCHING=false ./scripts/start_backend.sh
```

### 3) 代码中 Provider 是如何选择的

统一工厂：
- `create_requirement_provider()`
- `create_resume_profile_provider()`
- `create_match_provider()`

定义位置：
- `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_runtime.py`

调用位置：
- 简历解析：`/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/resume_parser.py`
- JD requirement 抽取：`/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/requirements.py`
- 匹配：`/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/matching.py`

### 4) Provider 实现位置

- Ollama：`/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_ollama.py`
- OpenAI/兼容 API：`/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_openai.py`
- 协议定义：`/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_provider.py`

---

## English

### 1) Unified Configuration Entry Points (Recommended)

The unified LLM configuration lives in:
- Startup script: `/Users/ansel/coding/codex_proj/hound/scripts/start_backend.sh`
- Runtime config and provider factory: `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_runtime.py`

Primary env vars:
- `HOUND_LLM_PROVIDER=rule|ollama|openai|auto`
- `HOUND_LLM_BASE_URL`
- `HOUND_LLM_MODEL`
- `HOUND_LLM_API_KEY`
- `HOUND_LLM_TIMEOUT_SECONDS`
- `HOUND_LLM_MATCHING=auto|true|false`

Legacy env vars are still supported:
- `HOUND_OLLAMA_URL`, `HOUND_OLLAMA_MODEL`, `HOUND_OLLAMA_TIMEOUT_SECONDS`
- `HOUND_OPENAI_BASE_URL`, `HOUND_OPENAI_MODEL`, `HOUND_OPENAI_API_KEY`

### 2) Quick Switching Examples

OpenAI API:
```bash
HOUND_LLM_PROVIDER=openai \
HOUND_LLM_BASE_URL=https://api.openai.com/v1 \
HOUND_LLM_MODEL=gpt-4o-mini \
HOUND_LLM_API_KEY=YOUR_KEY \
./scripts/start_backend.sh
```

Local LLM API (e.g., Ollama):
```bash
HOUND_LLM_PROVIDER=ollama \
HOUND_LLM_BASE_URL=http://127.0.0.1:11434 \
HOUND_LLM_MODEL=gemma3:27b \
./scripts/start_backend.sh
```

Disable LLM matching (speed up while keeping LLM extraction):
```bash
HOUND_LLM_MATCHING=false ./scripts/start_backend.sh
```

### 3) How Provider Selection Works in Code

Unified factories:
- `create_requirement_provider()`
- `create_resume_profile_provider()`
- `create_match_provider()`

Defined in:
- `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_runtime.py`

Used in:
- Resume parsing: `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/resume_parser.py`
- Requirement extraction: `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/requirements.py`
- Matching: `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/matching.py`

### 4) Provider Implementations

- Ollama: `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_ollama.py`
- OpenAI/compatible API: `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_openai.py`
- Protocols: `/Users/ansel/coding/codex_proj/hound/backend/src/hound_core/llm_provider.py`

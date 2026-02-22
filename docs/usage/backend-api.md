# Backend API 使用说明

## 启动

```bash
PYTHONPATH=backend/src conda run -n hound uvicorn hound_core.api:app --host 127.0.0.1 --port 8000
```

或使用快捷脚本（默认启用 Ollama，并自动开启 LLM 匹配）：

```bash
./scripts/start_backend.sh
```

## 接口

### GET /health

返回：

```json
{"status": "ok"}
```

### POST /analyze

请求体：

```json
{
  "profile": {
    "skills": ["python", "fastapi", "sql"],
    "experiences": []
  },
  "posting_text": "Requirements:\n- Python\n- Kubernetes"
}
```

返回体（示例）：

```json
{
  "overall_score": 50,
  "rows": [
    {
      "requirement_id": "req-1",
      "verdict": "met",
      "confidence": 0.85,
      "evidence": ["Matched skill: python"],
      "gap_reason": null,
      "category": "must",
      "dimension": "technical",
      "requirement_text": "Python"
    }
  ],
  "suggestions": [
    {
      "priority": "high",
      "message": "For req-2: add measurable evidence for 'Kubernetes' in resume bullets."
    }
  ]
}
```

### POST /resume/parse

`multipart/form-data` 上传 `file` 字段，支持 `.pdf` 和 `.docx`。

请求示例（curl）：

```bash
curl -X POST http://127.0.0.1:8000/resume/parse \
  -F "file=@/absolute/path/to/resume.docx"
```

返回体（示例）：

```json
{
  "profile": {
    "skills": ["python", "fastapi", "sql"],
    "experiences": [],
    "semantic_summary": "Backend engineer focused on production Python services and reliability.",
    "strengths": ["automation", "service reliability"],
    "experience_signals": ["reduced migration effort"],
    "source": "resume.docx"
  },
  "extracted_text": "Software Engineer with Python FastAPI and SQL experience",
  "cache_hit": false
}
```

## 日志

- 后端日志文件默认写到：`logs/hound.log`
- 可通过环境变量覆盖路径：`HOUND_LOG_PATH=/your/path/hound.log`

## LLM 配置

- `HOUND_LLM_PROVIDER=rule`：纯规则解析（默认）
- `HOUND_LLM_PROVIDER=ollama`：启用 Ollama
- `HOUND_LLM_MATCHING=auto|true|false`：匹配阶段是否启用 LLM（默认 `auto`，跟随 `HOUND_LLM_PROVIDER`）
- `HOUND_OLLAMA_URL`：Ollama 地址（默认 `http://127.0.0.1:11434`）
- `HOUND_OLLAMA_MODEL`：模型名（默认 `gemma3:27b`）
- `HOUND_OLLAMA_TIMEOUT_SECONDS`：模型请求超时秒数（默认 `120`）
- `HOUND_RESUME_CACHE_PATH`：简历解析缓存文件路径（默认 `logs/resume-parse-cache.json`）

如果你希望提速，可保持 `HOUND_LLM_PROVIDER=ollama`，但关闭匹配阶段 LLM：

```bash
HOUND_LLM_MATCHING=false ./scripts/start_backend.sh
```

## 评分口径（当前）

- Requirement 会带 `dimension`：`technical` / `soft` / `compliance` / `other`。
- 总分计算会对维度做降权：`technical=1.0`、`soft=0.45`、`compliance=0.2`、`other=0.65`。
- `unknown` 不计入分母（避免信息缺失项把总分直接拉低）。

## 简历缓存行为

- `/resume/parse` 会按文件内容哈希缓存最近一次解析结果。
- 上传同一份简历时将直接返回缓存（`cache_hit=true`），不会重复触发 LLM 解析。
- 上传新简历时缓存会被替换（符合“只在用户上传新简历时重新解析”的策略）。

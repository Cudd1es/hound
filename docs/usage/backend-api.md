# Backend API 使用说明

## 启动

```bash
PYTHONPATH=backend/src conda run -n hound uvicorn hound_core.api:app --host 127.0.0.1 --port 8000
```

或使用快捷脚本（默认启用 Ollama）：

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
    "source": "resume.docx"
  },
  "extracted_text": "Software Engineer with Python FastAPI and SQL experience"
}
```

## 日志

- 后端日志文件默认写到：`logs/hound.log`
- 可通过环境变量覆盖路径：`HOUND_LOG_PATH=/your/path/hound.log`

## LLM 配置

- `HOUND_LLM_PROVIDER=rule`：纯规则解析（默认）
- `HOUND_LLM_PROVIDER=ollama`：启用 Ollama
- `HOUND_OLLAMA_URL`：Ollama 地址（默认 `http://127.0.0.1:11434`）
- `HOUND_OLLAMA_MODEL`：模型名（默认 `gemma3-27b`）
- `HOUND_OLLAMA_TIMEOUT_SECONDS`：模型请求超时秒数（默认 `120`）

# Backend API 使用说明

## 启动

```bash
PYTHONPATH=backend/src conda run -n hound uvicorn hound_core.api:app --host 127.0.0.1 --port 8000
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

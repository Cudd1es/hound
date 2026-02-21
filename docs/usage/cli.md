# CLI 使用说明

## 命令

```bash
PYTHONPATH=backend/src conda run -n hound python -m hound_core.cli \
  --resume <resume.json> \
  --posting <posting.txt> \
  [--output <report.json>]
```

## 参数

- `--resume`: 简历 JSON 文件路径
- `--posting`: job posting 纯文本文件路径
- `--output`: 可选，输出 JSON 报告文件路径

## 示例

```bash
PYTHONPATH=backend/src conda run -n hound python -m hound_core.cli \
  --resume docs/fixtures/sample-resume.json \
  --posting docs/fixtures/sample-posting.txt \
  --output /tmp/hound-report.json
```

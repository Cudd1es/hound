# Hound

基于 Option A 的实现：
- Python 后端核心分析引擎（抽取要求、匹配评分、建议生成）
- 本地 FastAPI 服务（供 Chrome 插件调用）
- 本地 CLI（批量或脚本化分析）
- Chrome MV3 插件（边看 job posting 边分析）
- 简历解析缓存（同一文件不重复 LLM 解析）与 JD 聚焦提取（优先职责/要求区段）

## 1. 环境

本项目测试和运行默认使用 conda 环境 `hound`。

```bash
conda env list
```

如果不存在：

```bash
conda create -y -n hound python=3.11 pytest fastapi uvicorn httpx
conda install -y -n hound -c conda-forge python-docx pypdf
```

## 2. 运行测试

```bash
conda run -n hound pytest backend/tests -q
```

## 3. 启动本地 API

```bash
PYTHONPATH=backend/src conda run -n hound uvicorn hound_core.api:app --host 127.0.0.1 --port 8000
```

快捷启动（默认启用 Ollama + `gemma3:27b`，并自动启用 LLM 匹配）：

```bash
./scripts/start_backend.sh
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 4. 使用 CLI

```bash
PYTHONPATH=backend/src conda run -n hound python -m hound_core.cli \
  --resume docs/fixtures/sample-resume.json \
  --posting docs/fixtures/sample-posting.txt
```

## 5. 加载 Chrome 插件

1. 打开 Chrome `chrome://extensions`
2. 打开「开发者模式」
3. 选择「加载已解压的扩展程序」
4. 目录选择 `extension/`
5. 打开任意 job posting 页面，点击扩展图标打开侧边栏
6. 在侧边栏中：
   - 可上传 PDF/DOCX 并点击「解析简历文件」自动填充简历 JSON
   - 可点击「从当前页面提取」自动抓取 posting
   - 填写/保存简历 JSON
   - 点击「开始分析」调用本地 API
   - 可查看「运行日志」定位接口路径和提取异常

## 6. Logging

- 插件侧边栏内置运行日志（请求 URL、提取回退、错误详情）。
- 后端日志默认写入 `logs/hound.log`。

## 7. Ollama LLM 模式

- 默认规则解析（不开 LLM）：`HOUND_LLM_PROVIDER=rule`
- 启用 Ollama：`HOUND_LLM_PROVIDER=ollama`
- 匹配阶段是否启用 LLM：`HOUND_LLM_MATCHING=auto|true|false`（默认 `auto`）
- 默认 Ollama 地址：`http://127.0.0.1:11434`
- 默认模型：`gemma3:27b`

如果你本地模型名不同，启动前覆盖：

```bash
HOUND_OLLAMA_MODEL=gemma3:27b ./scripts/start_backend.sh
```

只想保留 LLM 提取（简历/JD），但加速匹配阶段：

```bash
HOUND_LLM_MATCHING=false ./scripts/start_backend.sh
```

详细见：`docs/usage/extension.md`

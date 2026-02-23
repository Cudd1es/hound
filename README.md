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

## 7. Secret 防护

- 仓库内禁止跟踪 `*.pem` / `*.key` / `*.p12` / `*.pfx`。
- `scripts/secret_scan.sh` 提供三种扫描：
  - `staged`：扫描暂存区（用于 pre-commit）
  - `repo`：扫描当前仓库 tracked 文件
  - `history`：扫描历史中是否还存在 `extension.pem` 或 private key 片段

启用本地 git pre-commit hook（推荐）：

```bash
git config core.hooksPath .githooks
```

手动扫描：

```bash
bash scripts/secret_scan.sh all
```

可选：若你本机安装了 `pre-commit`，也可使用 `.pre-commit-config.yaml`。

## 8. 统一 LLM 配置

- Provider：`HOUND_LLM_PROVIDER=rule|ollama|openai|auto`
- Base URL：`HOUND_LLM_BASE_URL`
- Model：`HOUND_LLM_MODEL`
- API Key：`HOUND_LLM_API_KEY`
- Timeout：`HOUND_LLM_TIMEOUT_SECONDS`
- 匹配开关：`HOUND_LLM_MATCHING=auto|true|false`

示例（OpenAI API）：

```bash
HOUND_LLM_PROVIDER=openai \
HOUND_LLM_BASE_URL=https://api.openai.com/v1 \
HOUND_LLM_MODEL=gpt-4o-mini \
HOUND_LLM_API_KEY=YOUR_KEY \
./scripts/start_backend.sh
```

示例（本地 LLM API，如 Ollama）：

```bash
HOUND_LLM_PROVIDER=ollama \
HOUND_LLM_BASE_URL=http://127.0.0.1:11434 \
HOUND_LLM_MODEL=gemma3:27b \
./scripts/start_backend.sh
```

仅关闭 LLM 匹配以提速（保留 LLM 抽取）：

```bash
HOUND_LLM_MATCHING=false ./scripts/start_backend.sh
```

详细见：
- `docs/usage/llm-config-and-provider-guide.md`（中英双语，统一 LLM 配置）
- `docs/architecture/current-architecture-and-flow.md`（中英双语，架构图与流程图）
- `docs/usage/extension.md`

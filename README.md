# Hound

基于 Option A 的实现：
- Python 后端核心分析引擎（抽取要求、匹配评分、建议生成）
- 本地 FastAPI 服务（供 Chrome 插件调用）
- 本地 CLI（批量或脚本化分析）
- Chrome MV3 插件（边看 job posting 边分析）

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

详细见：`docs/usage/extension.md`

# Chrome 插件使用说明

插件目录：`extension/`

## 功能

- 从当前页面提取岗位描述（content script）
- 上传 PDF/DOCX 简历并自动生成简历 JSON
- 编辑并保存简历 JSON（chrome.storage.local）
- 调用本地 API（支持填写 `.../analyze` 或 base URL）
- 渲染总分、逐条匹配结论和建议
- 侧边栏内置运行日志，方便排查请求与提取错误
- JD 提取会优先聚焦 `Overview/Responsibilities/Qualifications` 并自动剔除 `About the company/More jobs` 等噪声区段
- 简历解析支持本地缓存：同一文件（名称+大小+修改时间一致）将直接复用上次解析 JSON

## 本地联调步骤

1. 先启动后端 API：

```bash
PYTHONPATH=backend/src conda run -n hound uvicorn hound_core.api:app --host 127.0.0.1 --port 8000
```

推荐使用快捷脚本（默认启用 Ollama + `gemma3:27b`）：

```bash
./scripts/start_backend.sh
```

2. 加载扩展：
   - 打开 `chrome://extensions`
   - 开启开发者模式
   - 点击「加载已解压的扩展程序」，选择 `extension/`

3. 打开 job posting 页面：
   - 点击扩展图标打开 side panel
   - 如需导入简历，选择 PDF/DOCX 后点击「解析简历文件」
   - 点击「从当前页面提取」
   - 点击「开始分析」

## 常见问题

- `API 错误: 404/500`：确认 API 是否运行，并检查 side panel 的「运行日志」里请求 URL。
- `简历解析失败: 接口不存在`：通常是后端版本过旧或 API 前缀路径配置不一致，重启后端并确认接口存在 `POST /resume/parse`。
- `提取异常: Could not establish connection...`：插件已加 fallback；若仍失败，请刷新当前 job posting 页面后重试。
- 提取文本过短：页面结构可能不匹配，手动粘贴 posting 即可
- JSON 解析失败：检查简历输入是否为合法 JSON
- 如需强制重新解析同一简历，可修改简历文件（更新时间）后重新上传

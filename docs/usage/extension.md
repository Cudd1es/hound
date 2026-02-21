# Chrome 插件使用说明

插件目录：`extension/`

## 功能

- 从当前页面提取岗位描述（content script）
- 编辑并保存简历 JSON（chrome.storage.local）
- 调用本地 API `/analyze`
- 渲染总分、逐条匹配结论和建议

## 本地联调步骤

1. 先启动后端 API：

```bash
PYTHONPATH=backend/src conda run -n hound uvicorn hound_core.api:app --host 127.0.0.1 --port 8000
```

2. 加载扩展：
   - 打开 `chrome://extensions`
   - 开启开发者模式
   - 点击「加载已解压的扩展程序」，选择 `extension/`

3. 打开 job posting 页面：
   - 点击扩展图标打开 side panel
   - 点击「从当前页面提取」
   - 点击「开始分析」

## 常见问题

- `API 错误: 404/500`：确认 API 是否运行、URL 是否是 `http://127.0.0.1:8000/analyze`
- 提取文本过短：页面结构可能不匹配，手动粘贴 posting 即可
- JSON 解析失败：检查简历输入是否为合法 JSON

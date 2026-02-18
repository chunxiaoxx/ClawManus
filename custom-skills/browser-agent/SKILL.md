# Browser Agent - 深度浏览器自动化

对标 BrowserUseTool，具备智能元素定位、自动填表、错误恢复等能力。

## 核心功能

### 1. 智能元素定位
- get_by_role - 通过角色定位
- get_by_label - 通过标签定位
- get_by_placeholder - 通过占位符定位
- get_by_text - 通过文本定位
- CSS/XPath - 备用定位

### 2. 自动填表
```python
fields = [
    FormField("username", "username", SelectorType.NAME, "john"),
    FormField("password", "password", SelectorType.NAME, "secret"),
]
await agent.fill_form("https://example.com/login", fields)
```

### 3. 动作序列
```python
actions = [
    ActionStep("click", "#submit"),
    ActionStep("wait", "#result", "visible"),
    ActionStep("screenshot", "", None, "result.png"),
]
await agent.execute_actions(actions)
```

### 4. 数据提取
```python
data = await agent.extract_data({
    "title": "h1",
    "price": ".price",
    "description": ".desc",
})
```

## 使用示例

```python
from skills.browser_agent.browser_agent import BrowserAgent, FormField, ActionStep

agent = BrowserAgent(headless=True)
await agent.initialize()

# 填表
await agent.fill_form("https://example.com", [
    FormField("email", "email", SelectorType.NAME, "test@example.com"),
])

# 执行动作
await agent.execute_actions([
    ActionStep("click", "button[type=submit]"),
    ActionStep("wait", "#success", "visible"),
    ActionStep("screenshot", "", None, "success.png"),
])

await agent.close()
```

# Task Engine - 终极任务引擎

## 功能

- **智能任务规划**: 自动拆解复杂任务
- **23+ 工具支持**: search, browse, code, exec, memory, github, etc.
- **进度追踪**: 实时显示执行进度
- **Telegram 推送**: 任务状态实时通知
- **验证+重试**: 每步验证，失败自动重试

## 工具列表 (23个)

| 类别 | 工具 |
|------|------|
| 搜索 | search, web_search |
| 浏览器 | browse, screenshot, fill_form |
| 代码 | code, python, javascript |
| 执行 | exec, bash |
| 文件 | read, write, append |
| Git | github, git |
| 记忆 | memory, remember |
| 报告 | report, summarize |
| 通知 | notify, telegram |
| 工具 | calc, convert |

## 使用方式

```bash
# 直接运行
python3 skills/task-engine/ultimate_engine.py "你的任务"

# 或使用脚本
./scripts/run-task.sh "你的任务"
```

## 代码调用

```python
from skills.task_engine.ultimate_engine import run_task
import asyncio

result = asyncio.run(run_task("帮我调研 AI"))
```

## 测试结果

```
🚀 开始任务: 帮我调研 AI 发展趋势
📦 可用工具: 23 个
📋 规划完成: 4 个步骤

✅ 任务完成!
  完成: 4/4 步骤
  耗时: 0秒
```

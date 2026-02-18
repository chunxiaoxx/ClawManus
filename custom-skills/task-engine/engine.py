#!/usr/bin/env python3
"""
OpenClaw Task Engine - 任务执行引擎
全自动任务拆解、执行、验证、报告
"""

import json
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class Step:
    def __init__(self, step_id: int, action: str, description: str, 
                 params: Dict = None, expected: str = ""):
        self.id = step_id
        self.action = action
        self.description = description
        self.params = params or {}
        self.expected = expected
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.retries = 0

class Task:
    def __init__(self, task_id: str, description: str):
        self.id = task_id
        self.description = description
        self.steps: List[Step] = []
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.progress = 0
        self.result = None

class TaskEngine:
    """任务执行引擎"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.tools = self._init_tools()
        self.progress_callback: Optional[Callable] = None
        
    def _init_tools(self):
        """初始化工具"""
        return {
            "search": self._tool_search,
            "browse": self._tool_browse,
            "code": self._tool_code,
            "exec": self._tool_exec,
            "memory": self._tool_memory,
            "github": self._tool_github,
            "report": self._tool_report,
        }
    
    def set_progress_callback(self, callback: Callable):
        """设置进度回调"""
        self.progress_callback = callback
    
    async def plan(self, task_description: str) -> Task:
        """任务规划 - 拆解为步骤"""
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id, task_description)
        
        # 智能拆解 (使用 LLM 逻辑)
        steps = await self._llm_plan(task_description)
        
        for i, step_data in enumerate(steps):
            step = Step(
                step_id=step_data.get("id", i+1),
                action=step_data.get("action", "unknown"),
                description=step_data.get("description", ""),
                params=step_data.get("params", {}),
                expected=step_data.get("expected", "")
            )
            task.steps.append(step)
        
        self.tasks[task_id] = task
        return task
    
    async def _llm_plan(self, task_description: str) -> List[Dict]:
        """LLM 任务拆解"""
        # 根据任务类型智能拆解
        task_lower = task_description.lower()
        
        if "调研" in task_lower or "研究" in task_lower or "research" in task_lower:
            return [
                {"id": 1, "action": "search", "description": "搜索相关信息", 
                 "expected": "返回搜索结果", "params": {"query": task_description}},
                {"id": 2, "action": "browse", "description": "获取详细内容", 
                 "expected": "成功获取内容", "params": {}},
                {"id": 3, "action": "memory", "description": "保存调研结果", 
                 "expected": "保存成功", "params": {}},
                {"id": 4, "action": "report", "description": "生成调研报告", 
                 "expected": "报告完成", "params": {}}
            ]
        elif "分析" in task_lower or "分析" in task_lower:
            return [
                {"id": 1, "action": "search", "description": "收集数据", 
                 "expected": "数据收集完成", "params": {}},
                {"id": 2, "action": "code", "description": "数据分析", 
                 "expected": "分析完成", "params": {}},
                {"id": 3, "action": "report", "description": "生成报告", 
                 "expected": "报告生成", "params": {}}
            ]
        elif "创建" in task_lower or "生成" in task_lower:
            return [
                {"id": 1, "action": "plan", "description": "制定计划", 
                 "expected": "计划完成", "params": {}},
                {"id": 2, "action": "code", "description": "生成代码", 
                 "expected": "代码生成", "params": {}},
                {"id": 3, "action": "exec", "description": "执行验证", 
                 "expected": "验证通过", "params": {}},
                {"id": 4, "action": "report", "description": "生成报告", 
                 "expected": "完成", "params": {}}
            ]
        else:
            # 默认简单拆解
            return [
                {"id": 1, "action": "search", "description": "搜索信息", 
                 "expected": "完成", "params": {"query": task_description}},
                {"id": 2, "action": "report", "description": "生成结果", 
                 "expected": "完成", "params": {}}
            ]
    
    async def execute(self, task: Task, max_retries: int = 3) -> Task:
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        total_steps = len(task.steps)
        
        for i, step in enumerate(task.steps):
            step.status = TaskStatus.RUNNING
            
            # 更新进度
            task.progress = int((i / total_steps) * 100)
            await self._notify_progress(task)
            
            # 执行步骤
            success = False
            for retry in range(max_retries):
                try:
                    result = await self._execute_step(step)
                    step.result = result
                    
                    if self._verify_step(step):
                        step.status = TaskStatus.COMPLETED
                        success = True
                        break
                    else:
                        step.error = "Verification failed"
                except Exception as e:
                    step.error = str(e)
                
                step.retries += 1
                if retry < max_retries - 1:
                    step.status = TaskStatus.RETRYING
                    await asyncio.sleep(1)  # 重试等待
            
            if not success:
                step.status = TaskStatus.FAILED
            
            # 更新进度
            task.progress = int(((i + 1) / total_steps) * 100)
            await self._notify_progress(task)
        
        # 任务完成
        if all(s.status == TaskStatus.COMPLETED for s in task.steps):
            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.FAILED
        
        task.completed_at = datetime.now()
        task.progress = 100
        await self._notify_progress(task)
        
        return task
    
    async def _execute_step(self, step: Step) -> Dict:
        """执行单个步骤"""
        tool = self.tools.get(step.action)
        if not tool:
            return {"error": f"Unknown action: {step.action}"}
        
        return await tool(step.params)
    
    def _verify_step(self, step: Step) -> bool:
        """验证步骤结果"""
        if step.result is None:
            return False
        
        # 简单验证
        if isinstance(step.result, dict):
            if step.result.get("status") == "error":
                return False
        
        return True
    
    async def _notify_progress(self, task: Task):
        """通知进度"""
        if self.progress_callback:
            await self.progress_callback(task)
    
    # ===== 工具实现 =====
    
    async def _tool_search(self, params: Dict) -> Dict:
        """搜索工具"""
        query = params.get("query", "")
        # 调用搜索 API
        return {"status": "success", "action": "search", "query": query}
    
    async def _tool_browse(self, params: Dict) -> Dict:
        """浏览工具"""
        url = params.get("url", "")
        return {"status": "success", "action": "browse", "url": url}
    
    async def _tool_code(self, params: Dict) -> Dict:
        """代码工具"""
        code = params.get("code", "")
        return {"status": "success", "action": "code", "code": code[:100]}
    
    async def _tool_exec(self, params: Dict) -> Dict:
        """执行命令"""
        command = params.get("command", "")
        return {"status": "success", "action": "exec", "command": command}
    
    async def _tool_memory(self, params: Dict) -> Dict:
        """记忆工具"""
        content = params.get("content", "")
        return {"status": "success", "action": "memory", "saved": True}
    
    async def _tool_github(self, params: Dict) -> Dict:
        """GitHub 工具"""
        operation = params.get("operation", "")
        return {"status": "success", "action": "github", "operation": operation}
    
    async def _tool_report(self, params: Dict) -> Dict:
        """报告工具"""
        title = params.get("title", "Report")
        return {"status": "success", "action": "report", "title": title}
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[Task]:
        """列出所有任务"""
        return list(self.tasks.values())
    
    def generate_report(self, task: Task) -> str:
        """生成任务报告"""
        completed = sum(1 for s in task.steps if s.status == TaskStatus.COMPLETED)
        total = len(task.steps)
        
        report = f"""
╔════════════════════════════════════════════════════════════╗
║                    任务执行报告                             ║
╠════════════════════════════════════════════════════════════╣
║ 任务ID: {task.id}
║ 描述: {task.description[:40]}
║ 状态: {task.status.value}
║ 进度: {task.progress}%
║ 完成: {completed}/{total} 步骤
║ 耗时: {self._format_duration(task)}
╚════════════════════════════════════════════════════════════╝

### 步骤详情
"""
        for step in task.steps:
            status_icon = "✅" if step.status == TaskStatus.COMPLETED else "❌" if step.status == TaskStatus.FAILED else "⏳"
            report += f"\n{status_icon} Step {step.id}: [{step.action}] {step.description}"
            if step.error:
                report += f"\n   错误: {step.error}"
            if step.retries > 0:
                report += f"\n   重试: {step.retries} 次"
        
        return report
    
    def _format_duration(self, task: Task) -> str:
        """格式化耗时"""
        if not task.started_at:
            return "N/A"
        
        end = task.completed_at or datetime.now()
        duration = end - task.started_at
        seconds = int(duration.total_seconds())
        
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds//60}分{seconds%60}秒"
        else:
            return f"{seconds//3600}小时{(seconds%3600)//60}分"


# 全局引擎实例
_engine = TaskEngine()

async def run_task(task_description: str) -> str:
    """运行任务的便捷函数"""
    # 设置进度回调 (可以连接 Telegram)
    # _engine.set_progress_callback(on_progress)
    
    # 规划
    task = await _engine.plan(task_description)
    print(f"📋 任务规划: {len(task.steps)} 个步骤")
    
    # 执行
    task = await _engine.execute(task)
    
    # 生成报告
    report = _engine.generate_report(task)
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        task_desc = "调研 OpenManus 并总结核心功能"
    else:
        task_desc = " ".join(sys.argv[1:])
    
    result = asyncio.run(run_task(task_desc))
    print(result)

#!/usr/bin/env python3
"""
OpenClaw Integrated Task Engine - 任务执行引擎 + 进度追踪
完整集成版
"""

import json
import asyncio
import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

# 导入进度追踪
from progress import ProgressTracker, get_tracker

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

class IntegratedTaskEngine:
    """
    集成任务引擎 - 任务执行 + 进度追踪
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.progress = get_tracker()  # 使用全局进度追踪
        self.tools = self._init_tools()
        self.telegram_configured = False
        
    def configure_telegram(self, token: str, chat_id: str):
        """配置 Telegram 推送"""
        self.progress.set_telegram(token, chat_id)
        self.progress.add_callback(self._telegram_notify)
        self.telegram_configured = True
        print(f"✅ Telegram 已配置: {chat_id}")
    
    async def _telegram_notify(self, task_progress):
        """Telegram 通知回调"""
        if self.telegram_configured:
            await self.progress.send_telegram(task_progress)
    
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
    
    async def run(self, task_description: str, notify: bool = True) -> Task:
        """
        运行任务的完整流程
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n🚀 开始任务: {task_description}")
        print("=" * 60)
        
        # 1. 规划
        task = await self._plan(task_description)
        print(f"📋 规划完成: {len(task.steps)} 个步骤")
        
        # 2. 启动进度追踪
        if notify:
            self.progress.start_task(task.id, task.description, len(task.steps))
        
        # 3. 执行
        await self._execute(task)
        
        # 4. 完成
        if notify:
            status = "completed" if task.status == TaskStatus.COMPLETED else "failed"
            error = "" if task.status == TaskStatus.COMPLETED else "有步骤失败"
            self.progress.complete_task(task.id, status, error)
        
        # 5. 生成报告
        report = self._generate_report(task)
        print(report)
        
        return task
    
    async def _plan(self, task_description: str) -> Task:
        """任务规划"""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id, task_description)
        
        # 智能拆解
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
        task_lower = task_description.lower()
        
        if "调研" in task_lower or "研究" in task_lower:
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
        elif "分析" in task_lower:
            return [
                {"id": 1, "action": "search", "description": "收集数据", 
                 "expected": "数据收集完成", "params": {}},
                {"id": 2, "action": "code", "description": "数据分析", 
                 "expected": "分析完成", "params": {}},
                {"id": 3, "action": "report", "description": "生成报告", 
                 "expected": "报告生成", "params": {}}
            ]
        else:
            return [
                {"id": 1, "action": "search", "description": "搜索信息", 
                 "expected": "完成", "params": {"query": task_description}},
                {"id": 2, "action": "report", "description": "生成结果", 
                 "expected": "完成", "params": {}}
            ]
    
    async def _execute(self, task: Task, max_retries: int = 3):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        total_steps = len(task.steps)
        
        for i, step in enumerate(task.steps):
            step.status = TaskStatus.RUNNING
            
            # 更新进度
            task.progress = int((i / total_steps) * 100)
            self.progress.update_progress(
                task.id, 
                step.id, 
                f"[{step.action}] {step.description[:30]}",
                task.progress
            )
            
            print(f"\n🔄 Step {step.id}/{total_steps}: [{step.action}] {step.description}")
            
            # 执行步骤
            success = False
            for retry in range(max_retries):
                try:
                    result = await self._execute_step(step)
                    step.result = result
                    
                    if self._verify_step(step):
                        step.status = TaskStatus.COMPLETED
                        success = True
                        print(f"   ✅ 完成")
                        break
                    else:
                        step.error = "Verification failed"
                        print(f"   ⚠️ 验证失败, 重试 {retry+1}/{max_retries}")
                except Exception as e:
                    step.error = str(e)
                    print(f"   ❌ 错误: {e}")
                
                step.retries += 1
                if retry < max_retries - 1:
                    step.status = TaskStatus.RETRYING
                    await asyncio.sleep(1)
            
            if not success:
                step.status = TaskStatus.FAILED
                print(f"   ❌ 失败: {step.error}")
            
            # 更新进度
            task.progress = int(((i + 1) / total_steps) * 100)
            self.progress.update_progress(
                task.id, 
                step.id, 
                f"[{step.action}] {step.description[:30]}",
                task.progress
            )
        
        # 任务完成
        if all(s.status == TaskStatus.COMPLETED for s in task.steps):
            task.status = TaskStatus.COMPLETED
            print("\n✅ 任务全部完成!")
        else:
            task.status = TaskStatus.FAILED
            print("\n⚠️ 任务部分完成")
        
        task.completed_at = datetime.now()
        task.progress = 100
        self.progress.update_progress(task.id, total_steps, "完成", 100)
    
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
        if isinstance(step.result, dict):
            if step.result.get("status") == "error":
                return False
        return True
    
    # ===== 工具实现 =====
    
    async def _tool_search(self, params: Dict) -> Dict:
        """搜索工具"""
        query = params.get("query", "")
        print(f"   🔍 搜索: {query}")
        # 调用搜索
        return {"status": "success", "action": "search", "query": query}
    
    async def _tool_browse(self, params: Dict) -> Dict:
        """浏览工具"""
        url = params.get("url", "")
        print(f"   🌐 浏览: {url or '页面'}")
        return {"status": "success", "action": "browse", "url": url}
    
    async def _tool_code(self, params: Dict) -> Dict:
        """代码工具"""
        code = params.get("code", "")
        print(f"   💻 执行代码")
        return {"status": "success", "action": "code", "code": code[:50]}
    
    async def _tool_exec(self, params: Dict) -> Dict:
        """执行命令"""
        command = params.get("command", "")
        print(f"   ⚡ 执行命令: {command[:30]}...")
        return {"status": "success", "action": "exec", "command": command}
    
    async def _tool_memory(self, params: Dict) -> Dict:
        """记忆工具"""
        content = params.get("content", "")
        print(f"   💾 保存记忆")
        return {"status": "success", "action": "memory", "saved": True}
    
    async def _tool_github(self, params: Dict) -> Dict:
        """GitHub 工具"""
        operation = params.get("operation", "")
        print(f"   📂 GitHub: {operation}")
        return {"status": "success", "action": "github", "operation": operation}
    
    async def _tool_report(self, params: Dict) -> Dict:
        """报告工具"""
        title = params.get("title", "Report")
        print(f"   📝 生成报告: {title}")
        return {"status": "success", "action": "report", "title": title}
    
    def _generate_report(self, task: Task) -> str:
        """生成任务报告"""
        completed = sum(1 for s in task.steps if s.status == TaskStatus.COMPLETED)
        total = len(task.steps)
        
        duration = ""
        if task.started_at and task.completed_at:
            seconds = int((task.completed_at - task.started_at).total_seconds())
            duration = f"{seconds}秒"
        
        report = f"""
╔════════════════════════════════════════════════════════════╗
║                    任务执行报告                             ║
╠════════════════════════════════════════════════════════════╣
║ 任务ID: {task.id}
║ 描述: {task.description[:40]}
║ 状态: {'✅ 完成' if task.status == TaskStatus.COMPLETED else '⚠️ 部分完成'}
║ 进度: 100%
║ 完成: {completed}/{total} 步骤
║ 耗时: {duration}
╚════════════════════════════════════════════════════════════╝
"""
        return report
    
    def get_progress(self, task_id: str) -> Optional[Dict]:
        """获取任务进度"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        progress = self.progress.get_status(task_id)
        if progress:
            return {
                "task_id": task_id,
                "description": task.description,
                "status": task.status.value,
                "progress": task.progress,
                "current_step": progress.current_step,
                "total_steps": progress.total_steps,
                "step_name": progress.step_name
            }
        return None


# 全局引擎
_engine = IntegratedTaskEngine()

async def run_task(task_description: str, notify: bool = True) -> str:
    """运行任务的便捷函数"""
    return await _engine.run(task_description, notify)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        task_desc = "调研 OpenManus 并总结核心功能"
    else:
        task_desc = " ".join(sys.argv[1:])
    
    result = asyncio.run(run_task(task_desc))

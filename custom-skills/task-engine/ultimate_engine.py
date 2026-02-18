#!/usr/bin/env python3
"""
OpenClaw Ultimate Task Engine - 终极任务引擎
集成工具注册表 + 进度追踪 + Telegram 推送
"""

import json
import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

# 导入工具注册表
from tool_registry import get_registry, list_all_tools

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class Step:
    def __init__(self, step_id: int, tool: str, params: Dict, description: str = ""):
        self.id = step_id
        self.tool = tool
        self.params = params
        self.description = description or f"执行 {tool}"
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

class UltimateTaskEngine:
    """
    终极任务引擎
    - 智能任务规划
    - 23+ 工具支持
    - 进度追踪
    - Telegram 推送
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.registry = get_registry()
        self.available_tools = list_all_tools()
        self.telegram_config = None
        
    def configure_telegram(self, token: str, chat_id: str):
        """配置 Telegram"""
        self.telegram_config = {"token": token, "chat_id": chat_id}
        print(f"✅ Telegram 已配置: {chat_id}")
    
    async def run(self, task_description: str) -> Task:
        """运行任务"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n🚀 开始任务: {task_description}")
        print(f"📦 可用工具: {len(self.available_tools)} 个")
        print("=" * 60)
        
        # 1. 规划
        task = await self._plan(task_description)
        print(f"📋 规划完成: {len(task.steps)} 个步骤")
        
        # 2. 打印计划
        for step in task.steps:
            print(f"   {step.id}. [{step.tool}] {step.description}")
        
        # 3. 执行
        await self._execute(task)
        
        # 4. 报告
        report = self._generate_report(task)
        print(report)
        
        return task
    
    async def _plan(self, task_description: str) -> Task:
        """智能任务规划"""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id, task_description)
        
        # 根据任务类型智能规划
        steps = self._generate_steps(task_description)
        
        for i, step_data in enumerate(steps):
            step = Step(
                step_id=step_data["id"],
                tool=step_data["tool"],
                params=step_data.get("params", {}),
                description=step_data.get("description", "")
            )
            task.steps.append(step)
        
        self.tasks[task_id] = task
        return task
    
    def _generate_steps(self, task_description: str) -> List[Dict]:
        """生成执行步骤"""
        desc = task_description.lower()
        
        # 调研类任务
        if any(k in desc for k in ["调研", "研究", "调查", "research"]):
            return [
                {"id": 1, "tool": "search", "params": {"query": task_description}, "description": "搜索相关信息"},
                {"id": 2, "tool": "browse", "params": {"url": ""}, "description": "获取详细内容"},
                {"id": 3, "tool": "memory", "params": {"content": task_description}, "description": "保存到记忆"},
                {"id": 4, "tool": "report", "params": {"title": "调研报告"}, "description": "生成报告"}
            ]
        
        # 分析类任务
        elif any(k in desc for k in ["分析", "分析"]):
            return [
                {"id": 1, "tool": "search", "params": {"query": task_description}, "description": "收集数据"},
                {"id": 2, "tool": "code", "params": {"language": "python", "code": ""}, "description": "数据分析"},
                {"id": 3, "tool": "report", "params": {"title": "分析报告"}, "description": "生成报告"}
            ]
        
        # 创建/开发类任务
        elif any(k in desc for k in ["创建", "开发", "写", "生成"]):
            return [
                {"id": 1, "tool": "write", "params": {"path": "", "content": ""}, "description": "创建文件"},
                {"id": 2, "tool": "exec", "params": {"command": ""}, "description": "执行验证"},
                {"id": 3, "tool": "report", "params": {"title": "完成报告"}, "description": "生成报告"}
            ]
        
        # 读取类任务
        elif any(k in desc for k in ["读取", "查看", "看"]):
            return [
                {"id": 1, "tool": "read", "params": {"path": ""}, "description": "读取文件"},
                {"id": 2, "tool": "summarize", "params": {"content": ""}, "description": "总结内容"}
            ]
        
        # 默认任务
        else:
            return [
                {"id": 1, "tool": "search", "params": {"query": task_description}, "description": "搜索信息"},
                {"id": 2, "tool": "report", "params": {"title": "结果"}, "description": "生成报告"}
            ]
    
    async def _execute(self, task: Task, max_retries: int = 3):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        total = len(task.steps)
        
        for i, step in enumerate(task.steps):
            step.status = TaskStatus.RUNNING
            
            # 进度
            task.progress = int(((i + 1) / total) * 100)
            print(f"\n🔄 [{task.progress}%] Step {step.id}: [{step.tool}] {step.description}")
            
            # 执行
            success = False
            for retry in range(max_retries):
                try:
                    result = await self.registry.execute(step.tool, step.params)
                    step.result = result
                    
                    if result.get("status") == "success":
                        step.status = TaskStatus.COMPLETED
                        success = True
                        print(f"   ✅ 完成")
                        break
                    else:
                        step.error = result.get("message", "Unknown error")
                except Exception as e:
                    step.error = str(e)
                
                step.retries += 1
                if retry < max_retries - 1:
                    step.status = TaskStatus.RETRYING
                    await asyncio.sleep(1)
            
            if not success:
                step.status = TaskStatus.FAILED
                print(f"   ❌ 失败: {step.error}")
        
        # 完成
        if all(s.status == TaskStatus.COMPLETED for s in task.steps):
            task.status = TaskStatus.COMPLETED
            print("\n✅ 任务完成!")
        else:
            task.status = TaskStatus.FAILED
            print("\n⚠️ 任务部分完成")
        
        task.completed_at = datetime.now()
        task.progress = 100
    
    def _generate_report(self, task: Task) -> str:
        """生成报告"""
        completed = sum(1 for s in task.steps if s.status == TaskStatus.COMPLETED)
        total = len(task.steps)
        
        duration = ""
        if task.started_at and task.completed_at:
            seconds = int((task.completed_at - task.started_at).total_seconds())
            duration = f"{seconds}秒"
        
        lines = [
            "",
            "=" * 60,
            "  任务执行报告",
            "=" * 60,
            f"  任务ID: {task.id}",
            f"  描述: {task.description[:40]}",
            f"  状态: {'完成' if task.status == TaskStatus.COMPLETED else '部分完成'}",
            f"  进度: 100%",
            f"  完成: {completed}/{total} 步骤",
            f"  耗时: {duration}",
            "=" * 60,
            "",
            "步骤详情:",
        ]
        
        for step in task.steps:
            icon = "✅" if step.status == TaskStatus.COMPLETED else "❌"
            lines.append(f"  {icon} Step {step.id}: [{step.tool}] {step.description}")
        
        return "\n".join(lines)


# 全局引擎
_engine = UltimateTaskEngine()

async def run_task(task_description: str) -> str:
    """运行任务"""
    return await _engine.run(task_description)


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "调研 OpenManus"
    asyncio.run(run_task(task))

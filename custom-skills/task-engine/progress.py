#!/usr/bin/env python3
"""
Progress Tracker - 进度追踪系统
带 Telegram 推送
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import json

@dataclass
class TaskProgress:
    """任务进度"""
    task_id: str
    description: str
    status: str  # pending, running, completed, failed
    progress: int = 0  # 0-100
    current_step: int = 0
    total_steps: int = 0
    step_name: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error: str = ""

class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskProgress] = {}
        self.callbacks: List[Callable] = []
        self.telegram_token = None
        self.telegram_chat_id = None
        
    def set_telegram(self, token: str, chat_id: str):
        """设置 Telegram"""
        self.telegram_token = token
        self.telegram_chat_id = chat_id
    
    def add_callback(self, callback: Callable):
        """添加回调"""
        self.callbacks.append(callback)
    
    def start_task(self, task_id: str, description: str, total_steps: int):
        """开始任务"""
        progress = TaskProgress(
            task_id=task_id,
            description=description,
            status="running",
            total_steps=total_steps
        )
        self.tasks[task_id] = progress
        self._notify(progress)
        
    def update_progress(self, task_id: str, step: int, step_name: str, progress: int):
        """更新进度"""
        if task_id in self.tasks:
            self.tasks[task_id].current_step = step
            self.tasks[task_id].step_name = step_name
            self.tasks[task_id].progress = progress
            self.tasks[task_id].updated_at = datetime.now()
            self._notify(self.tasks[task_id])
    
    def complete_task(self, task_id: str, status: str = "completed", error: str = ""):
        """完成任务"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].progress = 100
            self.tasks[task_id].error = error
            self.tasks[task_id].updated_at = datetime.now()
            self._notify(self.tasks[task_id])
    
    def _notify(self, progress: TaskProgress):
        """通知所有回调"""
        for callback in self.callbacks:
            try:
                callback(progress)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def get_status(self, task_id: str) -> Optional[TaskProgress]:
        """获取状态"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[TaskProgress]:
        """列出所有任务"""
        return list(self.tasks.values())
    
    def format_progress(self, progress: TaskProgress) -> str:
        """格式化进度消息"""
        icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌"
        }
        
        icon = icons.get(progress.status, "📊")
        
        bar_length = 20
        filled = int(bar_length * progress.progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        msg = f"""
{icon} *任务进度*

*{progress.description}*

📊 进度: `{progress.progress}%`
{bar}

🔢 Step {progress.current_step}/{progress.total_steps}: {progress.step_name}
"""
        if progress.error:
            msg += f"\n❌ 错误: {progress.error}"
        
        return msg
    
    async def send_telegram(self, progress: TaskProgress):
        """发送到 Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        import aiohttp
        
        message = self.format_progress(progress)
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=data)
        except Exception as e:
            print(f"Telegram send error: {e}")
    
    def save_state(self, path: str):
        """保存状态"""
        data = {
            task_id: {
                "task_id": p.task_id,
                "description": p.description,
                "status": p.status,
                "progress": p.progress,
                "current_step": p.current_step,
                "total_steps": p.total_steps,
                "step_name": p.step_name,
                "started_at": p.started_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
                "error": p.error,
            }
            for task_id, p in self.tasks.items()
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_state(self, path: str):
        """加载状态"""
        if not os.path.exists(path):
            return
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        for task_id, p in data.items():
            progress = TaskProgress(
                task_id=p["task_id"],
                description=p["description"],
                status=p["status"],
                progress=p["progress"],
                current_step=p["current_step"],
                total_steps=p["total_steps"],
                step_name=p["step_name"],
                error=p.get("error", ""),
            )
            progress.started_at = datetime.fromisoformat(p["started_at"])
            progress.updated_at = datetime.fromisoformat(p["updated_at"])
            self.tasks[task_id] = progress


# 全局实例
_tracker = ProgressTracker()

def get_tracker() -> ProgressTracker:
    """获取追踪器"""
    return _tracker


if __name__ == "__main__":
    # 测试
    tracker = ProgressTracker()
    
    tracker.start_task("test123", "测试任务", 4)
    tracker.update_progress("test123", 1, "搜索信息", 25)
    tracker.update_progress("test123", 2, "分析数据", 50)
    
    print(tracker.format_progress(tracker.get_status("test123")))
    
    tracker.complete_task("test123")
    print(tracker.format_progress(tracker.get_status("test123")))

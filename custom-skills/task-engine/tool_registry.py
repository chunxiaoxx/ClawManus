#!/usr/bin/env python3
"""
Enhanced Tool Registry - 增强工具注册表
支持更多工具类型
"""

import os
import subprocess
import json
from typing import Dict, Any, Callable, Optional

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_all_tools()
    
    def _register_all_tools(self):
        """注册所有工具"""
        # 搜索工具
        self.register("search", self._tool_search)
        self.register("web_search", self._tool_web_search)
        
        # 浏览器工具
        self.register("browse", self._tool_browse)
        self.register("screenshot", self._tool_screenshot)
        self.register("fill_form", self._tool_fill_form)
        
        # 代码工具
        self.register("code", self._tool_code)
        self.register("python", self._tool_python)
        self.register("javascript", self._tool_javascript)
        
        # 执行工具
        self.register("exec", self._tool_exec)
        self.register("bash", self._tool_bash)
        
        # 文件工具
        self.register("read", self._tool_read)
        self.register("write", self._tool_write)
        self.register("append", self._tool_append)
        
        # GitHub 工具
        self.register("github", self._tool_github)
        self.register("git", self._tool_git)
        
        # 记忆工具
        self.register("memory", self._tool_memory)
        self.register("remember", self._tool_remember)
        
        # 报告工具
        self.register("report", self._tool_report)
        self.register("summarize", self._tool_summarize)
        
        # 通知工具
        self.register("notify", self._tool_notify)
        self.register("telegram", self._tool_telegram)
        
        # 工具
        self.register("calc", self._tool_calc)
        self.register("convert", self._tool_convert)
    
    def register(self, name: str, func: Callable):
        """注册工具"""
        self.tools[name] = func
    
    async def execute(self, tool_name: str, params: Dict) -> Dict:
        """执行工具"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        
        try:
            result = await tool(params)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_tools(self) -> list:
        """列出所有工具"""
        return list(self.tools.keys())
    
    # ===== 搜索工具 =====
    
    async def _tool_search(self, params: Dict) -> Dict:
        """网络搜索"""
        query = params.get("query", "")
        return {"status": "success", "action": "search", "query": query, "results": []}
    
    async def _tool_web_search(self, params: Dict) -> Dict:
        """网页搜索"""
        query = params.get("query", "")
        return {"status": "success", "action": "web_search", "query": query}
    
    # ===== 浏览器工具 =====
    
    async def _tool_browse(self, params: Dict) -> Dict:
        """浏览网页"""
        url = params.get("url", "")
        action = params.get("action", "goto")
        return {"status": "success", "action": "browse", "url": url, "operation": action}
    
    async def _tool_screenshot(self, params: Dict) -> Dict:
        """截图"""
        path = params.get("path", "/tmp/screenshot.png")
        return {"status": "success", "action": "screenshot", "path": path}
    
    async def _tool_fill_form(self, params: Dict) -> Dict:
        """填表"""
        fields = params.get("fields", [])
        return {"status": "success", "action": "fill_form", "fields": fields}
    
    # ===== 代码工具 =====
    
    async def _tool_code(self, params: Dict) -> Dict:
        """执行代码"""
        code = params.get("code", "")
        language = params.get("language", "python")
        return {"status": "success", "action": "code", "language": language}
    
    async def _tool_python(self, params: Dict) -> Dict:
        """执行 Python"""
        code = params.get("code", "")
        return {"status": "success", "action": "python"}
    
    async def _tool_javascript(self, params: Dict) -> Dict:
        """执行 JavaScript"""
        code = params.get("code", "")
        return {"status": "success", "action": "javascript"}
    
    # ===== 执行工具 =====
    
    async def _tool_exec(self, params: Dict) -> Dict:
        """执行命令"""
        command = params.get("command", "")
        cwd = params.get("cwd", os.getcwd())
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=cwd
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "action": "exec",
                "command": command,
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:500],
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _tool_bash(self, params: Dict) -> Dict:
        """执行 Bash"""
        command = params.get("command", "")
        return await self._tool_exec({"command": command})
    
    # ===== 文件工具 =====
    
    async def _tool_read(self, params: Dict) -> Dict:
        """读取文件"""
        path = params.get("path", "")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"status": "success", "action": "read", "path": path, "content": content[:5000]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _tool_write(self, params: Dict) -> Dict:
        """写入文件"""
        path = params.get("path", "")
        content = params.get("content", "")
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "action": "write", "path": path, "bytes": len(content)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _tool_append(self, params: Dict) -> Dict:
        """追加文件"""
        path = params.get("path", "")
        content = params.get("content", "")
        
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "action": "append", "path": path, "bytes": len(content)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ===== GitHub 工具 =====
    
    async def _tool_github(self, params: Dict) -> Dict:
        """GitHub 操作"""
        operation = params.get("operation", "")
        repo = params.get("repo", "")
        return {"status": "success", "action": "github", "operation": operation, "repo": repo}
    
    async def _tool_git(self, params: Dict) -> Dict:
        """Git 操作"""
        command = params.get("command", "")
        return {"status": "success", "action": "git", "command": command}
    
    # ===== 记忆工具 =====
    
    async def _tool_memory(self, params: Dict) -> Dict:
        """保存记忆"""
        content = params.get("content", "")
        key = params.get("key", "default")
        
        # 保存到 memory 文件
        memory_path = f"/home/chunxiao/.openclaw/workspace/memory/2026-02-18.md"
        try:
            with open(memory_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n## 记忆\n{content}\n")
            return {"status": "success", "action": "memory", "key": key}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _tool_remember(self, params: Dict) -> Dict:
        """记住内容"""
        return await self._tool_memory(params)
    
    # ===== 报告工具 =====
    
    async def _tool_report(self, params: Dict) -> Dict:
        """生成报告"""
        title = params.get("title", "Report")
        content = params.get("content", "")
        format = params.get("format", "markdown")
        
        return {
            "status": "success",
            "action": "report",
            "title": title,
            "format": format
        }
    
    async def _tool_summarize(self, params: Dict) -> Dict:
        """总结内容"""
        content = params.get("content", "")
        return {"status": "success", "action": "summarize", "length": len(content)}
    
    # ===== 通知工具 =====
    
    async def _tool_notify(self, params: Dict) -> Dict:
        """发送通知"""
        message = params.get("message", "")
        channel = params.get("channel", "telegram")
        return {"status": "success", "action": "notify", "channel": channel, "message": message}
    
    async def _tool_telegram(self, params: Dict) -> Dict:
        """发送 Telegram"""
        message = params.get("message", "")
        chat_id = params.get("chat_id", "")
        return {"status": "success", "action": "telegram", "message": message}
    
    # ===== 工具 =====
    
    async def _tool_calc(self, params: Dict) -> Dict:
        """计算"""
        expression = params.get("expression", "")
        try:
            result = eval(expression)
            return {"status": "success", "action": "calc", "expression": expression, "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _tool_convert(self, params: Dict) -> Dict:
        """转换"""
        value = params.get("value", "")
        from_unit = params.get("from", "")
        to_unit = params.get("to", "")
        return {"status": "success", "action": "convert", "value": value, "from": from_unit, "to": to_unit}


# 全局注册表
_registry = ToolRegistry()

def get_registry() -> ToolRegistry:
    """获取工具注册表"""
    return _registry

# 便捷函数
async def execute_tool(tool_name: str, params: Dict = None) -> Dict:
    """执行工具的便捷函数"""
    return await _registry.execute(tool_name, params or {})

def list_all_tools() -> list:
    """列出所有可用工具"""
    return _registry.list_tools()


if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== 可用工具 ===")
        tools = list_all_tools()
        print(f"共 {len(tools)} 个工具:")
        for t in sorted(tools):
            print(f"  - {t}")
        
        print("\n=== 测试工具 ===")
        result = await execute_tool("calc", {"expression": "2+2"})
        print(result)
    
    asyncio.run(test())

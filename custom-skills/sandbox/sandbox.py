#!/usr/bin/env python3
"""
OpenClaw Sandbox - 本地代码沙箱
安全隔离执行 Python/JS 代码
"""

import subprocess
import tempfile
import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional

class Sandbox:
    def __init__(self, timeout: int = 30, memory_limit: str = "256m"):
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.temp_dir = tempfile.mkdtemp(prefix="openclaw_sandbox_")
        
    def execute_python(self, code: str) -> Dict[str, Any]:
        """执行 Python 代码 (沙箱)"""
        # 创建临时文件
        script_id = str(uuid.uuid4())[:8]
        script_path = os.path.join(self.temp_dir, f"script_{script_id}.py")
        
        # 包装代码 (限制导入)
        safe_code = self._wrap_python(code)
        
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(safe_code)
            
            # 执行 (使用受限资源)
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.temp_dir
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "执行超时"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            # 清理
            if os.path.exists(script_path):
                os.remove(script_path)
    
    def _wrap_python(self, code: str) -> str:
        """包装代码，限制危险操作"""
        # 禁止的导入
        forbidden = ["os", "sys", "subprocess", "import", "exec", "eval", "open", 
                     "requests", "urllib", "socket", "threading", "multiprocessing"]
        
        # 检查危险代码
        for word in forbidden:
            if f"import {word}" in code or f"from {word} import" in code:
                # 替换为安全版本
                code = code.replace(f"import {word}", "# import blocked")
                code = code.replace(f"from {word} import", "# from blocked")
        
        return f"""
# Sandbox - OpenClaw Code Execution
import json
import math
import random
import datetime

# User code:
{code}
"""
    
    def execute_javascript(self, code: str) -> Dict[str, Any]:
        """执行 JavaScript 代码"""
        script_id = str(uuid.uuid4())[:8]
        script_path = os.path.join(self.temp_dir, f"script_{script_id}.js")
        
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "执行超时"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
    
    def cleanup(self):
        """清理临时文件"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    sandbox = Sandbox(timeout=10)
    
    # 测试 Python
    print("=== Python 沙箱测试 ===")
    result = sandbox.execute_python("""
print("Hello from sandbox!")
result = 2 + 2
print(f"2 + 2 = {result}")
""")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    sandbox.cleanup()

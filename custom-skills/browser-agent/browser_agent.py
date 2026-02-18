#!/usr/bin/env python3
"""
OpenClaw Browser Agent - 深度浏览器自动化
智能元素定位、自动填表、错误恢复
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class SelectorType(Enum):
    ROLE = "role"
    LABEL = "label"
    PLACEHOLDER = "placeholder"
    TEXT = "text"
    TEST_ID = "testId"
    CSS = "css"
    XPath = "xpath"

@dataclass
class FormField:
    """表单字段"""
    name: str
    selector: str
    selector_type: SelectorType
    value: str
    required: bool = True

@dataclass
class ActionStep:
    """动作步骤"""
    action: str  # click, type, select, wait, scroll
    selector: str
    selector_type: SelectorType = SelectorType.CSS
    value: Optional[str] = None
    wait_for: Optional[str] = None  # visible, hidden, networkidle

class BrowserAgent:
    """
    深度浏览器自动化 Agent
    对标 BrowserUseTool
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.actions: List[ActionStep] = []
        
    async def initialize(self):
        """初始化浏览器"""
        # 使用 Playwright
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    # ===== 智能元素定位 =====
    
    async def find_element(self, selector: str, selector_type: SelectorType):
        """多策略元素定位"""
        strategies = self._get_strategies(selector, selector_type)
        
        for strategy in strategies:
            try:
                element = await self._try_strategy(strategy)
                if element:
                    return element
            except Exception:
                continue
        
        raise ElementNotFound(f"找不到元素: {selector}")
    
    def _get_strategies(self, selector: str, selector_type: SelectorType) -> List[Dict]:
        """获取定位策略列表"""
        strategies = []
        
        if selector_type == SelectorType.CSS:
            strategies.append({"type": "css", "selector": selector})
        elif selector_type == SelectorType.XPATH:
            strategies.append({"type": "xpath", "selector": selector})
        elif selector_type == SelectorType.ROLE:
            strategies.append({"type": "get_by_role", "selector": selector})
        elif selector_type == SelectorType.LABEL:
            strategies.append({"type": "get_by_label", "selector": selector})
        elif selector_type == SelectorType.PLACEHOLDER:
            strategies.append({"type": "get_by_placeholder", "selector": selector})
        elif selector_type == SelectorType.TEXT:
            strategies.append({"type": "get_by_text", "selector": selector})
        
        # 添加回退策略
        strategies.append({"type": "css", "selector": f"[name='{selector}']"})
        strategies.append({"type": "css", "selector": f"#{{selector}}"})
        strategies.append({"type": "css", "selector": f".{{selector}}"})
        
        return strategies
    
    async def _try_strategy(self, strategy: Dict) -> Optional[Any]:
        """尝试定位策略"""
        strategy_type = strategy["type"]
        selector = strategy["selector"]
        
        if strategy_type == "css":
            return await self.page.query_selector(selector)
        elif strategy_type == "xpath":
            return await self.page.query_selector(f"xpath={selector}")
        elif strategy_type == "get_by_role":
            return await self.page.get_by_role(selector).first
        elif strategy_type == "get_by_label":
            return await self.page.get_by_label(selector).first
        elif strategy_type == "get_by_placeholder":
            return await self.page.get_by_placeholder(selector).first
        elif strategy_type == "get_by_text":
            return await self.page.get_by_text(selector).first
        
        return None
    
    # ===== 动作执行 =====
    
    async def click(self, selector: str, selector_type: SelectorType = SelectorType.CSS):
        """点击元素"""
        element = await self.find_element(selector, selector_type)
        await element.click()
        return True
    
    async def type_text(self, selector: str, text: str, selector_type: SelectorType = SelectorType.CSS):
        """输入文本"""
        element = await self.find_element(selector, selector_type)
        await element.fill(text)
        return True
    
    async def select_option(self, selector: str, value: str):
        """选择选项"""
        await self.page.select_option(selector, value)
        return True
    
    async def wait_for(self, selector: str, state: str = "visible", timeout: int = 30000):
        """等待元素"""
        await self.page.wait_for_selector(selector, state=state, timeout=timeout)
        return True
    
    async def screenshot(self, path: str = None) -> bytes:
        """截图"""
        return await self.page.screenshot(path=path)
    
    async def scroll(self, x: int = 0, y: int = 500):
        """滚动页面"""
        await self.page.evaluate(f"window.scrollTo({x}, {y})")
    
    # ===== 高级功能 =====
    
    async def fill_form(self, url: str, fields: List[FormField]) -> Dict:
        """自动填表"""
        await self.page.goto(url)
        results = []
        
        for field in fields:
            try:
                element = await self.find_element(field.selector, field.selector_type)
                await element.fill(field.value)
                results.append({"field": field.name, "status": "success"})
            except Exception as e:
                results.append({"field": field.name, "status": "error", "message": str(e)})
        
        return {
            "status": "completed",
            "results": results,
            "total": len(fields),
            "success": sum(1 for r in results if r["status"] == "success")
        }
    
    async def execute_actions(self, actions: List[ActionStep]) -> List[Dict]:
        """执行动作序列"""
        results = []
        
        for i, action in enumerate(actions):
            try:
                if action.action == "click":
                    await self.click(action.selector, action.selector_type)
                elif action.action == "type":
                    await self.type_text(action.selector, action.value, action.selector_type)
                elif action.action == "select":
                    await self.select_option(action.selector, action.value)
                elif action.action == "wait":
                    await self.wait_for(action.selector, action.wait_for or "visible")
                elif action.action == "scroll":
                    await self.scroll(0, int(action.value or 500))
                elif action.action == "screenshot":
                    await self.screenshot(action.value)
                
                results.append({"step": i+1, "action": action.action, "status": "success"})
            except Exception as e:
                results.append({"step": i+1, "action": action.action, "status": "error", "message": str(e)})
        
        return results
    
    async def extract_data(self, selectors: Dict) -> Dict:
        """提取页面数据"""
        data = {}
        
        for key, selector in selectors.items():
            try:
                element = await self.page.query_selector(selector)
                if element:
                    data[key] = await element.inner_text()
                else:
                    data[key] = None
            except Exception:
                data[key] = None
        
        return data
    
    async def wait_for_network_idle(self, timeout: int = 30000):
        """等待网络空闲"""
        await self.page.wait_for_load_state("networkidle", timeout=timeout)


class ElementNotFound(Exception):
    """元素未找到异常"""
    pass


# 便捷函数
async def quick_browse(url: str, actions: List[Dict]) -> Dict:
    """快速浏览"""
    agent = BrowserAgent(headless=True)
    
    try:
        await agent.initialize()
        await agent.page.goto(url)
        
        # 执行动作
        for action in actions:
            action_type = action.get("type", "click")
            
            if action_type == "click":
                await agent.click(action.get("selector", ""))
            elif action_type == "type":
                await agent.type_text(action.get("selector", ""), action.get("value", ""))
            elif action_type == "screenshot":
                await agent.screenshot(action.get("path", "/tmp/screenshot.png"))
        
        return {"status": "success", "url": url}
    
    finally:
        await agent.close()


if __name__ == "__main__":
    # 测试
    async def test():
        agent = BrowserAgent(headless=False)
        await agent.initialize()
        
        # 打开百度
        await agent.page.goto("https://www.baidu.com")
        await agent.screenshot("/tmp/baidu.png")
        
        print("截图保存到 /tmp/baidu.png")
        
        await agent.close()
    
    asyncio.run(test())

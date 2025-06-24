"""browser-use AI降级功能"""

import asyncio
from typing import Any, Dict, Optional

from loguru import logger
from playwright.async_api import Page

try:
    from browser_use import Agent
    BROWSER_USE_AVAILABLE = True
except ImportError:
    logger.warning("browser-use未安装，AI降级功能不可用")
    BROWSER_USE_AVAILABLE = False

from ..config import settings


class BrowserUseAgent:
    """browser-use AI代理，用于智能网页操作"""
    
    def __init__(self):
        self.agent: Optional[Agent] = None
        self._initialized = False
    
    async def initialize(self, page: Page) -> bool:
        """初始化AI代理"""
        if not BROWSER_USE_AVAILABLE:
            logger.warning("browser-use不可用，跳过AI代理初始化")
            return False
        
        try:
            # 注意：这里需要根据实际的browser-use API进行调整
            self.agent = Agent(
                task="智能抓取豆瓣图书信息",
                llm_config={
                    "provider": "openai",  # 或其他支持的LLM提供商
                    "model": "gpt-4",
                    "temperature": 0.1,
                },
                use_vision=True,
                max_actions_per_step=10,
            )
            
            self._initialized = True
            logger.info("browser-use AI代理初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"AI代理初始化失败: {e}")
            return False
    
    async def search_and_extract_book(self, page: Page, query: str) -> Dict[str, Any]:
        """使用AI智能搜索并提取图书信息"""
        if not self._initialized or not self.agent:
            raise RuntimeError("AI代理未初始化")
        
        task_prompt = f"""
        任务：在豆瓣读书网站上搜索图书"{query}"并提取第一个结果的详细信息
        
        步骤：
        1. 在豆瓣读书首页的搜索框中输入"{query}"
        2. 点击搜索按钮或按Enter键
        3. 在搜索结果中点击第一本书的标题链接
        4. 进入图书详情页面后，提取以下信息：
           - 书名
           - 作者
           - 出版社
           - 出版日期
           - 页数
           - 评分和评分人数
           - 内容简介
           - 是否可在线阅读
           - 短评（前5条）
           - 书评（前10条）
        
        请确保提取的信息准确完整。
        """
        
        try:
            # 使用browser-use执行任务
            result = await self.agent.run(task_prompt, page)
            
            # 处理和解析结果
            return self._parse_ai_result(result)
            
        except Exception as e:
            logger.error(f"AI抓取失败: {e}")
            raise
    
    async def extract_book_detail(self, page: Page, book_id: str) -> Dict[str, Any]:
        """使用AI智能提取图书详情"""
        if not self._initialized or not self.agent:
            raise RuntimeError("AI代理未初始化")
        
        task_prompt = f"""
        任务：从当前豆瓣图书详情页面提取完整的图书信息
        
        当前页面应该是图书ID为{book_id}的详情页面。
        
        请提取以下信息：
        1. 基本信息：
           - 书名（主标题和副标题）
           - 作者列表
           - 译者（如果有）
           - 出版社
           - 出版日期
           - ISBN-10和ISBN-13
           - 页数
           - 定价
           - 装帧方式
        
        2. 内容信息：
           - 内容简介
           - 作者简介
           - 目录
        
        3. 评分和互动：
           - 平均评分
           - 评分人数
           - 各星级评分分布
           - 是否可在线阅读
        
        4. 用户评论：
           - 短评（前5条，包含用户名、时间、评分、内容）
           - 书评（前10条，包含用户名、时间、标题、评分、内容）
        
        5. 其他信息：
           - 封面图片URL
           - 图书标签
        
        请确保信息提取准确，如果某些信息不存在则标记为null。
        """
        
        try:
            # 使用browser-use执行任务
            result = await self.agent.run(task_prompt, page)
            
            # 处理和解析结果
            return self._parse_ai_result(result)
            
        except Exception as e:
            logger.error(f"AI详情提取失败: {e}")
            raise
    
    def _parse_ai_result(self, result: Any) -> Dict[str, Any]:
        """解析AI返回的结果"""
        # 这里需要根据browser-use的实际返回格式进行解析
        # 暂时返回一个示例结构
        
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            # 如果返回的是文本，尝试解析为JSON
            try:
                import json
                return json.loads(result)
            except json.JSONDecodeError:
                # 如果不是JSON，返回原始文本
                return {"raw_text": result}
        else:
            return {"raw_result": str(result)}


class AIFallbackManager:
    """AI降级管理器"""
    
    def __init__(self):
        self.browser_use_agent = BrowserUseAgent()
        self._agent_ready = False
    
    async def ensure_agent_ready(self, page: Page) -> bool:
        """确保AI代理就绪"""
        if not self._agent_ready:
            self._agent_ready = await self.browser_use_agent.initialize(page)
        return self._agent_ready
    
    async def fallback_search_book(self, page: Page, query: str) -> Dict[str, Any]:
        """AI降级搜索图书"""
        if not await self.ensure_agent_ready(page):
            raise RuntimeError("AI代理不可用")
        
        logger.info(f"使用AI降级搜索图书: {query}")
        return await self.browser_use_agent.search_and_extract_book(page, query)
    
    async def fallback_extract_detail(self, page: Page, book_id: str) -> Dict[str, Any]:
        """AI降级提取图书详情"""
        if not await self.ensure_agent_ready(page):
            raise RuntimeError("AI代理不可用")
        
        logger.info(f"使用AI降级提取图书详情: {book_id}")
        return await self.browser_use_agent.extract_book_detail(page, book_id)


# 全局AI降级管理器
ai_fallback_manager = AIFallbackManager() 
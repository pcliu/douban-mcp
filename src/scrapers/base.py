"""基础爬虫类 - 实现缓存降级策略"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timezone

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .browser_manager import browser_manager
from ..config import settings
from ..cache.cache_manager import cache_manager

T = TypeVar('T')


class BaseScraper(ABC, Generic[T]):
    """基础爬虫类 - 实现缓存降级策略"""
    
    def __init__(self, scraper_name: str):
        self.scraper_name = scraper_name
        self.cache_prefix = f"{settings.cache_key_prefix}{scraper_name}:"
    
    @abstractmethod
    async def scrape_with_playwright(self, page: Page, **kwargs) -> T:
        """使用固定Playwright脚本抓取数据"""
        pass
    
    @abstractmethod
    async def scrape_with_browser_use(self, page: Page, **kwargs) -> T:
        """使用browser-use AI降级抓取数据"""
        pass
    
    @abstractmethod
    def get_cache_key(self, **kwargs) -> str:
        """生成缓存键"""
        pass
    
    async def scrape(self, **kwargs) -> T:
        """主要抓取方法 - 实现缓存降级策略"""
        cache_key = self.get_cache_key(**kwargs)
        
        # 1. 尝试从缓存获取
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"从缓存获取数据: {cache_key}")
            return cached_result
        
        # 2. 使用固定Playwright脚本
        try:
            logger.info(f"使用固定脚本抓取: {cache_key}")
            result = await self._scrape_with_retry(self.scrape_with_playwright, **kwargs)
            
            # 成功则缓存结果
            await self._save_to_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"固定脚本抓取失败: {e}, 切换到AI降级")
        
        # 3. 使用browser-use AI降级
        try:
            logger.info(f"使用AI降级抓取: {cache_key}")
            result = await self._scrape_with_retry(self.scrape_with_browser_use, **kwargs)
            
            # 成功则缓存结果
            await self._save_to_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"AI降级抓取也失败: {e}")
            raise
    
    async def _scrape_with_retry(self, scrape_func, **kwargs) -> T:
        """带重试的抓取方法"""
        last_exception = None
        
        for attempt in range(settings.max_retries):
            try:
                # 随机延迟避免被检测
                if attempt > 0:
                    delay = random.uniform(
                        settings.request_delay_min * attempt,
                        settings.request_delay_max * attempt
                    )
                    await asyncio.sleep(delay)
                
                async with browser_manager:
                    page = await browser_manager.new_page()
                    try:
                        return await scrape_func(page, **kwargs)
                    finally:
                        await page.close()
                        
            except Exception as e:
                last_exception = e
                logger.warning(f"抓取尝试 {attempt + 1}/{settings.max_retries} 失败: {e}")
                
                # 如果是网络超时，等待更长时间
                if isinstance(e, PlaywrightTimeoutError):
                    await asyncio.sleep(5)
        
        raise last_exception or Exception("所有重试都失败了")
    
    async def _get_from_cache(self, cache_key: str) -> Optional[T]:
        """从缓存获取数据"""
        try:
            return await cache_manager.get_scraped_data(cache_key)
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
            return None
    
    async def _save_to_cache(self, cache_key: str, data: T) -> None:
        """保存数据到缓存"""
        try:
            await cache_manager.set_scraped_data(
                cache_key, 
                data, 
                ttl=settings.cache_ttl
            )
            logger.debug(f"数据已缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")
    
    async def wait_for_element(
        self, 
        page: Page, 
        selector: str, 
        timeout: int = 10000
    ) -> bool:
        """等待元素出现"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False
    
    async def safe_click(self, page: Page, selector: str) -> bool:
        """安全点击元素"""
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.click()
                return True
        except Exception as e:
            logger.debug(f"点击失败 {selector}: {e}")
        return False
    
    async def safe_fill(self, page: Page, selector: str, text: str) -> bool:
        """安全填入文本"""
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.fill(text)
                return True
        except Exception as e:
            logger.debug(f"填入文本失败 {selector}: {e}")
        return False
    
    async def extract_text(self, page: Page, selector: str) -> Optional[str]:
        """提取文本内容"""
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                text = await element.text_content()
                return text.strip() if text else None
        except Exception as e:
            logger.debug(f"提取文本失败 {selector}: {e}")
        return None
    
    async def extract_attribute(
        self, 
        page: Page, 
        selector: str, 
        attribute: str
    ) -> Optional[str]:
        """提取元素属性"""
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                return await element.get_attribute(attribute)
        except Exception as e:
            logger.debug(f"提取属性失败 {selector}.{attribute}: {e}")
        return None
    
    def get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now(timezone.utc).isoformat()
    
    async def random_delay(self, min_delay: float = None, max_delay: float = None) -> None:
        """随机延迟"""
        min_delay = min_delay or settings.request_delay_min
        max_delay = max_delay or settings.request_delay_max
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay) 
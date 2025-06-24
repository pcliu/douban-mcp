"""浏览器管理器 - 支持本地和云端浏览器"""

import asyncio
from typing import Any, Dict, Optional
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright
import random
from loguru import logger

from ..config import settings


class BrowserManager:
    """浏览器管理器 - 支持本地和云端浏览器"""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    async def start(self) -> None:
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        
        if settings.browser_mode == "remote":
            await self._start_remote_browser()
        else:
            await self._start_local_browser()
        
        # 创建浏览器上下文
        await self._create_context()
        logger.info(f"浏览器已启动 (模式: {settings.browser_mode})")
    
    async def _start_local_browser(self) -> None:
        """启动本地浏览器"""
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--window-size=1920,1080",
        ]
        
        # 添加用户自定义参数
        browser_args.extend(settings.local_browser_args)
        
        launch_options = {
            "headless": settings.browser_headless,
            "args": browser_args,
        }
        
        # 如果指定了自定义浏览器路径
        if settings.local_browser_executable_path:
            launch_options["executable_path"] = settings.local_browser_executable_path
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
    
    async def _start_remote_browser(self) -> None:
        """启动远程浏览器"""
        if not settings.remote_browser_url:
            raise ValueError("远程浏览器模式需要配置 remote_browser_url")
        
        # 构建连接选项
        connect_options = {
            "wsEndpoint": settings.remote_browser_url,
        }
        
        # 添加认证信息
        headers = {}
        if settings.remote_browser_api_key:
            headers["Authorization"] = f"Bearer {settings.remote_browser_api_key}"
        if settings.remote_browser_token:
            headers["X-Token"] = settings.remote_browser_token
        
        if headers:
            connect_options["headers"] = headers
        
        try:
            self.browser = await self.playwright.chromium.connect(**connect_options)
        except Exception as e:
            logger.error(f"连接远程浏览器失败: {e}")
            raise
    
    async def _create_context(self) -> None:
        """创建浏览器上下文"""
        if not self.browser:
            raise RuntimeError("浏览器未启动")
        
        # 随机选择用户代理
        user_agent = random.choice(self._user_agents)
        
        context_options = {
            "user_agent": user_agent,
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "extra_http_headers": {
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }
        }
        
        self.context = await self.browser.new_context(**context_options)
        
        # 启用请求拦截优化
        await self._setup_request_interception()
    
    async def _setup_request_interception(self) -> None:
        """设置请求拦截以优化性能"""
        if not self.context:
            return
        
        async def route_handler(route, request):
            """拦截不必要的资源请求"""
            resource_type = request.resource_type
            
            # 跳过图片、字体、样式表等静态资源以提高速度
            if resource_type in ["image", "font", "stylesheet", "media"]:
                await route.abort()
            else:
                await route.continue_()
        
        await self.context.route("**/*", route_handler)
    
    async def new_page(self) -> Page:
        """创建新页面"""
        if not self.context:
            raise RuntimeError("浏览器上下文未创建")
        
        page = await self.context.new_page()
        
        # 设置超时
        page.set_default_timeout(settings.browser_timeout)
        
        return page
    
    async def close(self) -> None:
        """关闭浏览器"""
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        logger.info("浏览器已关闭")
    
    async def get_browser_info(self) -> Dict[str, Any]:
        """获取浏览器信息"""
        if not self.browser:
            return {"status": "not_started"}
        
        return {
            "status": "running",
            "mode": settings.browser_mode,
            "headless": settings.browser_headless,
            "version": await self.browser.version() if hasattr(self.browser, 'version') else "unknown",
            "contexts": len(self.browser.contexts) if self.browser else 0,
        }
    
    async def __aenter__(self):
        """异步上下文管理器进入"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


# 全局浏览器管理器实例
browser_manager = BrowserManager() 
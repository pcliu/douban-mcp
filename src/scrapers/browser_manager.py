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
    
    def _calculate_center_position_and_size(self) -> tuple[str, tuple[int, int] | None]:
        """计算浏览器窗口在屏幕中央的位置和调整后的尺寸"""
        try:
            import tkinter as tk
            root = tk.Tk()
            
            # 获取屏幕尺寸
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            
            # 获取窗口尺寸
            window_width = settings.browser_viewport_width
            window_height = settings.browser_viewport_height
            original_size = (window_width, window_height)
            size_adjusted = False
            
            # 如果窗口尺寸大于屏幕尺寸，调整窗口尺寸
            if window_width > screen_width:
                logger.warning(f"窗口宽度({window_width})大于屏幕宽度({screen_width})，调整为屏幕宽度的90%")
                window_width = int(screen_width * 0.9)
                size_adjusted = True
                
            if window_height > screen_height - 100:  # 预留100像素给任务栏等
                logger.warning(f"窗口高度({window_height})大于可用屏幕高度，调整为可用高度的90%")
                window_height = int((screen_height - 100) * 0.9)
                size_adjusted = True
            
            # 考虑窗口标题栏和边框的额外高度（大约80像素）
            window_height_with_frame = window_height + 80
            
            # 计算居中位置
            center_x = (screen_width - window_width) // 2
            center_y = (screen_height - window_height_with_frame) // 2
            
            # 确保坐标不为负数，并设置最小边距
            center_x = max(10, center_x)
            center_y = max(10, center_y)
            
            logger.info(f"屏幕尺寸: {screen_width}x{screen_height}")
            if size_adjusted:
                logger.info(f"原始窗口尺寸: {original_size[0]}x{original_size[1]}")
                logger.info(f"调整后窗口尺寸: {window_width}x{window_height}")
            else:
                logger.info(f"窗口尺寸: {window_width}x{window_height}")
            logger.info(f"计算的居中位置: {center_x},{center_y}")
            
            adjusted_size = (window_width, window_height) if size_adjusted else None
            return f"{center_x},{center_y}", adjusted_size
            
        except Exception as e:
            logger.warning(f"无法计算窗口居中位置: {e}，使用默认位置")
            # 如果无法获取屏幕尺寸，使用通用的居中位置
            return "200,150", None
    
    def _calculate_center_position(self) -> str:
        """计算浏览器窗口在屏幕中央的位置（向后兼容方法）"""
        position, _ = self._calculate_center_position_and_size()
        return position
    
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
        # 获取窗口尺寸和位置信息
        window_width = settings.browser_viewport_width
        window_height = settings.browser_viewport_height
        window_position = None
        
        # 根据配置决定是否设置窗口居中位置
        if settings.browser_center_window and not settings.browser_headless:
            window_position, adjusted_size = self._calculate_center_position_and_size()
            if adjusted_size:
                window_width, window_height = adjusted_size
        elif not settings.browser_headless:
            window_position = "100,100"
        
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            f"--window-size={window_width},{window_height}",
            "--start-maximized" if not settings.browser_headless else "",  # 非headless模式下最大化窗口
        ]
        
        # 添加窗口位置参数
        if window_position and not settings.browser_headless:
            browser_args.append(f"--window-position={window_position}")
        
        # 移除空字符串
        browser_args = [arg for arg in browser_args if arg]
        
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
            "viewport": {
                "width": settings.browser_viewport_width,
                "height": settings.browser_viewport_height
            },
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "device_scale_factor": 1,  # 设置设备像素比
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
            
            # 根据配置决定是否阻止资源类型
            blocked_types = ["media"]  # 默认阻止媒体文件
            
            # 如果配置中不加载图片，则也阻止图片
            if not settings.browser_load_images:
                blocked_types.append("image")
            
            if resource_type in blocked_types:
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
            try:
                await self.context.close()
            except Exception as e:
                logger.warning(f"关闭浏览器上下文时出错: {e}")
            finally:
                self.context = None
        
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")
            finally:
                self.browser = None
        
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.warning(f"停止Playwright时出错: {e}")
            finally:
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
            "version": self.browser.version if hasattr(self.browser, 'version') else "unknown",
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
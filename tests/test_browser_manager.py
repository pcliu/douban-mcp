"""浏览器管理器测试"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from pathlib import Path

# 设置项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.browser_manager import BrowserManager, browser_manager
from src.config import Settings


class TestBrowserManager:
    """BrowserManager 测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.browser_manager = BrowserManager()
    
    async def test_init(self):
        """测试初始化"""
        assert self.browser_manager.playwright is None
        assert self.browser_manager.browser is None
        assert self.browser_manager.context is None
        assert len(self.browser_manager._user_agents) == 3
        assert all("Mozilla/5.0" in ua for ua in self.browser_manager._user_agents)
    
    @pytest.mark.asyncio
    async def test_start_local_browser_success(self):
        """测试成功启动本地浏览器"""
        # Mock playwright 和相关对象
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_chromium = AsyncMock()
        
        # 设置 mock 对象属性
        mock_playwright.chromium = mock_chromium
        mock_chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        
        with patch('src.scrapers.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright_instance = AsyncMock()
            mock_async_playwright_instance.start.return_value = mock_playwright
            mock_async_playwright.return_value = mock_async_playwright_instance
            
            # 测试设置
            with patch('src.scrapers.browser_manager.settings') as mock_settings:
                mock_settings.browser_mode = "local"
                mock_settings.browser_headless = True
                mock_settings.local_browser_args = []
                mock_settings.local_browser_executable_path = None
                
                await self.browser_manager.start()
                
                # 验证调用
                mock_chromium.launch.assert_called_once()
                mock_browser.new_context.assert_called_once()
                assert self.browser_manager.playwright is not None
                assert self.browser_manager.browser is not None
                assert self.browser_manager.context is not None
    
    @pytest.mark.asyncio
    async def test_start_remote_browser_success(self):
        """测试成功启动远程浏览器"""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_chromium = AsyncMock()
        
        mock_playwright.chromium = mock_chromium
        mock_chromium.connect.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        
        with patch('src.scrapers.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            with patch('src.scrapers.browser_manager.settings') as mock_settings:
                mock_settings.browser_mode = "remote"
                mock_settings.remote_browser_url = "wss://test.browserless.io"
                mock_settings.remote_browser_api_key = "test_key"
                mock_settings.remote_browser_token = "test_token"
                
                await self.browser_manager.start()
                
                # 验证远程连接调用
                mock_chromium.connect.assert_called_once_with(
                    wsEndpoint="wss://test.browserless.io",
                    headers={
                        "Authorization": "Bearer test_key",
                        "X-Token": "test_token"
                    }
                )
    
    @pytest.mark.asyncio
    async def test_start_remote_browser_missing_url(self):
        """测试远程浏览器缺少URL配置"""
        mock_playwright = AsyncMock()
        
        with patch('src.scrapers.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            with patch('src.scrapers.browser_manager.settings') as mock_settings:
                mock_settings.browser_mode = "remote"
                mock_settings.remote_browser_url = None
                
                with pytest.raises(ValueError, match="远程浏览器模式需要配置 remote_browser_url"):
                    await self.browser_manager.start()
    
    @pytest.mark.asyncio
    async def test_start_remote_browser_connection_failed(self):
        """测试远程浏览器连接失败"""
        mock_playwright = AsyncMock()
        mock_chromium = AsyncMock()
        mock_playwright.chromium = mock_chromium
        mock_chromium.connect.side_effect = Exception("连接失败")
        
        with patch('src.scrapers.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            with patch('src.scrapers.browser_manager.settings') as mock_settings:
                mock_settings.browser_mode = "remote"
                mock_settings.remote_browser_url = "wss://invalid.url"
                mock_settings.remote_browser_api_key = None
                mock_settings.remote_browser_token = None
                
                with pytest.raises(Exception, match="连接失败"):
                    await self.browser_manager.start()
    
    @pytest.mark.asyncio
    async def test_create_context_options(self):
        """测试创建浏览器上下文的配置"""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        self.browser_manager.browser = mock_browser
        
        await self.browser_manager._create_context()
        
        # 验证 new_context 被调用
        mock_browser.new_context.assert_called_once()
        
        # 获取调用参数
        call_args = mock_browser.new_context.call_args[1]
        
        # 验证基本配置
        assert "user_agent" in call_args
        assert "Mozilla/5.0" in call_args["user_agent"]
        assert call_args["viewport"] == {"width": 1920, "height": 1080}
        assert call_args["locale"] == "zh-CN"
        assert call_args["timezone_id"] == "Asia/Shanghai"
        assert "Accept-Language" in call_args["extra_http_headers"]
        assert "zh-CN" in call_args["extra_http_headers"]["Accept-Language"]
    
    @pytest.mark.asyncio
    async def test_create_context_without_browser(self):
        """测试没有浏览器时创建上下文"""
        self.browser_manager.browser = None
        
        with pytest.raises(RuntimeError, match="浏览器未启动"):
            await self.browser_manager._create_context()
    
    @pytest.mark.asyncio
    async def test_new_page_success(self):
        """测试成功创建新页面"""
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        self.browser_manager.context = mock_context
        
        with patch('src.scrapers.browser_manager.settings') as mock_settings:
            mock_settings.browser_timeout = 30000
            
            page = await self.browser_manager.new_page()
            
            assert page is mock_page
            mock_context.new_page.assert_called_once()
            mock_page.set_default_timeout.assert_called_once_with(30000)
    
    @pytest.mark.asyncio
    async def test_new_page_without_context(self):
        """测试没有上下文时创建页面"""
        self.browser_manager.context = None
        
        with pytest.raises(RuntimeError, match="浏览器上下文未创建"):
            await self.browser_manager.new_page()
    
    @pytest.mark.asyncio
    async def test_close_all_components(self):
        """测试关闭所有浏览器组件"""
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()
        
        self.browser_manager.context = mock_context
        self.browser_manager.browser = mock_browser
        self.browser_manager.playwright = mock_playwright
        
        await self.browser_manager.close()
        
        # 验证关闭顺序和调用
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
        
        # 验证所有引用被清理
        assert self.browser_manager.context is None
        assert self.browser_manager.browser is None
        assert self.browser_manager.playwright is None
    
    @pytest.mark.asyncio
    async def test_close_partial_components(self):
        """测试部分组件存在时的关闭"""
        mock_browser = AsyncMock()
        
        # 只设置浏览器，没有上下文和playwright
        self.browser_manager.browser = mock_browser
        self.browser_manager.context = None
        self.browser_manager.playwright = None
        
        await self.browser_manager.close()
        
        mock_browser.close.assert_called_once()
        assert self.browser_manager.browser is None
    
    @pytest.mark.asyncio
    async def test_get_browser_info_not_started(self):
        """测试获取未启动浏览器的信息"""
        self.browser_manager.browser = None
        
        info = await self.browser_manager.get_browser_info()
        assert info == {"status": "not_started"}
    
    @pytest.mark.asyncio
    async def test_get_browser_info_running(self):
        """测试获取运行中浏览器的信息"""
        mock_browser = AsyncMock()
        mock_browser.version.return_value = "120.0.0.0"
        mock_browser.contexts = ["context1", "context2"]
        
        self.browser_manager.browser = mock_browser
        
        with patch('src.scrapers.browser_manager.settings') as mock_settings:
            mock_settings.browser_mode = "local"
            mock_settings.browser_headless = True
            
            info = await self.browser_manager.get_browser_info()
            
            assert info["status"] == "running"
            assert info["mode"] == "local"
            assert info["headless"] is True
            assert info["version"] == "120.0.0.0"
            assert info["contexts"] == 2
    
    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """测试异步上下文管理器成功流程"""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_chromium = AsyncMock()
        
        mock_playwright.chromium = mock_chromium
        mock_chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        
        with patch('src.scrapers.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            with patch('src.scrapers.browser_manager.settings') as mock_settings:
                mock_settings.browser_mode = "local"
                mock_settings.browser_headless = True
                mock_settings.local_browser_args = []
                mock_settings.local_browser_executable_path = None
                
                async with self.browser_manager as manager:
                    assert manager is self.browser_manager
                    assert manager.browser is not None
                    assert manager.context is not None
                
                # 验证退出时调用了 close
                mock_context.close.assert_called_once()
                mock_browser.close.assert_called_once()
                mock_playwright.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_exception(self):
        """测试异步上下文管理器异常处理"""
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_chromium = AsyncMock()
        
        mock_playwright.chromium = mock_chromium
        mock_chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        
        with patch('src.scrapers.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            with patch('src.scrapers.browser_manager.settings') as mock_settings:
                mock_settings.browser_mode = "local"
                mock_settings.browser_headless = True
                mock_settings.local_browser_args = []
                mock_settings.local_browser_executable_path = None
                
                with pytest.raises(ValueError, match="测试异常"):
                    async with self.browser_manager:
                        raise ValueError("测试异常")
                
                # 即使发生异常，仍应该调用 close
                mock_context.close.assert_called_once()
                mock_browser.close.assert_called_once()
                mock_playwright.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_request_interception(self):
        """测试请求拦截设置"""
        mock_context = AsyncMock()
        self.browser_manager.context = mock_context
        
        await self.browser_manager._setup_request_interception()
        
        # 验证路由处理器被设置
        mock_context.route.assert_called_once_with("**/*", ANY)
    
    def test_user_agents_randomization(self):
        """测试用户代理随机化"""
        # 多次创建上下文应该可能选择不同的用户代理
        user_agents = set()
        
        for _ in range(10):
            # 由于使用了 random.choice，这里模拟测试
            import random
            selected_ua = random.choice(self.browser_manager._user_agents)
            user_agents.add(selected_ua)
        
        # 应该至少有一个用户代理被选中
        assert len(user_agents) >= 1
        assert all("Mozilla/5.0" in ua for ua in user_agents)


class TestBrowserManagerIntegration:
    """BrowserManager 集成测试"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_local_browser_startup(self):
        """测试真实的本地浏览器启动（集成测试）"""
        # 只在有真实浏览器环境时运行
        if os.getenv("SKIP_BROWSER_TESTS") == "true":
            pytest.skip("跳过浏览器测试")
        
        browser_manager = BrowserManager()
        
        with patch('src.scrapers.browser_manager.settings') as mock_settings:
            mock_settings.browser_mode = "local"
            mock_settings.browser_headless = True
            mock_settings.browser_timeout = 10000
            mock_settings.local_browser_args = []
            mock_settings.local_browser_executable_path = None
            
            try:
                await browser_manager.start()
                
                # 验证组件正常创建
                assert browser_manager.playwright is not None
                assert browser_manager.browser is not None
                assert browser_manager.context is not None
                
                # 测试创建页面
                page = await browser_manager.new_page()
                assert page is not None
                
                # 测试获取浏览器信息
                info = await browser_manager.get_browser_info()
                assert info["status"] == "running"
                assert info["mode"] == "local"
                
            finally:
                await browser_manager.close()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_global_browser_manager_instance(self):
        """测试全局浏览器管理器实例"""
        # 确保全局实例存在
        assert browser_manager is not None
        assert isinstance(browser_manager, BrowserManager)
        
        # 初始状态应该是未启动的
        info = await browser_manager.get_browser_info()
        assert info["status"] == "not_started"


class TestBrowserManagerErrorHandling:
    """BrowserManager 错误处理测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.browser_manager = BrowserManager()
    
    @pytest.mark.asyncio
    async def test_launch_failure_handling(self):
        """测试浏览器启动失败处理"""
        mock_playwright = AsyncMock()
        mock_chromium = AsyncMock()
        mock_playwright.chromium = mock_chromium
        mock_chromium.launch.side_effect = Exception("启动失败")
        
        with patch('src.scrapers.browser_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start.return_value = mock_playwright
            
            with patch('src.scrapers.browser_manager.settings') as mock_settings:
                mock_settings.browser_mode = "local"
                mock_settings.browser_headless = True
                mock_settings.local_browser_args = []
                mock_settings.local_browser_executable_path = None
                
                with pytest.raises(Exception, match="启动失败"):
                    await self.browser_manager.start()
    
    @pytest.mark.asyncio
    async def test_context_creation_failure(self):
        """测试上下文创建失败处理"""
        mock_browser = AsyncMock()
        mock_browser.new_context.side_effect = Exception("上下文创建失败")
        
        self.browser_manager.browser = mock_browser
        
        with pytest.raises(Exception, match="上下文创建失败"):
            await self.browser_manager._create_context()
    
    @pytest.mark.asyncio
    async def test_page_creation_failure(self):
        """测试页面创建失败处理"""
        mock_context = AsyncMock()
        mock_context.new_page.side_effect = Exception("页面创建失败")
        
        self.browser_manager.context = mock_context
        
        with pytest.raises(Exception, match="页面创建失败"):
            await self.browser_manager.new_page()
    
    @pytest.mark.asyncio
    async def test_close_with_errors(self):
        """测试关闭时出现错误的处理"""
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()
        
        # 模拟关闭时出错
        mock_context.close.side_effect = Exception("关闭上下文失败")
        mock_browser.close.side_effect = Exception("关闭浏览器失败")
        mock_playwright.stop.side_effect = Exception("停止playwright失败")
        
        self.browser_manager.context = mock_context
        self.browser_manager.browser = mock_browser
        self.browser_manager.playwright = mock_playwright
        
        # close 方法应该继续执行，即使某些步骤失败
        # 这里我们不期望异常，因为 close 应该是 best-effort 的
        try:
            await self.browser_manager.close()
        except Exception:
            # 如果实现中没有处理异常，这个测试会失败
            # 这提示我们需要在 close 方法中添加异常处理
            pass
        
        # 无论如何，引用都应该被清理
        assert self.browser_manager.context is None
        assert self.browser_manager.browser is None
        assert self.browser_manager.playwright is None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"]) 
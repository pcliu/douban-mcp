"""配置管理模块测试"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from src.config import Settings


class TestSettings:
    """配置设置测试类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        # 创建一个不使用.env文件的Settings实例来测试真正的默认值
        settings = Settings(_env_file=None)
        
        # 数据库配置
        assert settings.cache_db_path == "./data/cache.db"
        
        # 浏览器配置
        assert settings.browser_headless is True
        assert settings.browser_timeout == 30000
        assert "Mozilla/5.0" in settings.browser_user_agent
        assert settings.browser_mode == "local"
        
        # 本地浏览器配置
        assert settings.local_browser_executable_path is None
        assert settings.local_browser_args == []
        
        # 远程浏览器配置
        assert settings.remote_browser_url is None
        assert settings.remote_browser_api_key is None
        assert settings.remote_browser_token is None
        
        # 抓取配置
        assert settings.request_delay_min == 1.0
        assert settings.request_delay_max == 3.0
        assert settings.max_concurrent_requests == 5
        assert settings.max_retries == 3
        
        # 缓存配置
        assert settings.cache_ttl == 3600
        assert settings.cache_key_prefix == "douban_mcp:"
        
        # MCP配置
        assert settings.mcp_server_name == "douban-mcp"
        assert settings.mcp_server_version == "0.1.0"
        
        # 日志配置
        assert settings.log_level == "INFO"
        assert "time" in settings.log_format
    
    def test_env_file_loading(self):
        """测试从.env文件加载配置"""
        # 创建临时.env文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_content = """
BROWSER_MODE=remote
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=60000
REMOTE_BROWSER_URL=wss://test.browserless.io
REMOTE_BROWSER_TOKEN=test_token_123
REQUEST_DELAY_MIN=2.5
REQUEST_DELAY_MAX=5.0
MAX_RETRIES=5
CACHE_TTL=7200
LOG_LEVEL=DEBUG
"""
            f.write(env_content)
            env_file_path = f.name
        
        try:
            # 使用临时.env文件创建Settings
            settings = Settings(_env_file=env_file_path)
            
            assert settings.browser_mode == "remote"
            assert settings.browser_headless is False
            assert settings.browser_timeout == 60000
            assert settings.remote_browser_url == "wss://test.browserless.io"
            assert settings.remote_browser_token == "test_token_123"
            assert settings.request_delay_min == 2.5
            assert settings.request_delay_max == 5.0
            assert settings.max_retries == 5
            assert settings.cache_ttl == 7200
            assert settings.log_level == "DEBUG"
            
        finally:
            # 清理临时文件
            os.unlink(env_file_path)
    
    def test_environment_variables_priority(self):
        """测试环境变量优先级（环境变量 > .env文件 > 默认值）"""
        # 创建临时.env文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_content = """
BROWSER_MODE=remote
BROWSER_HEADLESS=false
LOG_LEVEL=DEBUG
"""
            f.write(env_content)
            env_file_path = f.name
        
        try:
            # 设置环境变量（应该覆盖.env文件中的值）
            with patch.dict(os.environ, {
                'BROWSER_MODE': 'local',
                'LOG_LEVEL': 'ERROR',
                'MAX_RETRIES': '10'
            }):
                settings = Settings(_env_file=env_file_path)
                
                # 环境变量应该覆盖.env文件
                assert settings.browser_mode == "local"  # 环境变量覆盖
                assert settings.log_level == "ERROR"      # 环境变量覆盖
                assert settings.max_retries == 10         # 环境变量覆盖
                
                # .env文件中的值（环境变量中没有的）
                assert settings.browser_headless is False  # 来自.env文件
                
        finally:
            os.unlink(env_file_path)
    
    def test_case_insensitive_env_vars(self):
        """测试环境变量不区分大小写"""
        with patch.dict(os.environ, {
            'browser_mode': 'remote',
            'BROWSER_HEADLESS': 'true',
            'Browser_Timeout': '45000'
        }):
            settings = Settings()
            
            assert settings.browser_mode == "remote"
            assert settings.browser_headless is True
            assert settings.browser_timeout == 45000
    
    def test_local_browser_configuration(self):
        """测试本地浏览器配置"""
        with patch.dict(os.environ, {
            'BROWSER_MODE': 'local',
            'LOCAL_BROWSER_EXECUTABLE_PATH': '/usr/bin/chromium',
            'LOCAL_BROWSER_ARGS': '["--no-sandbox", "--disable-gpu"]'
        }):
            settings = Settings()
            
            assert settings.browser_mode == "local"
            assert settings.local_browser_executable_path == "/usr/bin/chromium"
            # 注意：JSON字符串解析可能需要特殊处理
    
    def test_remote_browser_configuration(self):
        """测试远程浏览器配置"""
        with patch.dict(os.environ, {
            'BROWSER_MODE': 'remote',
            'REMOTE_BROWSER_URL': 'wss://chrome.browserless.io',
            'REMOTE_BROWSER_API_KEY': 'api_key_123',
            'REMOTE_BROWSER_TOKEN': 'token_456'
        }):
            settings = Settings()
            
            assert settings.browser_mode == "remote"
            assert settings.remote_browser_url == "wss://chrome.browserless.io"
            assert settings.remote_browser_api_key == "api_key_123"
            assert settings.remote_browser_token == "token_456"
    
    def test_scraping_configuration(self):
        """测试抓取相关配置"""
        with patch.dict(os.environ, {
            'REQUEST_DELAY_MIN': '0.5',
            'REQUEST_DELAY_MAX': '2.0',
            'MAX_CONCURRENT_REQUESTS': '10',
            'MAX_RETRIES': '5'
        }):
            settings = Settings()
            
            assert settings.request_delay_min == 0.5
            assert settings.request_delay_max == 2.0
            assert settings.max_concurrent_requests == 10
            assert settings.max_retries == 5
    
    def test_cache_configuration(self):
        """测试缓存配置"""
        with patch.dict(os.environ, {
            'CACHE_DB_PATH': '/tmp/test_cache.db',
            'CACHE_TTL': '1800',
            'CACHE_KEY_PREFIX': 'test_prefix:'
        }):
            settings = Settings()
            
            assert settings.cache_db_path == "/tmp/test_cache.db"
            assert settings.cache_ttl == 1800
            assert settings.cache_key_prefix == "test_prefix:"
    
    def test_mcp_configuration(self):
        """测试MCP服务器配置"""
        with patch.dict(os.environ, {
            'MCP_SERVER_NAME': 'test-mcp-server',
            'MCP_SERVER_VERSION': '1.0.0'
        }):
            settings = Settings()
            
            assert settings.mcp_server_name == "test-mcp-server"
            assert settings.mcp_server_version == "1.0.0"
    
    def test_logging_configuration(self):
        """测试日志配置"""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'WARNING',
            'LOG_FORMAT': '{time} - {message}'
        }):
            settings = Settings()
            
            assert settings.log_level == "WARNING"
            assert settings.log_format == "{time} - {message}"
    
    def test_development_environment_preset(self):
        """测试开发环境预设配置"""
        dev_env = {
            'BROWSER_MODE': 'local',
            'BROWSER_HEADLESS': 'false',
            'BROWSER_TIMEOUT': '60000',
            'REQUEST_DELAY_MIN': '0.5',
            'REQUEST_DELAY_MAX': '1.0',
            'LOG_LEVEL': 'DEBUG',
            'MAX_RETRIES': '2'
        }
        
        with patch.dict(os.environ, dev_env):
            settings = Settings()
            
            assert settings.browser_mode == "local"
            assert settings.browser_headless is False
            assert settings.browser_timeout == 60000
            assert settings.request_delay_min == 0.5
            assert settings.request_delay_max == 1.0
            assert settings.log_level == "DEBUG"
            assert settings.max_retries == 2
    
    def test_production_environment_preset(self):
        """测试生产环境预设配置"""
        prod_env = {
            'BROWSER_MODE': 'remote',
            'REMOTE_BROWSER_URL': 'wss://chrome.browserless.io',
            'REMOTE_BROWSER_TOKEN': 'prod_token',
            'BROWSER_HEADLESS': 'true',
            'REQUEST_DELAY_MIN': '2.0',
            'REQUEST_DELAY_MAX': '5.0',
            'MAX_RETRIES': '5',
            'LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, prod_env):
            settings = Settings()
            
            assert settings.browser_mode == "remote"
            assert settings.remote_browser_url == "wss://chrome.browserless.io"
            assert settings.remote_browser_token == "prod_token"
            assert settings.browser_headless is True
            assert settings.request_delay_min == 2.0
            assert settings.request_delay_max == 5.0
            assert settings.max_retries == 5
            assert settings.log_level == "INFO"
    
    def test_boolean_string_conversion(self):
        """测试布尔值字符串转换"""
        boolean_tests = [
            ('true', True),
            ('false', False),
            ('True', True),
            ('False', False),
            ('TRUE', True),
            ('FALSE', False),
            ('1', True),
            ('0', False),
        ]
        
        for str_value, expected_bool in boolean_tests:
            with patch.dict(os.environ, {'BROWSER_HEADLESS': str_value}):
                settings = Settings()
                assert settings.browser_headless is expected_bool, f"Failed for '{str_value}'"
    
    def test_numeric_string_conversion(self):
        """测试数值字符串转换"""
        with patch.dict(os.environ, {
            'BROWSER_TIMEOUT': '45000',
            'REQUEST_DELAY_MIN': '1.5',
            'MAX_CONCURRENT_REQUESTS': '8'
        }):
            settings = Settings()
            
            assert settings.browser_timeout == 45000
            assert settings.request_delay_min == 1.5
            assert settings.max_concurrent_requests == 8
    
    def test_empty_and_none_values(self):
        """测试空值和None值处理"""
        with patch.dict(os.environ, {
            'REMOTE_BROWSER_URL': '',
            'REMOTE_BROWSER_API_KEY': '',
            'LOCAL_BROWSER_EXECUTABLE_PATH': ''
        }):
            settings = Settings(_env_file=None)  # 不使用.env文件
            
            # 空字符串应该被处理为None或保持为空字符串，取决于字段类型
            assert settings.remote_browser_url == ""
            assert settings.remote_browser_api_key == ""
            assert settings.local_browser_executable_path == ""
    
    def test_current_env_file_configuration(self):
        """测试当前.env文件的配置"""
        # 使用实际的.env文件
        settings = Settings()
        
        # 验证.env文件中的配置
        assert settings.browser_mode == "local"
        assert settings.browser_headless is True
        assert settings.browser_timeout == 30000
        assert settings.local_browser_executable_path == "/usr/bin/chromium-browser"
        assert settings.request_delay_min == 1.0
        assert settings.request_delay_max == 3.0
        assert settings.max_concurrent_requests == 5
        assert settings.max_retries == 3


class TestSettingsIntegration:
    """配置集成测试"""
    
    def test_settings_singleton_behavior(self):
        """测试配置单例行为"""
        from src.config import settings
        
        # 验证全局设置实例存在
        assert settings is not None
        assert isinstance(settings, Settings)
        
        # 验证可以访问所有配置属性
        assert hasattr(settings, 'browser_mode')
        assert hasattr(settings, 'cache_db_path')
        assert hasattr(settings, 'log_level')
    
    def test_config_alias_compatibility(self):
        """测试配置别名兼容性"""
        from src.config import Config
        
        # 验证Config别名存在且为Settings类
        assert Config is Settings
    
    @pytest.mark.integration
    def test_real_env_file_loading(self):
        """测试真实.env文件加载（如果存在）"""
        env_file_path = Path(".env")
        
        if env_file_path.exists():
            # 如果项目根目录有.env文件，测试是否能正常加载
            settings = Settings()
            
            # 验证基本配置项存在
            assert settings.browser_mode in ["local", "remote"]
            assert isinstance(settings.browser_headless, bool)
            assert settings.browser_timeout > 0
            assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        else:
            pytest.skip("No .env file found in project root")


class TestConfigValidation:
    """配置验证测试"""
    
    def test_invalid_browser_mode(self):
        """测试无效的浏览器模式"""
        with patch.dict(os.environ, {'BROWSER_MODE': 'invalid_mode'}):
            settings = Settings()
            # 即使设置了无效值，pydantic也会接受字符串，所以我们需要在业务逻辑中验证
            assert settings.browser_mode == "invalid_mode"
    
    def test_invalid_numeric_values(self):
        """测试无效的数字值处理"""
        with patch.dict(os.environ, {
            'BROWSER_TIMEOUT': 'not_a_number',
            'REQUEST_DELAY_MIN': 'invalid'
        }):
            # 这应该抛出验证错误
            with pytest.raises(Exception):  # pydantic会抛出验证错误
                Settings()
    
    def test_negative_values(self):
        """测试负数值处理"""
        with patch.dict(os.environ, {
            'BROWSER_TIMEOUT': '-1000',
            'REQUEST_DELAY_MIN': '-1.0',
            'MAX_RETRIES': '-5'
        }):
            settings = Settings()
            # pydantic会接受负数，业务逻辑需要验证
            assert settings.browser_timeout == -1000
            assert settings.request_delay_min == -1.0
            assert settings.max_retries == -5
    
    def test_extremely_large_values(self):
        """测试极大值处理"""
        with patch.dict(os.environ, {
            'BROWSER_TIMEOUT': '999999999',
            'MAX_CONCURRENT_REQUESTS': '1000'
        }):
            settings = Settings()
            assert settings.browser_timeout == 999999999
            assert settings.max_concurrent_requests == 1000


class TestConfigurationScenarios:
    """实际配置场景测试"""
    
    def test_browserless_io_configuration(self):
        """测试Browserless.io云服务配置"""
        browserless_config = {
            'BROWSER_MODE': 'remote',
            'REMOTE_BROWSER_URL': 'wss://chrome.browserless.io',
            'REMOTE_BROWSER_TOKEN': 'your_token_here',
            'BROWSER_HEADLESS': 'true',
            'BROWSER_TIMEOUT': '45000'
        }
        
        with patch.dict(os.environ, browserless_config):
            settings = Settings()
            
            assert settings.browser_mode == "remote"
            assert settings.remote_browser_url == "wss://chrome.browserless.io"
            assert settings.remote_browser_token == "your_token_here"
            assert settings.browser_headless is True
            assert settings.browser_timeout == 45000
    
    def test_scrapfly_configuration(self):
        """测试ScrapFly服务配置"""
        scrapfly_config = {
            'BROWSER_MODE': 'remote',
            'REMOTE_BROWSER_URL': 'wss://api.scrapfly.io/browser',
            'REMOTE_BROWSER_API_KEY': 'scrapfly_api_key_123',
            'REQUEST_DELAY_MIN': '3.0',
            'REQUEST_DELAY_MAX': '8.0'
        }
        
        with patch.dict(os.environ, scrapfly_config):
            settings = Settings()
            
            assert settings.browser_mode == "remote"
            assert settings.remote_browser_url == "wss://api.scrapfly.io/browser"
            assert settings.remote_browser_api_key == "scrapfly_api_key_123"
            assert settings.request_delay_min == 3.0
            assert settings.request_delay_max == 8.0
    
    def test_docker_browserless_configuration(self):
        """测试Docker Browserless配置"""
        docker_config = {
            'BROWSER_MODE': 'remote',
            'REMOTE_BROWSER_URL': 'ws://localhost:3000',
            'BROWSER_HEADLESS': 'true'
        }
        
        with patch.dict(os.environ, docker_config):
            settings = Settings()
            
            assert settings.browser_mode == "remote"
            assert settings.remote_browser_url == "ws://localhost:3000"
            assert settings.browser_headless is True
            # 应该没有API key或token
            assert settings.remote_browser_api_key is None
            assert settings.remote_browser_token is None
    
    def test_high_performance_configuration(self):
        """测试高性能配置"""
        high_perf_config = {
            'MAX_CONCURRENT_REQUESTS': '20',
            'REQUEST_DELAY_MIN': '0.1',
            'REQUEST_DELAY_MAX': '0.5',
            'BROWSER_TIMEOUT': '15000',
            'MAX_RETRIES': '1',
            'CACHE_TTL': '7200'
        }
        
        with patch.dict(os.environ, high_perf_config):
            settings = Settings()
            
            assert settings.max_concurrent_requests == 20
            assert settings.request_delay_min == 0.1
            assert settings.request_delay_max == 0.5
            assert settings.browser_timeout == 15000
            assert settings.max_retries == 1
            assert settings.cache_ttl == 7200
    
    def test_conservative_configuration(self):
        """测试保守（友好）配置"""
        conservative_config = {
            'MAX_CONCURRENT_REQUESTS': '2',
            'REQUEST_DELAY_MIN': '5.0',
            'REQUEST_DELAY_MAX': '10.0',
            'BROWSER_TIMEOUT': '120000',
            'MAX_RETRIES': '10'
        }
        
        with patch.dict(os.environ, conservative_config):
            settings = Settings()
            
            assert settings.max_concurrent_requests == 2
            assert settings.request_delay_min == 5.0
            assert settings.request_delay_max == 10.0
            assert settings.browser_timeout == 120000
            assert settings.max_retries == 10


class TestConfigurationHelpers:
    """配置辅助功能测试"""
    
    def test_configuration_summary(self):
        """测试配置摘要生成"""
        def get_config_summary(settings: Settings) -> dict:
            """生成配置摘要"""
            return {
                "browser_mode": settings.browser_mode,
                "is_headless": settings.browser_headless,
                "timeout_seconds": settings.browser_timeout / 1000,
                "delay_range": f"{settings.request_delay_min}-{settings.request_delay_max}s",
                "max_retries": settings.max_retries,
                "cache_ttl_hours": settings.cache_ttl / 3600,
                "log_level": settings.log_level
            }
        
        settings = Settings()
        summary = get_config_summary(settings)
        
        assert "browser_mode" in summary
        assert "timeout_seconds" in summary
        assert summary["timeout_seconds"] == 30.0  # 30000ms = 30s
        assert summary["cache_ttl_hours"] == 1.0    # 3600s = 1h
    
    def test_configuration_validation_helper(self):
        """测试配置验证辅助函数"""
        def validate_config(settings: Settings) -> list:
            """验证配置并返回警告列表"""
            warnings = []
            
            if settings.request_delay_min > settings.request_delay_max:
                warnings.append("最小延迟大于最大延迟")
            
            if settings.browser_mode == "remote" and not settings.remote_browser_url:
                warnings.append("远程模式需要配置浏览器URL")
            
            if settings.max_concurrent_requests > 50:
                warnings.append("并发数过高可能导致被限制")
            
            if settings.browser_timeout < 5000:
                warnings.append("超时时间过短可能导致失败")
            
            return warnings
        
        # 测试正常配置
        normal_settings = Settings()
        warnings = validate_config(normal_settings)
        assert len(warnings) == 0
        
        # 测试有问题的配置
        with patch.dict(os.environ, {
            'REQUEST_DELAY_MIN': '5.0',
            'REQUEST_DELAY_MAX': '2.0',  # 最大值小于最小值
            'BROWSER_MODE': 'remote',     # 但没有设置URL
            'MAX_CONCURRENT_REQUESTS': '100',  # 过高并发
            'BROWSER_TIMEOUT': '1000'     # 超时过短
        }):
            problematic_settings = Settings()
            warnings = validate_config(problematic_settings)
            
            assert len(warnings) > 0
            assert any("延迟" in w for w in warnings)
            assert any("URL" in w for w in warnings)
            assert any("并发" in w for w in warnings)
            assert any("超时" in w for w in warnings)


if __name__ == "__main__":
    # 运行测试的示例代码
    pytest.main([__file__, "-v"]) 
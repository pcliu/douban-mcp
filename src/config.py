"""配置管理模块"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序设置"""

    # SQLite数据库配置
    cache_db_path: str = "./data/cache.db"

    # 浏览器配置
    browser_headless: bool = True
    browser_timeout: int = 30000  # 30秒
    browser_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    browser_load_images: bool = True  # 是否加载图片
    browser_viewport_width: int = 1366  # 浏览器viewport宽度
    browser_viewport_height: int = 768  # 浏览器viewport高度
    browser_center_window: bool = True  # 是否将浏览器窗口居中
    
    # 浏览器模式配置 - "local" 或 "remote"
    browser_mode: str = "local"
    
    # 本地浏览器配置
    local_browser_executable_path: str | None = None  # 自定义浏览器路径
    local_browser_args: list[str] = []  # 额外启动参数
    
    # 远程浏览器配置 (如 Browserless, ScrapeOwl 等)
    remote_browser_url: str | None = None  # 远程浏览器websocket URL
    remote_browser_api_key: str | None = None  # API密钥
    remote_browser_token: str | None = None  # 访问令牌

    # 抓取配置
    request_delay_min: float = 1.0  # 最小延迟(秒)
    request_delay_max: float = 3.0  # 最大延迟(秒)
    max_concurrent_requests: int = 5
    max_retries: int = 3

    # 缓存配置
    cache_ttl: int = 3600  # 缓存TTL(秒)
    cache_key_prefix: str = "douban_mcp:"

    # MCP配置
    mcp_server_name: str = "douban-mcp"
    mcp_server_version: str = "0.1.0"

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "{time} | {level} | {name}:{function}:{line} - {message}"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# 全局配置实例
settings = Settings()

# 配置别名，保持向后兼容
Config = Settings

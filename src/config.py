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

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()

# 配置别名，保持向后兼容
Config = Settings

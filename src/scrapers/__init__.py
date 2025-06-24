"""爬虫核心逻辑模块"""

from .browser_manager import browser_manager, BrowserManager
from .base import BaseScraper
from .book_scraper import douban_book_scraper, DoubanBookScraper
from .ai_fallback import ai_fallback_manager, AIFallbackManager

__all__ = [
    "browser_manager",
    "BrowserManager", 
    "BaseScraper",
    "douban_book_scraper",
    "DoubanBookScraper",
    "ai_fallback_manager", 
    "AIFallbackManager",
]

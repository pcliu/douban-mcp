"""豆瓣图书抓取使用示例"""

import asyncio
import os
from pathlib import Path

# 设置项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.book_scraper import search_books, get_book_detail
from src.scrapers.browser_manager import browser_manager
from src.config import settings


async def example_search_books():
    """示例：搜索图书"""
    print("=== 搜索图书示例 ===")
    
    # 搜索关键词
    query = "Python编程"
    
    try:
        result = await search_books(query, limit=5)
        
        print(f"搜索关键词: {result.query}")
        print(f"找到图书数量: {result.total}")
        print(f"当前页: {result.page}")
        
        for i, book in enumerate(result.books, 1):
            print(f"\n第{i}本图书:")
            print(f"  标题: {book.title}")
            print(f"  作者: {', '.join([author.name for author in book.authors])}")
            print(f"  出版社: {book.publisher.name if book.publisher else '未知'}")
            print(f"  出版日期: {book.pubdate or '未知'}")
            print(f"  评分: {book.rating.average if book.rating else '无评分'}")
            print(f"  短评数量: {len(book.short_comments)}")
            print(f"  书评数量: {len(book.reviews)}")
            
    except Exception as e:
        print(f"搜索失败: {e}")


async def example_get_book_detail():
    """示例：获取图书详情"""
    print("\n=== 获取图书详情示例 ===")
    
    # 豆瓣图书ID (例如《Python编程：从入门到实践》)
    book_id = "26435243"
    
    try:
        book = await get_book_detail(book_id)
        
        print(f"图书标题: {book.title}")
        print(f"副标题: {book.subtitle or '无'}")
        print(f"作者: {', '.join([author.name for author in book.authors])}")
        print(f"出版社: {book.publisher.name if book.publisher else '未知'}")
        print(f"出版日期: {book.pubdate or '未知'}")
        print(f"页数: {book.pages or '未知'}")
        print(f"是否可在线阅读: {'是' if book.can_read_online else '否'}")
        
        if book.rating:
            print(f"评分: {book.rating.average}/10 ({book.rating.num_raters}人评价)")
        
        if book.summary:
            print(f"内容简介: {book.summary[:200]}...")
        
        print(f"\n短评 ({len(book.short_comments)}条):")
        for i, comment in enumerate(book.short_comments[:3], 1):
            print(f"  {i}. {comment.user}: {comment.content[:100]}...")
        
        print(f"\n书评 ({len(book.reviews)}条):")
        for i, review in enumerate(book.reviews[:3], 1):
            print(f"  {i}. {review.title} - {review.user}")
            print(f"     {review.content[:100]}...")
            
    except Exception as e:
        print(f"获取详情失败: {e}")


async def example_browser_configuration():
    """示例：浏览器配置展示"""
    print("\n=== 浏览器配置信息 ===")
    
    print(f"当前浏览器模式: {settings.browser_mode}")
    print(f"无头模式: {settings.browser_headless}")
    print(f"超时设置: {settings.browser_timeout}ms")
    print(f"请求延迟: {settings.request_delay_min}-{settings.request_delay_max}秒")
    print(f"最大重试次数: {settings.max_retries}")
    
    # 如果是远程模式，显示远程配置
    if settings.browser_mode == "remote":
        print(f"远程浏览器URL: {settings.remote_browser_url}")
        print(f"API密钥配置: {'已设置' if settings.remote_browser_api_key else '未设置'}")
        print(f"访问令牌配置: {'已设置' if settings.remote_browser_token else '未设置'}")
    
    # 获取浏览器状态
    try:
        info = await browser_manager.get_browser_info()
        print(f"浏览器状态: {info}")
    except Exception as e:
        print(f"无法获取浏览器状态: {e}")


async def example_configuration_switching():
    """示例：配置切换演示"""
    print("\n=== 配置切换演示 ===")
    
    # 注意：这个示例展示如何在代码中动态切换配置
    # 实际使用中建议通过环境变量配置
    
    print("当前配置:")
    await example_browser_configuration()
    
    # 模拟切换到本地模式 (仅演示，实际需要重启服务)
    print("\n模拟切换到本地模式...")
    settings.browser_mode = "local"
    settings.browser_headless = False  # 便于调试
    
    print("新配置:")
    print(f"浏览器模式: {settings.browser_mode}")
    print(f"无头模式: {settings.browser_headless}")


async def main():
    """主函数：运行所有示例"""
    print("豆瓣图书抓取系统示例")
    print("=" * 50)
    
    # 显示配置信息
    await example_browser_configuration()
    
    # 运行搜索示例
    await example_search_books()
    
    # 运行详情获取示例
    await example_get_book_detail()
    
    # 配置切换演示
    await example_configuration_switching()
    
    print("\n" + "=" * 50)
    print("示例运行完成！")


if __name__ == "__main__":
    # 设置示例环境变量
    os.environ.setdefault("BROWSER_MODE", "local")
    os.environ.setdefault("BROWSER_HEADLESS", "true")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # 运行示例
    asyncio.run(main()) 
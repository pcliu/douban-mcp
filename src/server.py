"""MCP服务器主入口"""

import asyncio
from typing import Any

from loguru import logger
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from .config import settings

# 创建服务器实例
server: Server[Any] = Server("douban-mcp")


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """列出可用的资源"""
    return [
        Resource(
            uri=AnyUrl("douban://books"),
            name="豆瓣读书",
            description="豆瓣读书数据抓取",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("douban://movies"),
            name="豆瓣电影",
            description="豆瓣电影数据抓取",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("douban://music"),
            name="豆瓣音乐",
            description="豆瓣音乐数据抓取",
            mimeType="application/json",
        ),
    ]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="search_douban_book",
            description="搜索豆瓣图书信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或ISBN",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_douban_book_detail",
            description="获取豆瓣图书详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "豆瓣图书ID",
                    },
                },
                "required": ["book_id"],
            },
        ),
        Tool(
            name="search_douban_movie",
            description="搜索豆瓣电影信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_douban_movie_detail",
            description="获取豆瓣电影详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "movie_id": {
                        "type": "string",
                        "description": "豆瓣电影ID",
                    },
                },
                "required": ["movie_id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "search_douban_book":
            from .tools.book_scraper import search_books

            search_result = await search_books(
                query=arguments["query"], limit=arguments.get("limit", 10)
            )
            return [TextContent(type="text", text=str(search_result))]

        elif name == "get_douban_book_detail":
            from .tools.book_scraper import get_book_detail

            book_detail = await get_book_detail(book_id=arguments["book_id"])
            return [TextContent(type="text", text=str(book_detail))]

        elif name == "search_douban_movie":
            from .tools.movie_scraper import search_movies

            movie_search_result = await search_movies(
                query=arguments["query"], limit=arguments.get("limit", 10)
            )
            return [TextContent(type="text", text=str(movie_search_result))]

        elif name == "get_douban_movie_detail":
            from .tools.movie_scraper import get_movie_detail

            movie_detail = await get_movie_detail(movie_id=arguments["movie_id"])
            return [TextContent(type="text", text=str(movie_detail))]

        else:
            raise ValueError(f"未知的工具: {name}")

    except Exception as e:
        logger.error(f"工具调用失败: {name}, 错误: {e}")
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def main() -> None:
    """主函数"""
    # 配置日志
    logger.configure(
        handlers=[
            {
                "sink": "logs/douban-mcp.log",
                "level": settings.log_level,
                "format": settings.log_format,
                "rotation": "1 day",
                "retention": "30 days",
            }
        ]
    )

    logger.info(f"启动 {settings.mcp_server_name} v{settings.mcp_server_version}")

    # 运行服务器
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=settings.mcp_server_name,
                server_version=settings.mcp_server_version,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())

"""豆瓣图书抓取工具 - MCP工具实现"""

from typing import List, Dict, Any
from loguru import logger
from mcp import Tool
from pydantic import BaseModel, Field

from ..models.book import Book, BookSearchResult
from ..scrapers.book_scraper import douban_book_scraper


class SearchBooksRequest(BaseModel):
    """搜索图书请求参数"""
    query: str = Field(..., description="搜索关键词或ISBN")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量限制(1-50)")


class GetBookDetailRequest(BaseModel):
    """获取图书详情请求参数"""
    book_id: str = Field(..., description="豆瓣图书ID")


# MCP工具定义
search_books_tool = Tool(
    name="search_books",
    description="搜索豆瓣图书，支持书名、作者、ISBN等关键词搜索",
    inputSchema=SearchBooksRequest.model_json_schema()
)

get_book_detail_tool = Tool(
    name="get_book_detail",
    description="根据豆瓣图书ID获取详细信息，包括基本信息、评分、短评、书评等",
    inputSchema=GetBookDetailRequest.model_json_schema()
)


async def search_books(query: str, limit: int = 10) -> BookSearchResult:
    """搜索豆瓣图书

    Args:
        query: 搜索关键词或ISBN
        limit: 返回结果数量限制

    Returns:
        图书搜索结果
    """
    try:
        logger.info(f"搜索图书: {query}, 限制数量: {limit}")
        
        # 使用爬虫搜索并获取第一本书的详情
        book = await douban_book_scraper.scrape(query=query)
        
        # 包装成搜索结果格式
        return BookSearchResult(
            books=[book],
            total=1,
            query=query,
            page=1,
            per_page=limit
        )
        
    except Exception as e:
        logger.error(f"搜索图书失败: {e}")
        return BookSearchResult(
            books=[],
            total=0,
            query=query,
            page=1,
            per_page=limit
        )


async def get_book_detail(book_id: str) -> Book:
    """获取豆瓣图书详情

    Args:
        book_id: 豆瓣图书ID

    Returns:
        图书详情
    """
    try:
        logger.info(f"获取图书详情: {book_id}")
        return await douban_book_scraper.scrape(book_id=book_id)
        
    except Exception as e:
        logger.error(f"获取图书详情失败: {e}")
        raise


# MCP工具处理函数
async def handle_search_books(request: Dict[str, Any]) -> Dict[str, Any]:
    """处理搜索图书请求"""
    params = SearchBooksRequest(**request)
    result = await search_books(params.query, params.limit)
    return result.model_dump()


async def handle_get_book_detail(request: Dict[str, Any]) -> Dict[str, Any]:
    """处理获取图书详情请求"""
    params = GetBookDetailRequest(**request)
    result = await get_book_detail(params.book_id)
    return result.model_dump()


# 工具注册映射
BOOK_TOOLS = {
    "search_books": {
        "tool": search_books_tool,
        "handler": handle_search_books
    },
    "get_book_detail": {
        "tool": get_book_detail_tool,
        "handler": handle_get_book_detail
    }
}

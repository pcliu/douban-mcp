"""豆瓣图书爬虫实现"""

import re
import asyncio
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from loguru import logger
from playwright.async_api import Page

from .base import BaseScraper
from ..models.book import (
    Book, BookAuthor, BookPublisher, BookRating, BookTag,
    BookComment, BookReview
)


class DoubanBookScraper(BaseScraper[Book]):
    """豆瓣图书爬虫"""
    
    def __init__(self):
        super().__init__("douban_book")
        self.base_url = "https://book.douban.com"
        self.search_url = f"{self.base_url}/search"
    
    def get_cache_key(self, **kwargs) -> str:
        """生成缓存键"""
        book_id = kwargs.get('book_id')
        query = kwargs.get('query')
        
        if book_id:
            return f"{self.cache_prefix}detail:{book_id}"
        elif query:
            return f"{self.cache_prefix}search:{query}"
        else:
            raise ValueError("必须提供 book_id 或 query 参数")
    
    async def scrape_with_playwright(self, page: Page, **kwargs) -> Book:
        """使用固定Playwright脚本抓取图书数据"""
        book_id = kwargs.get('book_id')
        query = kwargs.get('query')
        
        if book_id:
            return await self._scrape_book_detail_fixed(page, book_id)
        elif query:
            return await self._search_and_scrape_first_book_fixed(page, query)
        else:
            raise ValueError("必须提供 book_id 或 query 参数")
    
    async def scrape_with_browser_use(self, page: Page, **kwargs) -> Book:
        """使用browser-use AI降级抓取图书数据"""
        from .ai_fallback import ai_fallback_manager
        
        book_id = kwargs.get('book_id')
        query = kwargs.get('query')
        
        try:
            if book_id:
                # 先导航到图书详情页
                book_url = f"{self.base_url}/subject/{book_id}/"
                await page.goto(book_url)
                await page.wait_for_load_state('networkidle')
                
                # 使用AI降级提取详情
                ai_result = await ai_fallback_manager.fallback_extract_detail(page, book_id)
            elif query:
                # 先导航到豆瓣读书首页
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                
                # 使用AI降级搜索并提取
                ai_result = await ai_fallback_manager.fallback_search_book(page, query)
                # 从结果中提取book_id
                book_id = ai_result.get('id') or self._extract_book_id_from_url(ai_result.get('url', ''))
            else:
                raise ValueError("必须提供 book_id 或 query 参数")
            
            # 将AI结果转换为Book对象
            return self._convert_ai_result_to_book(ai_result, book_id)
            
        except Exception as e:
            logger.error(f"browser-use AI降级失败: {e}")
            # 如果AI降级也失败，尝试使用固定脚本作为最后手段
            logger.info("AI降级失败，尝试使用固定脚本作为最后手段")
            return await self.scrape_with_playwright(page, **kwargs)
    
    def _convert_ai_result_to_book(self, ai_result: Dict[str, Any], book_id: str) -> Book:
        """将AI降级结果转换为Book对象"""
        # 提取基本信息
        title = ai_result.get('title', '未知标题')
        subtitle = ai_result.get('subtitle')
        
        # 处理作者信息
        authors = []
        author_data = ai_result.get('authors', [])
        if isinstance(author_data, list):
            for author in author_data:
                if isinstance(author, dict):
                    authors.append(BookAuthor(
                        name=author.get('name', ''),
                        url=author.get('url')
                    ))
                elif isinstance(author, str):
                    authors.append(BookAuthor(name=author))
        
        # 处理出版社
        publisher = None
        pub_data = ai_result.get('publisher')
        if isinstance(pub_data, dict):
            publisher = BookPublisher(name=pub_data.get('name', ''))
        elif isinstance(pub_data, str):
            publisher = BookPublisher(name=pub_data)
        
        # 处理评分
        rating = None
        rating_data = ai_result.get('rating')
        if isinstance(rating_data, dict):
            rating = BookRating(
                average=rating_data.get('average'),
                num_raters=rating_data.get('num_raters')
            )
        
        # 处理短评
        short_comments = []
        comments_data = ai_result.get('short_comments', [])
        for comment in comments_data[:5]:
            if isinstance(comment, dict):
                short_comments.append(BookComment(
                    user=comment.get('user', '匿名用户'),
                    time=comment.get('time', ''),
                    rating=comment.get('rating'),
                    content=comment.get('content', '')
                ))
        
        # 处理书评
        reviews = []
        reviews_data = ai_result.get('reviews', [])
        for review in reviews_data[:10]:
            if isinstance(review, dict):
                reviews.append(BookReview(
                    user=review.get('user', '匿名用户'),
                    time=review.get('time', ''),
                    title=review.get('title', '无标题'),
                    rating=review.get('rating'),
                    content=review.get('content', '')
                ))
        
        # 构建图书URL
        book_url = ai_result.get('url', f"{self.base_url}/subject/{book_id}/")
        
        return Book(
            id=book_id or ai_result.get('id', 'unknown'),
            title=title,
            subtitle=subtitle,
            authors=authors,
            publisher=publisher,
            pubdate=ai_result.get('pubdate'),
            pages=ai_result.get('pages'),
            summary=ai_result.get('summary'),
            rating=rating,
            can_read_online=ai_result.get('can_read_online', False),
            short_comments=short_comments,
            reviews=reviews,
            url=book_url,
            image=ai_result.get('image'),
            scraped_at=self.get_current_timestamp()
        )
    
    async def _search_and_scrape_first_book_fixed(self, page: Page, query: str) -> Book:
        """搜索并抓取第一本书的详情"""
        logger.info(f"搜索图书: {query}")
        
        # 1. 访问豆瓣读书首页
        await page.goto(self.base_url)
        await self.random_delay(1, 2)
        
        # 2. 在搜索框输入书名
        search_input = 'input[name="search_text"], #inp-query'
        if not await self.safe_fill(page, search_input, query):
            raise Exception("无法找到搜索输入框")
        
        # 3. 点击搜索按钮
        search_button = 'input[type="submit"], .bn-submit'
        if not await self.safe_click(page, search_button):
            # 尝试按Enter键
            await page.keyboard.press('Enter')
        
        await page.wait_for_load_state('networkidle')
        await self.random_delay(2, 3)
        
        # 4. 获取第一个搜索结果的链接
        first_book_link = await self.extract_attribute(
            page, 
            '.item-root .title a, .subject-list .subject .info h2 a', 
            'href'
        )
        
        if not first_book_link:
            raise Exception("未找到搜索结果")
        
        # 5. 提取book_id并访问详情页
        book_id = self._extract_book_id_from_url(first_book_link)
        if not book_id:
            raise Exception("无法提取图书ID")
        
        return await self._scrape_book_detail_fixed(page, book_id)
    
    async def _scrape_book_detail_fixed(self, page: Page, book_id: str) -> Book:
        """抓取图书详情页面"""
        book_url = f"{self.base_url}/subject/{book_id}/"
        logger.info(f"抓取图书详情: {book_url}")
        
        await page.goto(book_url)
        await page.wait_for_load_state('networkidle')
        await self.random_delay(2, 3)
        
        # 基本信息
        title = await self._extract_title(page)
        subtitle = await self._extract_subtitle(page)
        authors = await self._extract_authors(page)
        publisher = await self._extract_publisher(page)
        pubdate = await self._extract_pubdate(page)
        pages = await self._extract_pages(page)
        summary = await self._extract_summary(page)
        rating = await self._extract_rating(page)
        can_read_online = await self._check_can_read_online(page)
        image = await self._extract_cover_image(page)
        
        # 抓取评论数据
        short_comments = await self._extract_short_comments(page)
        reviews = await self._extract_reviews(page)
        
        return Book(
            id=book_id,
            title=title,
            subtitle=subtitle,
            authors=authors,
            publisher=publisher,
            pubdate=pubdate,
            pages=pages,
            summary=summary,
            rating=rating,
            can_read_online=can_read_online,
            short_comments=short_comments,
            reviews=reviews,
            url=book_url,
            image=image,
            scraped_at=self.get_current_timestamp()
        )
    
    def _extract_book_id_from_url(self, url: str) -> Optional[str]:
        """从URL中提取图书ID"""
        match = re.search(r'/subject/(\d+)/', url)
        return match.group(1) if match else None
    
    async def _extract_title(self, page: Page) -> str:
        """提取图书标题"""
        title = await self.extract_text(page, 'h1 span[property="v:itemreviewed"]')
        if not title:
            title = await self.extract_text(page, 'h1')
        return title or "未知标题"
    
    async def _extract_subtitle(self, page: Page) -> Optional[str]:
        """提取副标题"""
        # 豆瓣通常将副标题包含在主标题中，用冒号分隔
        title = await self._extract_title(page)
        if ':' in title:
            parts = title.split(':', 1)
            return parts[1].strip() if len(parts) > 1 else None
        return None
    
    async def _extract_authors(self, page: Page) -> List[BookAuthor]:
        """提取作者信息"""
        authors = []
        
        # 尝试多个选择器
        selectors = [
            '#info a[href*="/author/"]',
            '.author a',
            '#info span:contains("作者") + a'
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    name = await element.text_content()
                    url = await element.get_attribute('href')
                    if name and name.strip():
                        authors.append(BookAuthor(
                            name=name.strip(),
                            url=urljoin(self.base_url, url) if url else None
                        ))
                if authors:
                    break
            except Exception as e:
                logger.debug(f"提取作者失败 {selector}: {e}")
        
        return authors
    
    async def _extract_publisher(self, page: Page) -> Optional[BookPublisher]:
        """提取出版社信息"""
        # 尝试从info区域提取出版社
        info_text = await self.extract_text(page, '#info')
        if info_text:
            # 查找出版社信息
            pub_match = re.search(r'出版社:\s*([^\n]+)', info_text)
            if pub_match:
                return BookPublisher(name=pub_match.group(1).strip())
        
        return None
    
    async def _extract_pubdate(self, page: Page) -> Optional[str]:
        """提取出版日期"""
        info_text = await self.extract_text(page, '#info')
        if info_text:
            # 查找出版时间
            date_match = re.search(r'出版年:\s*([^\n]+)', info_text)
            if date_match:
                return date_match.group(1).strip()
        
        return None
    
    async def _extract_pages(self, page: Page) -> Optional[int]:
        """提取页数"""
        info_text = await self.extract_text(page, '#info')
        if info_text:
            # 查找页数
            pages_match = re.search(r'页数:\s*(\d+)', info_text)
            if pages_match:
                return int(pages_match.group(1))
        
        return None
    
    async def _extract_summary(self, page: Page) -> Optional[str]:
        """提取内容简介"""
        summary = await self.extract_text(page, '#link-report .intro, .intro')
        return summary.strip() if summary else None
    
    async def _extract_rating(self, page: Page) -> Optional[BookRating]:
        """提取评分信息"""
        try:
            # 平均评分
            score_text = await self.extract_text(page, '.rating_num')
            average = float(score_text) if score_text else None
            
            # 评分人数
            count_text = await self.extract_text(page, '.rating_people span')
            if count_text:
                count_match = re.search(r'(\d+)', count_text)
                num_raters = int(count_match.group(1)) if count_match else None
            else:
                num_raters = None
            
            if average or num_raters:
                return BookRating(average=average, num_raters=num_raters)
        
        except Exception as e:
            logger.debug(f"提取评分失败: {e}")
        
        return None
    
    async def _check_can_read_online(self, page: Page) -> bool:
        """检查是否可在线阅读"""
        # 查找在线阅读链接
        read_link = await page.query_selector('a[href*="read"]')
        return read_link is not None
    
    async def _extract_cover_image(self, page: Page) -> Optional[str]:
        """提取封面图片"""
        return await self.extract_attribute(page, '#mainpic img', 'src')
    
    async def _extract_short_comments(self, page: Page) -> List[BookComment]:
        """提取短评"""
        comments = []
        
        try:
            # 查找短评区域
            comment_elements = await page.query_selector_all('.comment-item, .short-comment')
            
            for element in comment_elements[:5]:  # 最多5条短评
                try:
                    user = await element.query_selector('.comment-info a')
                    user_name = await user.text_content() if user else "匿名用户"
                    
                    time_elem = await element.query_selector('.comment-time')
                    time_text = await time_elem.text_content() if time_elem else ""
                    
                    content_elem = await element.query_selector('.short, .comment-content')
                    content = await content_elem.text_content() if content_elem else ""
                    
                    # 尝试提取评分
                    rating_elem = await element.query_selector('.rating')
                    rating = None
                    if rating_elem:
                        rating_class = await rating_elem.get_attribute('class')
                        if rating_class:
                            rating_match = re.search(r'allstar(\d)0', rating_class)
                            rating = int(rating_match.group(1)) if rating_match else None
                    
                    if user_name and content:
                        comments.append(BookComment(
                            user=user_name.strip(),
                            time=time_text.strip(),
                            rating=rating,
                            content=content.strip()
                        ))
                
                except Exception as e:
                    logger.debug(f"提取单条短评失败: {e}")
                    continue
        
        except Exception as e:
            logger.debug(f"提取短评失败: {e}")
        
        return comments
    
    async def _extract_reviews(self, page: Page) -> List[BookReview]:
        """提取书评"""
        reviews = []
        
        try:
            # 查找书评区域
            review_elements = await page.query_selector_all('.review-item, .review')
            
            for element in review_elements[:10]:  # 最多10条书评
                try:
                    user_elem = await element.query_selector('.review-info a, .reviewer a')
                    user_name = await user_elem.text_content() if user_elem else "匿名用户"
                    
                    time_elem = await element.query_selector('.review-time, .review-date')
                    time_text = await time_elem.text_content() if time_elem else ""
                    
                    title_elem = await element.query_selector('.review-title a, .title a')
                    title = await title_elem.text_content() if title_elem else "无标题"
                    
                    content_elem = await element.query_selector('.review-content, .content')
                    content = await content_elem.text_content() if content_elem else ""
                    
                    # 尝试提取评分
                    rating_elem = await element.query_selector('.rating')
                    rating = None
                    if rating_elem:
                        rating_class = await rating_elem.get_attribute('class')
                        if rating_class:
                            rating_match = re.search(r'allstar(\d)0', rating_class)
                            rating = int(rating_match.group(1)) if rating_match else None
                    
                    if user_name and title and content:
                        reviews.append(BookReview(
                            user=user_name.strip(),
                            time=time_text.strip(),
                            title=title.strip(),
                            rating=rating,
                            content=content.strip()
                        ))
                
                except Exception as e:
                    logger.debug(f"提取单条书评失败: {e}")
                    continue
        
        except Exception as e:
            logger.debug(f"提取书评失败: {e}")
        
        return reviews


# 全局爬虫实例
douban_book_scraper = DoubanBookScraper() 
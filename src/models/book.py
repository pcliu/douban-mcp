"""豆瓣图书数据模型"""


from pydantic import BaseModel, Field


class BookAuthor(BaseModel):
    """图书作者模型"""

    name: str = Field(..., description="作者姓名")
    url: str | None = Field(None, description="作者豆瓣链接")


class BookPublisher(BaseModel):
    """出版社模型"""

    name: str = Field(..., description="出版社名称")


class BookRating(BaseModel):
    """图书评分模型"""

    average: float | None = Field(None, description="平均评分")
    num_raters: int | None = Field(None, description="评分人数")
    rating_5: int | None = Field(None, description="5星评分数量")
    rating_4: int | None = Field(None, description="4星评分数量")
    rating_3: int | None = Field(None, description="3星评分数量")
    rating_2: int | None = Field(None, description="2星评分数量")
    rating_1: int | None = Field(None, description="1星评分数量")


class BookTag(BaseModel):
    """图书标签模型"""

    name: str = Field(..., description="标签名称")
    count: int | None = Field(None, description="标签使用次数")


class BookComment(BaseModel):
    """图书短评模型"""
    
    user: str = Field(..., description="用户名")
    time: str = Field(..., description="评论时间")
    rating: int | None = Field(None, description="评分(1-5星)")
    content: str = Field(..., description="评论内容")


class BookReview(BaseModel):
    """图书书评模型"""
    
    user: str = Field(..., description="评论者")
    time: str = Field(..., description="评论时间")
    title: str = Field(..., description="评论标题")
    rating: int | None = Field(None, description="评分(1-5星)")
    content: str = Field(..., description="评论详细内容")


class Book(BaseModel):
    """豆瓣图书模型"""

    id: str = Field(..., description="豆瓣图书ID")
    title: str = Field(..., description="图书标题")
    subtitle: str | None = Field(None, description="图书副标题")
    alt_title: str | None = Field(None, description="原作名")

    # 作者信息
    authors: list[BookAuthor] = Field(default_factory=list, description="作者列表")
    translators: list[BookAuthor] = Field(default_factory=list, description="译者列表")

    # 出版信息
    publisher: BookPublisher | None = Field(None, description="出版社")
    pubdate: str | None = Field(None, description="出版日期")
    isbn10: str | None = Field(None, description="ISBN-10")
    isbn13: str | None = Field(None, description="ISBN-13")
    pages: int | None = Field(None, description="页数")
    price: str | None = Field(None, description="定价")
    binding: str | None = Field(None, description="装帧")

    # 内容信息
    summary: str | None = Field(None, description="内容简介")
    author_intro: str | None = Field(None, description="作者简介")
    catalog: str | None = Field(None, description="目录")
    can_read_online: bool = Field(False, description="是否可在线阅读")

    # 评分和标签
    rating: BookRating | None = Field(None, description="评分信息")
    tags: list[BookTag] = Field(default_factory=list, description="标签列表")
    
    # 用户评论
    short_comments: list[BookComment] = Field(default_factory=list, description="短评列表")
    reviews: list[BookReview] = Field(default_factory=list, description="书评列表")

    # 其他信息
    url: str = Field(..., description="豆瓣链接")
    alt: str | None = Field(None, description="豆瓣链接(备用)")
    image: str | None = Field(None, description="封面图片链接")
    images: list[str] = Field(default_factory=list, description="图片链接列表")

    # 元数据
    scraped_at: str | None = Field(None, description="抓取时间")
    source: str = Field(default="douban", description="数据来源")


class BookSearchResult(BaseModel):
    """图书搜索结果模型"""

    books: list[Book] = Field(default_factory=list, description="图书列表")
    total: int = Field(0, description="总结果数")
    query: str = Field(..., description="搜索关键词")
    page: int = Field(1, description="当前页码")
    per_page: int = Field(10, description="每页结果数")

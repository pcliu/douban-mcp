## 图书
### 图书抓取规则

1. 先进入豆瓣读书首页：https://book.douban.com/
2. 在输入框中输入书名，点击查询
3. 选择第一本书
4. 点击书名
5. 进入到详细页面后，抓取图书信息


### 要抓取的图书信息

{
  "book": {
    "title": "图书名称",
    "pubdate": "2024-01-01",
    "pages": 300,
    "rating": {
      "score": 8.5,
      "count": 1234
    },
    "summary": "内容简介文本",
    "can_read_online": false,
    "short_comments": [
      {
        "user": "用户名1",
        "time": "2024-01-15",
        "rating": 4,
        "content": "短评内容1"
      },
      {
        "user": "用户名2", 
        "time": "2024-01-14",
        "rating": 5,
        "content": "短评内容2"
      },
      {
        "user": "用户名3",
        "time": "2024-01-13", 
        "rating": 3,
        "content": "短评内容3"
      },
      {
        "user": "用户名4",
        "time": "2024-01-12",
        "rating": 4,
        "content": "短评内容4"
      },
      {
        "user": "用户名5",
        "time": "2024-01-11",
        "rating": 5,
        "content": "短评内容5"
      }
    ],
    "reviews": [
      {
        "user": "评论者1",
        "time": "2024-01-15",
        "title": "评论标题1",
        "rating": 5,
        "content": "评论详细内容1"
      },
      {
        "user": "评论者2",
        "time": "2024-01-14", 
        "title": "评论标题2",
        "rating": 4,
        "content": "评论详细内容2"
      },
      {
        "user": "评论者3",
        "time": "2024-01-13",
        "title": "评论标题3", 
        "rating": 3,
        "content": "评论详细内容3"
      },
      {
        "user": "评论者4",
        "time": "2024-01-12",
        "title": "评论标题4",
        "rating": 5,
        "content": "评论详细内容4"
      },
      {
        "user": "评论者5",
        "time": "2024-01-11",
        "title": "评论标题5",
        "rating": 4,
        "content": "评论详细内容5"
      },
      {
        "user": "评论者6",
        "time": "2024-01-10",
        "title": "评论标题6",
        "rating": 5,
        "content": "评论详细内容6"
      },
      {
        "user": "评论者7",
        "time": "2024-01-09",
        "title": "评论标题7",
        "rating": 3,
        "content": "评论详细内容7"
      },
      {
        "user": "评论者8",
        "time": "2024-01-08",
        "title": "评论标题8",
        "rating": 4,
        "content": "评论详细内容8"
      },
      {
        "user": "评论者9",
        "time": "2024-01-07",
        "title": "评论标题9",
        "rating": 5,
        "content": "评论详细内容9"
      },
      {
        "user": "评论者10",
        "time": "2024-01-06",
        "title": "评论标题10",
        "rating": 4,
        "content": "评论详细内容10"
      }
    ]
  }
}



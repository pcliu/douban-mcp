# 浏览器配置指南

本项目支持灵活的浏览器配置，可以使用本地浏览器或云端浏览器服务。

## 配置方式

### 环境变量配置

创建 `.env` 文件来配置浏览器选项：

```bash
# 浏览器模式: "local" (本地) 或 "remote" (云端)
BROWSER_MODE=local

# 基础配置
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
```

## 本地浏览器配置

### 基本配置

```bash
# 使用本地浏览器
BROWSER_MODE=local
BROWSER_HEADLESS=true

# 可选：指定自定义浏览器路径
LOCAL_BROWSER_EXECUTABLE_PATH="/usr/bin/chromium-browser"

# 可选：额外启动参数
LOCAL_BROWSER_ARGS=["--disable-web-security", "--disable-features=VizDisplayCompositor"]
```

### 优点

- 无需外部依赖
- 成本低
- 完全控制浏览器环境
- 适合开发和测试

### 缺点

- 需要本地安装浏览器
- 资源消耗较大
- 可能面临反爬虫检测

## 云端浏览器配置

### Browserless.io

```bash
BROWSER_MODE=remote
REMOTE_BROWSER_URL=wss://chrome.browserless.io
REMOTE_BROWSER_TOKEN=YOUR_TOKEN_HERE
```

### 自建 Browserless Docker

```bash
# 启动Browserless容器
docker run -p 3000:3000 browserless/chrome

# 配置连接
BROWSER_MODE=remote
REMOTE_BROWSER_URL=ws://localhost:3000
```

### ScrapeOwl

```bash
BROWSER_MODE=remote
REMOTE_BROWSER_URL=wss://api.scrapeowl.com/v1/browser
REMOTE_BROWSER_API_KEY=YOUR_API_KEY_HERE
```

### 优点

- 无需本地资源
- 专业反爬虫技术
- 高可用性
- 易于扩展

### 缺点

- 需要付费订阅
- 网络延迟
- 依赖外部服务

## 配置示例

### 开发环境（本地）

```bash
BROWSER_MODE=local
BROWSER_HEADLESS=false  # 便于调试
BROWSER_TIMEOUT=60000
REQUEST_DELAY_MIN=0.5
REQUEST_DELAY_MAX=1.0
LOG_LEVEL=DEBUG
```

### 生产环境（云端）

```bash
BROWSER_MODE=remote
REMOTE_BROWSER_URL=wss://chrome.browserless.io
REMOTE_BROWSER_TOKEN=prod_token_here
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
REQUEST_DELAY_MIN=2.0
REQUEST_DELAY_MAX=5.0
MAX_RETRIES=5
LOG_LEVEL=INFO
```

## 切换配置

项目支持运行时动态切换浏览器模式，只需更新环境变量并重启服务：

```python
from src.config import settings

# 检查当前配置
print(f"当前浏览器模式: {settings.browser_mode}")
print(f"是否无头模式: {settings.browser_headless}")

# 获取浏览器信息
from src.scrapers.browser_manager import browser_manager
info = await browser_manager.get_browser_info()
print(f"浏览器状态: {info}")
```

## 故障排除

### 本地浏览器问题

1. **浏览器未安装**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install chromium-browser
   
   # 通过playwright安装
   uv run playwright install chromium
   ```

2. **权限问题**
   ```bash
   # 添加必要参数
   LOCAL_BROWSER_ARGS=["--no-sandbox", "--disable-setuid-sandbox"]
   ```

### 云端浏览器问题

1. **连接失败**
   - 检查URL和认证信息
   - 确认网络连接
   - 验证服务状态

2. **认证错误**
   - 检查API密钥格式
   - 确认令牌有效性
   - 查看服务商文档

## 性能优化

### 请求拦截

项目自动拦截不必要的资源请求以提高性能：

```python
# 在browser_manager.py中配置
async def _setup_request_interception(self):
    # 跳过图片、字体、样式表等
    if resource_type in ["image", "font", "stylesheet", "media"]:
        await route.abort()
```

### 并发控制

```bash
# 控制并发请求数量
MAX_CONCURRENT_REQUESTS=5

# 设置请求延迟
REQUEST_DELAY_MIN=1.0
REQUEST_DELAY_MAX=3.0
```

## 监控和调试

### 浏览器状态监控

```python
# 获取浏览器信息
info = await browser_manager.get_browser_info()
print(f"状态: {info['status']}")
print(f"模式: {info['mode']}")
print(f"版本: {info['version']}")
```

### 调试模式

```bash
# 启用可视化调试
BROWSER_HEADLESS=false
LOG_LEVEL=DEBUG

# 增加超时时间
BROWSER_TIMEOUT=120000
``` 
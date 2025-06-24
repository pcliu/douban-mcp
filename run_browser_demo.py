#!/usr/bin/env python3
"""
BrowserManager 演示脚本
展示如何启动和使用浏览器管理器
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers.browser_manager import browser_manager
from src.config import settings


async def demo_browser_startup():
    """演示浏览器启动和基本功能"""
    print("🚀 BrowserManager 演示程序")
    print("=" * 50)
    
    try:
        # 显示当前配置
        print("📋 当前配置:")
        print(f"  浏览器模式: {settings.browser_mode}")
        print(f"  无头模式: {settings.browser_headless}")
        print(f"  超时设置: {settings.browser_timeout}ms")
        print(f"  请求延迟: {settings.request_delay_min}-{settings.request_delay_max}秒")
        print()
        
        # 启动浏览器
        print("🔄 正在启动浏览器...")
        await browser_manager.start()
        
        # 获取浏览器信息
        info = await browser_manager.get_browser_info()
        print("✅ 浏览器启动成功!")
        print(f"  状态: {info['status']}")
        print(f"  模式: {info['mode']}")
        print(f"  无头模式: {info['headless']}")
        print(f"  版本: {info['version']}")
        print(f"  上下文数量: {info['contexts']}")
        print()
        
        # 创建新页面
        print("📄 创建新页面...")
        page = await browser_manager.new_page()
        print("✅ 页面创建成功!")
        
        # 访问一个简单的网页进行测试
        print("🌐 访问测试页面...")
        await page.goto("https://book.douban.com/subject/36062390/")
        
        # 获取页面标题
        title = await page.title()
        print(f"✅ 页面标题: {title}")
        
        # 获取用户代理
        user_agent_text = await page.text_content("body")
        print(f"🤖 当前用户代理: {user_agent_text.strip()}")
        
        # 等待几秒钟让用户看到结果
        print("\n⏳ 浏览器将保持运行5秒钟...")
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭浏览器
        print("\n🔄 正在关闭浏览器...")
        await browser_manager.close()
        print("✅ 浏览器已关闭")


async def demo_context_manager():
    """演示使用异步上下文管理器"""
    print("\n🎭 异步上下文管理器演示")
    print("=" * 50)
    
    try:
        async with browser_manager as manager:
            print("✅ 使用上下文管理器启动浏览器")
            
            info = await manager.get_browser_info()
            print(f"📊 浏览器状态: {info['status']}")
            
            # 创建页面并快速测试
            page = await manager.new_page()
            await page.goto("https://book.douban.com/subject/36062390/")
            
            # 获取页面内容
            content = await page.text_content("body")
            print("🔍 获取到页面headers信息")
            
            print("⏳ 等待3秒钟...")
            await asyncio.sleep(3)
            
        print("✅ 上下文管理器自动关闭浏览器")
        
    except Exception as e:
        print(f"❌ 上下文管理器演示出错: {e}")


async def main():
    """主函数"""
    print("🎯 BrowserManager 完整演示")
    print("这个演示将展示浏览器管理器的各种功能\n")
    
    # 基本启动演示
    await demo_browser_startup()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 上下文管理器演示
    await demo_context_manager()
    
    print("\n🎉 演示完成！")
    print("BrowserManager 功能已成功验证。")


if __name__ == "__main__":
    # 设置环境变量
    import os
    os.environ.setdefault("BROWSER_MODE", "local")
    os.environ.setdefault("BROWSER_HEADLESS", "false")  # 显示浏览器窗口
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # 运行演示
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  演示被用户中断")
    except Exception as e:
        print(f"\n💥 演示程序异常退出: {e}")
        import traceback
        traceback.print_exc() 
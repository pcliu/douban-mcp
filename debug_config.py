#!/usr/bin/env python3
"""配置调试脚本 - 分析为什么浏览器不显示窗口"""

import os
import sys
from pathlib import Path

print("🔍 配置调试分析")
print("=" * 50)

# 1. 检查环境变量设置
print("📋 步骤1: 设置环境变量")
print("设置前的环境变量:")
print(f"  BROWSER_HEADLESS = {os.environ.get('BROWSER_HEADLESS', '未设置')}")

# 设置环境变量
os.environ["BROWSER_MODE"] = "local"
os.environ["BROWSER_HEADLESS"] = "false"  # 注意：这里是字符串
os.environ["LOG_LEVEL"] = "INFO"

print("设置后的环境变量:")
print(f"  BROWSER_HEADLESS = {os.environ.get('BROWSER_HEADLESS', '未设置')}")
print()

# 2. 导入配置并检查
print("📋 步骤2: 导入配置模块")
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings

print("导入后的配置值:")
print(f"  settings.browser_headless = {settings.browser_headless}")
print(f"  settings.browser_mode = {settings.browser_mode}")
print(f"  settings.log_level = {settings.log_level}")
print()

# 3. 分析配置类型
print("📋 步骤3: 配置值类型分析")
print(f"  browser_headless 类型: {type(settings.browser_headless)}")
print(f"  环境变量 BROWSER_HEADLESS 类型: {type(os.environ.get('BROWSER_HEADLESS'))}")
print()

# 4. 测试 pydantic settings 的字符串转换
print("📋 步骤4: Pydantic Settings 字符串转换测试")
from src.config import Settings

# 测试不同的字符串值
test_values = ["false", "False", "FALSE", "0", "no", "No", "true", "True", "TRUE", "1", "yes", "Yes"]

print("测试各种字符串值的布尔转换:")
for val in test_values:
    os.environ["TEST_BOOL"] = val
    
    # 临时创建一个测试配置类
    from pydantic_settings import BaseSettings
    
    class TestSettings(BaseSettings):
        test_bool: bool = True
        
        model_config = {
            "env_file": ".env",
            "case_sensitive": False,
            "env_prefix": ""
        }
    
    test_settings = TestSettings()
    print(f"  '{val}' -> {test_settings.test_bool}")

print()

# 5. 检查 .env 文件
print("📋 步骤5: 检查 .env 文件")
env_file = Path(".env")
if env_file.exists():
    print(f"✅ 发现 .env 文件: {env_file.absolute()}")
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if content:
            print("📄 .env 文件内容:")
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    print(f"  {line}")
        else:
            print("⚠️ .env 文件为空")
    except Exception as e:
        print(f"❌ 读取 .env 文件失败: {e}")
else:
    print("ℹ️ 未找到 .env 文件")

print()

# 6. 建议的解决方案
print("💡 问题分析和解决方案:")
print("=" * 50)

if settings.browser_headless:
    print("❌ 问题确认: 浏览器在无头模式下运行")
    print("🔧 可能的原因:")
    print("  1. 环境变量设置时机问题（在导入settings之后设置）")
    print("  2. .env文件中有BROWSER_HEADLESS=true配置")
    print("  3. Pydantic字符串转布尔值的规则")
    print()
    print("🎯 解决方案:")
    print("  1. 在脚本最开始设置环境变量（在任何导入之前）")
    print("  2. 创建 .env 文件并设置 BROWSER_HEADLESS=false")
    print("  3. 直接传递参数重新创建Settings实例")
    print("  4. 使用系统环境变量设置")
else:
    print("✅ 配置正确: 浏览器应该显示窗口")
    print("🤔 如果仍然没有窗口，可能的原因:")
    print("  1. 在SSH/远程会话中运行")
    print("  2. 缺少显示服务器")
    print("  3. 防火墙或安全软件阻止")

print()
print("🚀 推荐的立即解决方法:")
print("在当前终端中运行:")
print("set BROWSER_HEADLESS=false && python run_browser_demo.py") 
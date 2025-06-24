#!/usr/bin/env python3
"""配置测试运行脚本"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from src.config import settings


def print_current_config():
    """打印当前配置"""
    print("=" * 60)
    print("当前配置信息")
    print("=" * 60)
    
    print(f"浏览器模式: {settings.browser_mode}")
    print(f"无头模式: {settings.browser_headless}")
    print(f"浏览器超时: {settings.browser_timeout}ms")
    print(f"请求延迟: {settings.request_delay_min}-{settings.request_delay_max}s")
    print(f"最大重试: {settings.max_retries}")
    print(f"并发请求: {settings.max_concurrent_requests}")
    print(f"缓存TTL: {settings.cache_ttl}s")
    print(f"日志级别: {settings.log_level}")
    
    if settings.browser_mode == "remote":
        print(f"远程浏览器URL: {settings.remote_browser_url}")
        print(f"API密钥: {'已设置' if settings.remote_browser_api_key else '未设置'}")
        print(f"访问令牌: {'已设置' if settings.remote_browser_token else '未设置'}")
    
    print("=" * 60)


def run_basic_tests():
    """运行基础配置测试"""
    print("\n🧪 运行基础配置测试...")
    
    # 运行特定的测试类
    result = pytest.main([
        "tests/test_config.py::TestSettings::test_default_values",
        "tests/test_config.py::TestSettings::test_env_file_loading", 
        "tests/test_config.py::TestSettings::test_environment_variables_priority",
        "-v"
    ])
    
    return result == 0


def run_scenario_tests():
    """运行配置场景测试"""
    print("\n🚀 运行配置场景测试...")
    
    result = pytest.main([
        "tests/test_config.py::TestConfigurationScenarios",
        "-v"
    ])
    
    return result == 0


def run_validation_tests():
    """运行配置验证测试"""
    print("\n✅ 运行配置验证测试...")
    
    result = pytest.main([
        "tests/test_config.py::TestConfigValidation",
        "-v"
    ])
    
    return result == 0


def run_all_config_tests():
    """运行所有配置测试"""
    print("\n🔥 运行所有配置测试...")
    
    result = pytest.main([
        "tests/test_config.py",
        "-v",
        "--tb=short"
    ])
    
    return result == 0


def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 运行集成测试...")
    
    result = pytest.main([
        "tests/test_config.py::TestSettingsIntegration",
        "-v"
    ])
    
    return result == 0


def check_env_file():
    """检查.env文件"""
    env_file = Path(".env")
    
    if env_file.exists():
        print(f"✅ 找到.env文件: {env_file.absolute()}")
        
        # 读取并显示配置
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                
                if lines:
                    print("\n📋 .env文件中的配置项:")
                    for line in lines[:10]:  # 显示前10行
                        if '=' in line:
                            key, value = line.split('=', 1)
                            print(f"  {key}: {value}")
                    
                    if len(lines) > 10:
                        print(f"  ... 还有 {len(lines) - 10} 个配置项")
                else:
                    print("⚠️ .env文件为空")
                    
        except Exception as e:
            print(f"❌ 读取.env文件失败: {e}")
    else:
        print("⚠️ 未找到.env文件，将使用默认配置")


def main():
    """主函数"""
    print("🔧 豆瓣MCP配置测试工具")
    
    # 检查.env文件
    check_env_file()
    
    # 显示当前配置
    print_current_config()
    
    # 询问用户要运行哪些测试
    print("\n请选择要运行的测试:")
    print("1. 基础配置测试")
    print("2. 配置场景测试") 
    print("3. 配置验证测试")
    print("4. 集成测试")
    print("5. 运行所有测试")
    print("0. 退出")
    
    choice = input("\n请输入选择 (0-5): ").strip()
    
    success = False
    
    if choice == "1":
        success = run_basic_tests()
    elif choice == "2":
        success = run_scenario_tests()
    elif choice == "3":
        success = run_validation_tests()
    elif choice == "4":
        success = run_integration_tests()
    elif choice == "5":
        success = run_all_config_tests()
    elif choice == "0":
        print("👋 退出")
        return 0
    else:
        print("❌ 无效选择")
        return 1
    
    # 显示结果
    if success:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print("\n❌ 测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    exit(main()) 
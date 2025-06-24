"""SQLite缓存系统测试"""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest
from src.cache import CacheManager, SQLiteClient
from src.config import Config


class TestConfig(Config):
    """测试用配置"""
    cache_db_path: str = ":memory:"  # 使用内存数据库进行测试


@pytest.fixture
async def cache_manager():
    """缓存管理器夹具"""
    config = TestConfig()
    manager = CacheManager(config)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_cache_set_and_get(cache_manager):
    """测试缓存设置和获取"""
    # 测试数据
    key = "test_book_123"
    content_type = "book"
    data = {
        "id": "123",
        "title": "测试图书",
        "author": "测试作者"
    }
    metadata = {"source": "test"}
    
    # 设置缓存
    success = await cache_manager.set_cache(
        key=key,
        content_type=content_type, 
        data=data,
        metadata=metadata
    )
    assert success is True
    
    # 获取缓存
    result = await cache_manager.get_cache(key, content_type)
    assert result is not None
    assert result["data"] == data
    assert result["metadata"] == metadata
    assert result["hit_count"] == 1


@pytest.mark.asyncio 
async def test_cache_miss(cache_manager):
    """测试缓存未命中"""
    result = await cache_manager.get_cache("nonexistent", "book")
    assert result is None


@pytest.mark.asyncio
async def test_click_script_management(cache_manager):
    """测试点击脚本管理"""
    content_type = "book"
    selector_version = "v1.0"
    script_data = {
        "selectors": [".title", ".author"],
        "actions": ["click", "extract"]
    }
    
    # 更新点击脚本
    success = await cache_manager.update_click_script(
        content_type=content_type,
        script_data=script_data,
        selector_version=selector_version,
        success=True
    )
    assert success is True
    
    # 获取点击脚本
    result = await cache_manager.get_click_script(content_type)
    assert result is not None
    assert result["script_data"] == script_data
    assert result["success_rate"] == 1.0
    assert result["selector_version"] == selector_version


@pytest.mark.asyncio
async def test_cache_stats(cache_manager):
    """测试缓存统计"""
    # 添加一些测试数据
    await cache_manager.set_cache("test1", "book", {"title": "Book 1"})
    await cache_manager.set_cache("test2", "movie", {"title": "Movie 1"})
    
    # 命中一次缓存
    await cache_manager.get_cache("test1", "book")
    
    # 获取统计信息
    stats = await cache_manager.get_stats()
    assert stats.total_entries >= 2
    assert stats.total_hits >= 1
    assert stats.hit_rate >= 0.0


@pytest.mark.asyncio
async def test_sqlite_client_direct():
    """直接测试SQLite客户端"""
    config = TestConfig()
    client = SQLiteClient(config)
    
    try:
        await client.connect()
        await client.init_tables()
        
        # 测试插入数据
        await client.execute(
            "INSERT INTO cache_entries (key, content_type, data) VALUES (?, ?, ?)",
            ("test_key", "test_type", '{"test": "data"}')
        )
        
        # 测试查询数据
        row = await client.fetchone(
            "SELECT * FROM cache_entries WHERE key = ?",
            ("test_key",)
        )
        assert row is not None
        assert row[1] == "test_key"  # key字段
        assert row[2] == "test_type"  # content_type字段
        
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # 运行简单测试
    async def run_basic_test():
        config = TestConfig()
        manager = CacheManager(config)
        
        try:
            await manager.initialize()
            print("✅ 缓存管理器初始化成功")
            
            # 测试缓存操作
            success = await manager.set_cache(
                "test_123", "book", {"title": "测试图书"}
            )
            print(f"✅ 缓存设置: {success}")
            
            result = await manager.get_cache("test_123", "book")
            print(f"✅ 缓存获取: {result is not None}")
            
            stats = await manager.get_stats()
            print(f"✅ 缓存统计: {stats}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        finally:
            await manager.close()
            print("✅ 缓存管理器关闭")
    
    asyncio.run(run_basic_test()) 
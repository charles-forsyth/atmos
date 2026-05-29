import os
from atmos.cache import CacheManager


def test_cache_initialization_testing():
    """Verify that CacheManager initializes in a testing directory when testing."""
    manager = CacheManager()
    assert "atmos_testing_cache_" in manager.config_dir.name
    assert manager.cache_file.name == "cache.json"
    assert manager.cache_file.exists()


def test_cache_set_and_get():
    """Test set and get operations."""
    manager = CacheManager()
    manager.clear()

    manager.set("test_key", {"foo": "bar"}, expires_sec=60)

    res = manager.get("test_key")
    assert res is not None
    val, is_expired, age_sec = res
    assert val == {"foo": "bar"}
    assert not is_expired
    assert age_sec >= 0


def test_cache_expiration(mocker):
    """Test expiration logic by mocking time.time."""
    manager = CacheManager()
    manager.clear()

    # Mock time.time() starting at 1000.0
    time_mock = mocker.patch("time.time", return_value=1000.0)
    manager.set("expire_key", "value", expires_sec=10)

    # Check immediate hit (age 0)
    res = manager.get("expire_key")
    assert res is not None
    val, is_expired, age_sec = res
    assert val == "value"
    assert not is_expired

    # Move time forward by 5 seconds (not expired)
    time_mock.return_value = 1005.0
    res = manager.get("expire_key")
    assert res is not None
    val, is_expired, age_sec = res
    assert val == "value"
    assert not is_expired
    assert age_sec == 5

    # Move time forward by 11 seconds (expired)
    time_mock.return_value = 1011.0
    res = manager.get("expire_key")
    assert res is not None
    val, is_expired, age_sec = res
    assert val == "value"
    assert is_expired
    assert age_sec == 11


def test_cache_remove_and_clear():
    """Test entry removal and cache clearing."""
    manager = CacheManager()
    manager.clear()

    manager.set("k1", "v1", 100)
    manager.set("k2", "v2", 100)

    assert manager.get("k1") is not None
    assert manager.get("k2") is not None

    # Remove single key
    removed = manager.remove("k1")
    assert removed is True
    assert manager.get("k1") is None
    assert manager.get("k2") is not None

    # Remove non-existent key
    assert manager.remove("nonexistent") is False

    # Clear all
    manager.clear()
    assert manager.get("k2") is None


def test_cache_corruption_recovery(tmp_path):
    """Test that corrupted cache files are safely backed up and reset."""
    manager = CacheManager(config_dir=tmp_path)

    # Write invalid JSON manually
    with open(manager.cache_file, "w") as f:
        f.write("{invalid_json: true")

    # Accessing should trigger recovery
    data = manager._load_cache()
    assert data == {}

    # Verify backup exists
    corrupted_backup = manager.cache_file.with_suffix(".json.corrupted")
    assert corrupted_backup.exists()
    with open(corrupted_backup, "r") as f:
        assert f.read() == "{invalid_json: true"


def test_cache_bypass_via_env():
    """Test that the ATMOS_NO_CACHE environment variable completely bypasses the cache."""
    manager = CacheManager()
    manager.clear()

    manager.set("bypass_key", "value", 100)
    assert manager.get("bypass_key") is not None

    os.environ["ATMOS_NO_CACHE"] = "1"
    try:
        assert manager.get("bypass_key") is None
    finally:
        del os.environ["ATMOS_NO_CACHE"]

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class CacheManager:
    """Manages the ~/.config/atmos/cache.json cache storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is not None:
            self.config_dir = config_dir
        elif "pytest" in sys.modules or os.environ.get("ATMOS_TESTING") == "1":
            self.config_dir = (
                Path(tempfile.gettempdir()) / f"atmos_testing_cache_{os.getpid()}"
            )
        else:
            self.config_dir = Path.home() / ".config/atmos"
        self.cache_file = self.config_dir / "cache.json"
        self._ensure_file()

    def _ensure_file(self):
        """Ensures the cache directory and cache file exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.cache_file.exists():
            self._save_cache({})

    def _load_cache(self) -> Dict[str, Any]:
        """Loads cache from the JSON file with corruption recovery."""
        try:
            if not self.cache_file.exists():
                return {}
            with open(self.cache_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            corrupted_backup = self.cache_file.with_suffix(".json.corrupted")
            try:
                shutil.copy(self.cache_file, corrupted_backup)
                print(
                    f"Warning: Cache storage at {self.cache_file} was corrupted and has been reset. "
                    f"A backup of the corrupted file was saved to {corrupted_backup}",
                    file=sys.stderr,
                )
            except Exception as backup_err:
                print(
                    f"Warning: Cache storage at {self.cache_file} was corrupted and reset. "
                    f"Failed to create backup: {backup_err}",
                    file=sys.stderr,
                )
            # Reset to empty config
            self._save_cache({})
            return {}
        except FileNotFoundError:
            return {}

    def _save_cache(self, cache_data: Dict[str, Any]):
        """Saves cache to the JSON file atomically."""
        tmp_file = self.cache_file.with_suffix(".json.tmp")
        try:
            with open(tmp_file, "w") as f:
                json.dump(cache_data, f, indent=4)
            tmp_file.replace(self.cache_file)
        except Exception as e:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass
            raise e

    def set(self, key: str, value: Any, expires_sec: int):
        """Sets a cache entry with an expiration time in seconds."""
        cache_data = self._load_cache()
        cache_data[key] = {
            "value": value,
            "created_at": time.time(),
            "expires_sec": expires_sec,
        }
        self._save_cache(cache_data)

    def get(self, key: str) -> Optional[Tuple[Any, bool, int]]:
        """
        Gets a cache entry by key.
        Returns: Tuple[value, is_expired, age_sec] or None if key not found.
        """
        if os.environ.get("ATMOS_NO_CACHE") == "1":
            return None

        cache_data = self._load_cache()
        entry = cache_data.get(key)
        if not entry:
            return None

        val = entry.get("value")
        created_at = entry.get("created_at", 0.0)
        expires_sec = entry.get("expires_sec", 0)

        now = time.time()
        age_sec = int(now - created_at)
        is_expired = age_sec > expires_sec

        return val, is_expired, age_sec

    def remove(self, key: str) -> bool:
        """Removes a cache entry. Returns True if removed, False otherwise."""
        cache_data = self._load_cache()
        if key in cache_data:
            del cache_data[key]
            self._save_cache(cache_data)
            return True
        return False

    def clear(self):
        """Clears all cache entries."""
        self._save_cache({})


# Global cache manager instance
cache_manager = CacheManager()

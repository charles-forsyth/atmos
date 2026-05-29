import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional


class PlacesManager:
    """Manages the ~/.config/atmos/places.json registry."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is not None:
            self.config_dir = config_dir
        elif "pytest" in sys.modules or os.environ.get("ATMOS_TESTING") == "1":
            self.config_dir = (
                Path(tempfile.gettempdir()) / f"atmos_testing_{os.getpid()}"
            )
        else:
            self.config_dir = Path.home() / ".config/atmos"
        self.places_file = self.config_dir / "places.json"
        self._ensure_file()

    def _ensure_file(self):
        """Ensures the config directory and places file exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.places_file.exists():
            self._save_places({})

    def _load_places(self) -> Dict[str, str]:
        """Loads places from the JSON file with corruption recovery."""
        try:
            if not self.places_file.exists():
                return {}
            with open(self.places_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            corrupted_backup = self.places_file.with_suffix(".json.corrupted")
            try:
                shutil.copy(self.places_file, corrupted_backup)
                print(
                    f"Warning: Saved places registry at {self.places_file} was corrupted and has been reset. "
                    f"A backup of the corrupted file was saved to {corrupted_backup}",
                    file=sys.stderr,
                )
            except Exception as backup_err:
                print(
                    f"Warning: Saved places registry at {self.places_file} was corrupted and reset. "
                    f"Failed to create backup: {backup_err}",
                    file=sys.stderr,
                )
            # Reset to empty config
            self._save_places({})
            return {}
        except FileNotFoundError:
            return {}

    def _save_places(self, places: Dict[str, str]):
        """Saves places to the JSON file atomically."""
        tmp_file = self.places_file.with_suffix(".json.tmp")
        try:
            with open(tmp_file, "w") as f:
                json.dump(places, f, indent=4)
            tmp_file.replace(self.places_file)
        except Exception as e:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass
            raise e

    def add(self, name: str, address: str):
        """Adds or updates a place (case-insensitive key match)."""
        places = self._load_places()
        target_key = name
        for key in list(places.keys()):
            if key.lower() == name.lower():
                target_key = key
                break
        places[target_key] = address
        self._save_places(places)

    def remove(self, name: str) -> bool:
        """Removes a place (case-insensitive). Returns True if removed, False if not found."""
        places = self._load_places()
        target_key = None
        for key in places:
            if key.lower() == name.lower():
                target_key = key
                break
        if target_key is not None:
            del places[target_key]
            self._save_places(places)
            return True
        return False

    def list(self) -> Dict[str, str]:
        """Returns all saved places."""
        return self._load_places()

    def get(self, name: str) -> Optional[str]:
        """Gets an address by name (case-insensitive key search)."""
        places = self._load_places()
        for key, val in places.items():
            if key.lower() == name.lower():
                return val
        return None


# Global instance
places_manager = PlacesManager()

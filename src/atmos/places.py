import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class PlacesManager:
    """Manages the ~/.config/atmos/places.json registry with rich metadata and default settings."""

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
            self._save_places_raw({"places": {}, "default_place": "Home"})
        else:
            # Load and force migration if old schema
            self._load_places_raw()

    def _load_places_raw(self) -> Dict[str, Any]:
        """Loads and migrates the registry from JSON."""
        try:
            if not self.places_file.exists():
                return {"places": {}, "default_place": "Home"}
            with open(self.places_file, "r") as f:
                data = json.load(f)
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
            # Reset
            data = {"places": {}, "default_place": "Home"}
            self._save_places_raw(data)
            return data
        except FileNotFoundError:
            return {"places": {}, "default_place": "Home"}

        # Perform migration if it's in the old flat dict format
        if "places" not in data:
            new_data: Dict[str, Any] = {"places": {}, "default_place": "Home"}
            # Check if there was any data inside the flat dict
            for k, v in data.items():
                if k == "default_place":
                    new_data["default_place"] = str(v)
                elif isinstance(v, str):
                    new_data["places"][k] = {
                        "address": v,
                        "lat": None,
                        "lng": None,
                        "formatted": None,
                    }
                elif isinstance(v, dict):
                    new_data["places"][k] = v
            self._save_places_raw(new_data)
            data = new_data

        return data

    def _save_places_raw(self, data: Dict[str, Any]):
        """Saves registry raw dictionary atomically."""
        tmp_file = self.places_file.with_suffix(".json.tmp")
        try:
            with open(tmp_file, "w") as f:
                json.dump(data, f, indent=4)
            tmp_file.replace(self.places_file)
        except Exception as e:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass
            raise e

    def add(self, name: str, address: str):
        """Standard add method to preserve backward compatibility."""
        self.add_rich(name, address)

    def add_rich(
        self,
        name: str,
        address: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        formatted: Optional[str] = None,
    ):
        """Adds or updates a place with rich coordinates and formatted fields."""
        data = self._load_places_raw()
        places = data["places"]

        # Case-insensitive key matching to preserve existing keys
        target_key = name
        for key in list(places.keys()):
            if key.lower() == name.lower():
                target_key = key
                break

        places[target_key] = {
            "address": address,
            "lat": lat,
            "lng": lng,
            "formatted": formatted,
        }
        self._save_places_raw(data)

    def remove(self, name: str) -> bool:
        """Removes a place case-insensitively."""
        data = self._load_places_raw()
        places = data["places"]
        target_key = None
        for key in places:
            if key.lower() == name.lower():
                target_key = key
                break
        if target_key is not None:
            del places[target_key]
            # If the default place was removed, reset it to Home or the first available place
            if data.get("default_place") == target_key:
                data["default_place"] = "Home"
            self._save_places_raw(data)
            return True
        return False

    def list(self) -> Dict[str, str]:
        """Returns a flat dict of {name: address} for backwards compatibility."""
        data = self._load_places_raw()
        places = data.get("places", {})
        flat_places = {}
        for k, v in places.items():
            if isinstance(v, dict):
                flat_places[k] = v.get("address", "")
            else:
                flat_places[k] = str(v)
        return flat_places

    def list_rich(self) -> Dict[str, Dict[str, Any]]:
        """Returns the raw dictionary of rich places."""
        data = self._load_places_raw()
        return data.get("places", {})

    def get(self, name: str) -> Optional[str]:
        """Gets the flat address string by name."""
        data = self._load_places_raw()
        places = data.get("places", {})
        for key, entry in places.items():
            if key.lower() == name.lower():
                if isinstance(entry, dict):
                    return entry.get("address")
                return str(entry)
        return None

    def get_coords(self, name: str) -> Optional[Tuple[float, float]]:
        """Retrieves pre-cached coordinates for a saved place name."""
        data = self._load_places_raw()
        places = data.get("places", {})
        for key, entry in places.items():
            if key.lower() == name.lower():
                if isinstance(entry, dict):
                    lat = entry.get("lat")
                    lng = entry.get("lng")
                    if lat is not None and lng is not None:
                        return float(lat), float(lng)
        return None

    def get_default(self) -> Optional[str]:
        """Gets the configured default place name."""
        data = self._load_places_raw()
        return data.get("default_place")

    def set_default(self, name: str) -> bool:
        """Sets the configured default place. Returns True if name exists, False otherwise."""
        data = self._load_places_raw()
        places = data.get("places", {})
        exists = False
        target_key = name
        for key in places:
            if key.lower() == name.lower():
                target_key = key
                exists = True
                break
        if exists or name == "Home":
            data["default_place"] = target_key
            self._save_places_raw(data)
            return True
        return False

    def export_places(self, filepath: Path) -> int:
        """Exports saved places registry to an external JSON file. Returns count of exported places."""
        data = self._load_places_raw()
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        return len(data.get("places", {}))

    def import_places(self, filepath: Path) -> int:
        """Imports saved places from an external JSON file. Returns count of imported/merged places."""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        with open(filepath, "r") as f:
            import_data = json.load(f)

        # Basic validation of structure
        imported_places = {}
        if "places" in import_data:
            imported_places = import_data["places"]
        else:
            # Try to read as flat structure
            for k, v in import_data.items():
                if k != "default_place":
                    if isinstance(v, str):
                        imported_places[k] = {
                            "address": v,
                            "lat": None,
                            "lng": None,
                            "formatted": None,
                        }
                    elif isinstance(v, dict):
                        imported_places[k] = v

        data = self._load_places_raw()
        places = data["places"]

        merged_count = 0
        for name, entry in imported_places.items():
            if isinstance(entry, dict):
                address = entry.get("address", "")
                lat = entry.get("lat")
                lng = entry.get("lng")
                formatted = entry.get("formatted")
            else:
                address = str(entry)
                lat, lng, formatted = None, None, None

            # Case-insensitive merge check
            target_key = name
            for key in list(places.keys()):
                if key.lower() == name.lower():
                    target_key = key
                    break

            places[target_key] = {
                "address": address,
                "lat": lat,
                "lng": lng,
                "formatted": formatted,
            }
            merged_count += 1

        # Also merge default place if specified
        if "default_place" in import_data:
            data["default_place"] = import_data["default_place"]

        self._save_places_raw(data)
        return merged_count


# Global instance
places_manager = PlacesManager()

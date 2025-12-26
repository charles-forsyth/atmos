import json
from pathlib import Path
from typing import Dict, Optional

class PlacesManager:
    """Manages the ~/.config/atmos/places.json registry."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config/atmos"
        self.places_file = self.config_dir / "places.json"
        self._ensure_file()

    def _ensure_file(self):
        """Ensures the config directory and places file exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.places_file.exists():
            self._save_places({})

    def _load_places(self) -> Dict[str, str]:
        """Loads places from the JSON file."""
        try:
            with open(self.places_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_places(self, places: Dict[str, str]):
        """Saves places to the JSON file."""
        with open(self.places_file, "w") as f:
            json.dump(places, f, indent=4)

    def add(self, name: str, address: str):
        """Adds or updates a place."""
        places = self._load_places()
        places[name] = address
        self._save_places(places)

    def remove(self, name: str) -> bool:
        """Removes a place. Returns True if removed, False if not found."""
        places = self._load_places()
        if name in places:
            del places[name]
            self._save_places(places)
            return True
        return False

    def list(self) -> Dict[str, str]:
        """Returns all saved places."""
        return self._load_places()

    def get(self, name: str) -> Optional[str]:
        """Gets an address by name (case-insensitive key search could be added)."""
        places = self._load_places()
        return places.get(name)

# Global instance
places_manager = PlacesManager()

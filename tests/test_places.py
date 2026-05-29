import json
import pytest
from atmos.places import PlacesManager


def test_places_manager(tmp_path, mocker):
    # Patch the config directory to use a temp path
    mocker.patch.object(PlacesManager, "__init__", return_value=None)

    manager = PlacesManager()
    manager.config_dir = tmp_path
    manager.places_file = tmp_path / "places.json"
    manager._ensure_file()

    # Test Add
    manager.add("Home", "123 Main St")
    assert manager.get("Home") == "123 Main St"

    # Test List
    places = manager.list()
    assert "Home" in places
    assert places["Home"] == "123 Main St"

    # Test Remove
    assert manager.remove("Home") is True
    assert manager.get("Home") is None
    assert manager.remove("Ghost") is False


def test_places_manager_case_insensitivity(tmp_path, mocker):
    mocker.patch.object(PlacesManager, "__init__", return_value=None)

    manager = PlacesManager()
    manager.config_dir = tmp_path
    manager.places_file = tmp_path / "places.json"
    manager._ensure_file()

    # Add Home (mixed case)
    manager.add("Home", "123 Main St")

    # Get should be case-insensitive
    assert manager.get("home") == "123 Main St"
    assert manager.get("HOME") == "123 Main St"
    assert manager.get("Home") == "123 Main St"

    # Adding 'HOME' should update the existing 'Home' key case-insensitively, keeping/updating correctly
    manager.add("HOME", "456 Oak Ave")
    assert manager.get("home") == "456 Oak Ave"
    assert len(manager.list()) == 1  # No duplicate keys

    # Remove should be case-insensitive
    assert manager.remove("home") is True
    assert manager.get("Home") is None
    assert len(manager.list()) == 0


def test_places_manager_corruption_recovery(tmp_path, mocker, capsys):
    mocker.patch.object(PlacesManager, "__init__", return_value=None)

    manager = PlacesManager()
    manager.config_dir = tmp_path
    manager.places_file = tmp_path / "places.json"
    manager._ensure_file()

    # Write malformed/corrupted json
    with open(manager.places_file, "w") as f:
        f.write("{invalid_json: true")

    # Loading should recover, copy backup to corrupted file, reset configuration, and print warning to stderr
    places = manager.list()
    assert places == {}

    # Verify backup exists and contains the corrupted data
    corrupted_file = tmp_path / "places.json.corrupted"
    assert corrupted_file.exists()
    with open(corrupted_file, "r") as f:
        assert f.read() == "{invalid_json: true"

    # Verify warning on stderr
    captured = capsys.readouterr()
    assert "Warning: Saved places registry at" in captured.err
    assert "corrupted and has been reset" in captured.err


def test_places_manager_atomic_save(tmp_path, mocker):
    mocker.patch.object(PlacesManager, "__init__", return_value=None)

    manager = PlacesManager()
    manager.config_dir = tmp_path
    manager.places_file = tmp_path / "places.json"
    manager._ensure_file()

    # Initial data
    manager.add("Work", "789 Pine Rd")

    # Mock open inside _save_places to fail during dump
    original_dump = json.dump

    def mock_dump(*args, **kwargs):
        raise IOError("Disk full or write error")

    mocker.patch("json.dump", side_effect=mock_dump)

    # Adding should raise error, but the original places.json must remain completely intact
    with pytest.raises(IOError):
        manager.add("Cabin", "555 Lake Dr")

    # Restore json.dump and check that the old data is untouched and no tmp files leak
    mocker.patch("json.dump", side_effect=original_dump)
    assert manager.get("Work") == "789 Pine Rd"
    assert manager.get("Cabin") is None

    # Tmp file shouldn't be left behind
    tmp_file = manager.places_file.with_suffix(".json.tmp")
    assert not tmp_file.exists()

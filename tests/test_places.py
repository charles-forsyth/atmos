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


def test_places_manager_rich_and_defaults(tmp_path, mocker):
    mocker.patch.object(PlacesManager, "__init__", return_value=None)

    manager = PlacesManager()
    manager.config_dir = tmp_path
    manager.places_file = tmp_path / "places.json"
    manager._ensure_file()

    # Test rich add
    manager.add_rich(
        "Office",
        "456 Corporate Blvd",
        lat=34.0522,
        lng=-118.2437,
        formatted="Office, Los Angeles, CA",
    )

    assert manager.get("Office") == "456 Corporate Blvd"
    assert manager.get_coords("Office") == (34.0522, -118.2437)

    rich_list = manager.list_rich()
    assert "Office" in rich_list
    assert rich_list["Office"]["lat"] == 34.0522
    assert rich_list["Office"]["formatted"] == "Office, Los Angeles, CA"

    # Test default place settings
    assert manager.get_default() == "Home"
    assert manager.set_default("Office") is True
    assert manager.get_default() == "Office"

    # Try setting invalid place as default (should fail)
    assert manager.set_default("InvalidPlace") is False
    assert manager.get_default() == "Office"


def test_places_manager_export_import(tmp_path, mocker):
    mocker.patch.object(PlacesManager, "__init__", return_value=None)

    # Setup source manager
    src_manager = PlacesManager()
    src_manager.config_dir = tmp_path / "src"
    src_manager.places_file = src_manager.config_dir / "places.json"
    src_manager._ensure_file()

    src_manager.add_rich("Home", "123 Main St", lat=40.7128, lng=-74.0060)
    src_manager.add_rich("Work", "789 Pine Rd", lat=37.7749, lng=-122.4194)
    src_manager.set_default("Work")

    export_path = tmp_path / "exported_places.json"
    exported_count = src_manager.export_places(export_path)
    assert exported_count == 2
    assert export_path.exists()

    # Setup destination manager
    dest_manager = PlacesManager()
    dest_manager.config_dir = tmp_path / "dest"
    dest_manager.places_file = dest_manager.config_dir / "places.json"
    dest_manager._ensure_file()

    # Verify dest starts empty/default
    assert dest_manager.get_default() == "Home"
    assert len(dest_manager.list()) == 0

    # Import
    imported_count = dest_manager.import_places(export_path)
    assert imported_count == 2

    # Verify dest contents
    assert dest_manager.get_default() == "Work"
    assert dest_manager.get("Home") == "123 Main St"
    assert dest_manager.get_coords("Home") == (40.7128, -74.0060)
    assert dest_manager.get("Work") == "789 Pine Rd"
    assert dest_manager.get_coords("Work") == (37.7749, -122.4194)


def test_places_manager_old_schema_migration(tmp_path, mocker):
    mocker.patch.object(PlacesManager, "__init__", return_value=None)

    manager = PlacesManager()
    manager.config_dir = tmp_path
    manager.places_file = tmp_path / "places.json"

    # Write old flat format dict manually
    old_data = {
        "Home": "123 Old Flat St",
        "Cabin": "555 Mountain View Dr",
        "default_place": "Cabin",
    }
    tmp_path.mkdir(parents=True, exist_ok=True)
    with open(manager.places_file, "w") as f:
        json.dump(old_data, f)

    # Initialize / Load should automatically trigger migration
    manager._ensure_file()

    # Check migrated contents
    assert manager.get_default() == "Cabin"
    assert manager.get("Home") == "123 Old Flat St"
    assert manager.get("Cabin") == "555 Mountain View Dr"

    # Ensure coordinates fields exist as None after migration
    rich_list = manager.list_rich()
    assert rich_list["Home"]["lat"] is None
    assert rich_list["Cabin"]["lng"] is None

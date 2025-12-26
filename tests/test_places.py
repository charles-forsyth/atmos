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

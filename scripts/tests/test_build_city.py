import sys, os, json, tempfile
sys.path.insert(0, 'scripts')

# Patch OUTPUT_DIR before importing build_data
import config as _cfg
_orig_output_dir = _cfg.OUTPUT_DIR

def test_build_for_city_outputs_correct_filenames(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, 'OUTPUT_DIR', str(tmp_path))
    # Re-import build_data so it picks up patched OUTPUT_DIR
    import importlib, build_data
    importlib.reload(build_data)

    fake_animals = [
        {
            "id": "GOV-1", "source": "gov_shelter", "kind": "dog", "name": "",
            "sex": "M", "age": "adult", "bodytype": "medium", "colour": "黑色",
            "sterilized": None, "vaccinated": None, "photo_url": "", "remark": "",
            "open_date": "2026-01-01", "update_date": "2026-01-01", "city": "臺北市",
            "_shelter_name": "臺北市動物之家", "_shelter_address": "臺北市中山區",
            "_shelter_phone": "", "_geo_address": "臺北市動物之家", "_location_type": "shelter",
            "source_url": "",
        }
    ]

    # Should produce animals_臺北市.json and locations_臺北市.json
    build_data.build_for_city("臺北市", fake_animals, "2026-01-01T00:00:00+08:00")

    assert (tmp_path / "animals_臺北市.json").exists(), "animals_臺北市.json not created"
    assert (tmp_path / "locations_臺北市.json").exists(), "locations_臺北市.json not created"

def test_build_for_city_taiwan_uses_全台_suffix(tmp_path, monkeypatch):
    """Verify ALL_TAIWAN uses '全台' filename suffix, not '全台灣'."""
    import config
    monkeypatch.setattr(config, 'OUTPUT_DIR', str(tmp_path))
    import importlib, build_data
    importlib.reload(build_data)

    fake_animals = [
        {
            "id": "GOV-2", "source": "gov_shelter", "kind": "cat", "name": "",
            "sex": "F", "age": "adult", "bodytype": "small", "colour": "白色",
            "sterilized": None, "vaccinated": None, "photo_url": "", "remark": "",
            "open_date": "2026-01-01", "update_date": "2026-01-01", "city": "臺北市",
            "_shelter_name": "臺北市動物之家", "_shelter_address": "臺北市中山區",
            "_shelter_phone": "", "_geo_address": "臺北市動物之家", "_location_type": "shelter",
            "source_url": "",
        }
    ]

    build_data.build_for_city("全台灣", fake_animals, "2026-01-01T00:00:00+08:00")
    # Must use '全台' suffix, not '全台灣'
    assert (tmp_path / "animals_全台.json").exists(), "Should create animals_全台.json"
    assert not (tmp_path / "animals_全台灣.json").exists(), "Should NOT create animals_全台灣.json"

import sys, os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import geocode


def test_override_takes_priority_over_nominatim(monkeypatch, tmp_path):
    """override JSON 中的地址應直接回傳指定座標，不呼叫 Nominatim。"""
    override_data = {
        "南屯區 信揚動物醫院": {"lat": 24.1372, "lng": 120.6468, "note": "test"}
    }
    override_file = tmp_path / "overrides.json"
    override_file.write_text(json.dumps(override_data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr('geocode.GEOCODE_OVERRIDES_FILE', str(override_file))
    monkeypatch.setattr('geocode.GEOCODE_CACHE_FILE', str(tmp_path / "cache.json"))

    # 確保 Nominatim 不被呼叫
    called = []
    monkeypatch.setattr('geocode._query_nominatim', lambda addr: called.append(addr) or None)

    result = geocode.geocode_addresses(["南屯區 信揚動物醫院"])

    assert "南屯區 信揚動物醫院" in result
    assert result["南屯區 信揚動物醫院"]["lat"] == 24.1372
    assert result["南屯區 信揚動物醫院"]["lng"] == 120.6468
    assert called == [], "Nominatim 不應被呼叫"


def test_override_takes_priority_over_stale_cache(monkeypatch, tmp_path):
    """override 應優先於舊快取，確保手動修正能覆蓋錯誤的快取座標。"""
    override_data = {
        "南屯區 信揚動物醫院": {"lat": 24.1372, "lng": 120.6468, "note": "test"}
    }
    # 舊快取存有錯誤座標（桃園的經緯度）
    stale_cache = {
        "南屯區 信揚動物醫院": {"lat": 25.0, "lng": 121.3}
    }
    override_file = tmp_path / "overrides.json"
    cache_file = tmp_path / "cache.json"
    override_file.write_text(json.dumps(override_data, ensure_ascii=False), encoding="utf-8")
    cache_file.write_text(json.dumps(stale_cache, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr('geocode.GEOCODE_OVERRIDES_FILE', str(override_file))
    monkeypatch.setattr('geocode.GEOCODE_CACHE_FILE', str(cache_file))

    result = geocode.geocode_addresses(["南屯區 信揚動物醫院"])

    # 應使用 override 座標，不是快取的錯誤座標
    assert result["南屯區 信揚動物醫院"]["lat"] == 24.1372
    assert result["南屯區 信揚動物醫院"]["lng"] == 120.6468


def test_non_override_address_falls_through_to_nominatim(monkeypatch, tmp_path):
    """不在 override 中的地址應繼續走 Nominatim 流程，並回傳正確座標。"""
    override_file = tmp_path / "overrides.json"
    override_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr('geocode.GEOCODE_OVERRIDES_FILE', str(override_file))
    monkeypatch.setattr('geocode.GEOCODE_CACHE_FILE', str(tmp_path / "cache.json"))

    called = []
    def mock_nominatim(addr):
        called.append(addr)
        return (24.0, 120.5)

    monkeypatch.setattr('geocode._query_nominatim', mock_nominatim)

    result = geocode.geocode_addresses(["台中市某個地址"])

    assert called == ["台中市某個地址"], "Nominatim 應被呼叫"
    assert result["台中市某個地址"]["lat"] == 24.0
    assert result["台中市某個地址"]["lng"] == 120.5

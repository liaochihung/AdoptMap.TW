"""
整合測試：驗證從 API 資料到最終 JSON 的完整流程。
使用靜態測試資料（不呼叫真實 API）。
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fetch_animals import parse_remark_location, _map_kind, _map_sex

# 模擬三種來源的 API 原始記錄（精簡版）
MOCK_SHELTER_RECORD = {
    "animal_place": "臺中市動物之家南屯園區",
    "shelter_name": "臺中市動物之家南屯園區",
    "animal_remark": "",
}

MOCK_VET_RECORD = {
    "animal_place": "臺中市動物之家中途動物醫院",
    "shelter_name": "臺中市動物之家中途動物醫院",
    "animal_remark": '我在 " 南屯區 信揚動物醫院 " 等待愛心認養喔！聯絡電話：04-24730000',
}

MOCK_YIQI_RECORD = {
    "animal_place": "臺中市動物之家益起認養吧",
    "shelter_name": "臺中市動物之家益起認養吧",
    "animal_remark": '我在西屯區"東森寵物台中澄清店"等待愛心認養喔！聯絡電話：04-24618811 台中市西屯區西屯路三段92-1號',
}


def _extract_zone(animal_place: str) -> str:
    for zone in ("南屯園區", "后里園區", "中途動物醫院", "益起認養吧"):
        if animal_place.endswith(zone):
            return zone
    return animal_place


def test_shelter_zone_extraction():
    assert _extract_zone("臺中市動物之家南屯園區") == "南屯園區"
    assert _extract_zone("臺中市動物之家后里園區") == "后里園區"
    assert _extract_zone("臺中市動物之家中途動物醫院") == "中途動物醫院"
    assert _extract_zone("臺中市動物之家益起認養吧") == "益起認養吧"


def test_shelter_returns_none():
    zone = _extract_zone(MOCK_SHELTER_RECORD["animal_place"])
    result = parse_remark_location(MOCK_SHELTER_RECORD["animal_remark"], zone)
    assert result is None


def test_vet_parsed_correctly():
    zone = _extract_zone(MOCK_VET_RECORD["animal_place"])
    result = parse_remark_location(MOCK_VET_RECORD["animal_remark"], zone)
    assert result is not None
    assert result["type"] == "vet_transit"
    assert "信揚動物醫院" in result["name"]
    assert result["address"] == ""
    assert result["phone"] == "04-24730000"


def test_yiqi_parsed_correctly():
    zone = _extract_zone(MOCK_YIQI_RECORD["animal_place"])
    result = parse_remark_location(MOCK_YIQI_RECORD["animal_remark"], zone)
    assert result is not None
    assert result["type"] == "yiqi"
    assert "東森寵物台中澄清店" in result["name"]
    assert result["address"] == "台中市西屯區西屯路三段92-1號"
    assert result["phone"] == "04-24618811"

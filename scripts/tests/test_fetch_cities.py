import sys
sys.path.insert(0, 'scripts')
from fetch_animals import _extract_city

def test_extract_city_taichung():
    rec = {"animal_place": "臺中市動物之家南屯園區", "shelter_name": "", "shelter_address": ""}
    assert _extract_city(rec) == "臺中市"

def test_extract_city_taipei():
    rec = {"animal_place": "臺北市動物之家", "shelter_name": "", "shelter_address": "臺北市中山區"}
    assert _extract_city(rec) == "臺北市"

def test_extract_city_unknown():
    rec = {"animal_place": "", "shelter_name": "", "shelter_address": ""}
    assert _extract_city(rec) == ""

def test_extract_city_from_address():
    rec = {"animal_place": "", "shelter_name": "", "shelter_address": "高雄市某收容所路1號"}
    assert _extract_city(rec) == "高雄市"

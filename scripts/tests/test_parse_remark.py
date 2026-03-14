import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fetch_animals import parse_remark_location

# --- 中途動物醫院 ---

def test_vet_transit_basic():
    remark = '我在 " 南屯區 信揚動物醫院 " 等待愛心認養喔！歡迎打電話詢問或預約互動時間，聯絡電話：04-24730000'
    result = parse_remark_location(remark, '中途動物醫院')
    assert result['type'] == 'vet_transit'
    assert '信揚動物醫院' in result['name']
    assert result['address'] == ''
    assert result['phone'] == '04-24730000'

def test_vet_transit_no_quotes():
    remark = '我在西區 台中動物醫院 等待認養，電話：04-12345678'
    result = parse_remark_location(remark, '中途動物醫院')
    assert result['type'] == 'vet_transit'
    assert result['name'] == ''      # 無引號 → 店名未知，geocoding 會 fallback 到 shelter_name
    assert result['address'] == ''

# --- 益起認養吧 ---

def test_yiqi_with_full_address():
    remark = '我在西屯區"東森寵物台中澄清店"等待愛心認養喔！聯絡電話：04-24618811 台中市西屯區西屯路三段92-1號'
    result = parse_remark_location(remark, '益起認養吧')
    assert result['type'] == 'yiqi'
    assert '東森寵物台中澄清店' in result['name']
    assert result['address'] == '台中市西屯區西屯路三段92-1號'
    assert result['phone'] == '04-24618811'

def test_yiqi_another_store():
    remark = '我在大里區"魚中魚大里店"等待主人的愛心認養喔！聯絡電話：04-24073388 台中市大里區國光路二段505號'
    result = parse_remark_location(remark, '益起認養吧')
    assert result['type'] == 'yiqi'
    assert result['address'] == '台中市大里區國光路二段505號'

def test_yiqi_pet_park_store():
    remark = '我在大里區"寵物公園大里成功店"等待主人的愛心認養喔！聯絡電話：04-24910650 台中市大里區成功路498號'
    result = parse_remark_location(remark, '益起認養吧')
    assert result['type'] == 'yiqi'
    assert result['address'] == '台中市大里區成功路498號'

# --- 收容所（備註不觸發解析）---

def test_shelter_no_remark():
    result = parse_remark_location('', '南屯園區')
    assert result is None

def test_shelter_health_remark():
    result = parse_remark_location('左側骨盆斷跛行，目前日常行動OK，局部脫毛。', '后里園區')
    assert result is None

# --- fallback ---

def test_unknown_shelter_type_returns_none():
    result = parse_remark_location('隨意備註', '未知')
    assert result is None

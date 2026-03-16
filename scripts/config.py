# scripts/config.py

# 農業部動物認領養 Open Data API
MOA_API_URL = "https://data.moa.gov.tw/Service/OpenData/TransService.aspx"
MOA_UNIT_ID = "QcbUEzN6E6DL"
MOA_PAGE_SIZE = 1000  # 每次請求筆數

# Nominatim geocoding
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "adopt-map/1.0 (https://github.com/liaochihung/AdoptMap.TW)"
NOMINATIM_DELAY = 1.5  # 秒，遵守每秒 1 次請求的限制

# 台中市範圍 bounding box（偏好此區域的 geocoding 結果）
TAICHUNG_VIEWBOX = "120.4,24.0,121.0,24.5"

# 固定座標（收容所不需要 geocoding）
KNOWN_LOCATIONS = {
    "臺中市動物之家南屯園區": {
        "id": "loc_nantun",
        "lat": 24.1366,
        "lng": 120.6175,
        "address": "臺中市南屯區中台路601號",
        "phone": "04-23850949",
        "type": "shelter",
    },
    "臺中市動物之家后里園區": {
        "id": "loc_houli",
        "lat": 24.3049,
        "lng": 120.7106,
        "address": "臺中市后里區堤防路370號",
        "phone": "04-25588024",
        "type": "shelter",
    },
}

# 輸出路徑（相對於專案根目錄）
_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
OUTPUT_DIR = str(_ROOT / "public/data")
THUMBS_DIR = str(_ROOT / "public/data/thumbs")
THUMB_SIZE = (96, 96)
CACHE_DIR = str(_ROOT / "scripts/.cache")
GEOCODE_CACHE_FILE = str(_ROOT / "scripts/.cache/geocode_cache.json")
GEOCODE_OVERRIDES_FILE = str(_ROOT / "scripts/geocode_overrides.json")
GEOCODE_FAILURES_LOG = str(_ROOT / "scripts/.cache/geocode_failures.log")

# 來源類型常數（對應 location.type）
LOCATION_TYPES = {
    "shelter": "公立收容所",
    "vet_transit": "中途動物醫院",
    "yiqi": "益起認養吧",
}

# 支援的縣市清單（依農業部 API animal_place 欄位）
ALL_CITIES = [
    "臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣",
    "苗栗縣", "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市",
    "嘉義縣", "臺南市", "高雄市", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣",
]

# 各縣市地圖中心座標（lat, lng）與預設 zoom
CITY_CENTERS = {
    "臺北市":  {"lat": 25.0478, "lng": 121.5319, "zoom": 12},
    "新北市":  {"lat": 25.0120, "lng": 121.4653, "zoom": 11},
    "基隆市":  {"lat": 25.1283, "lng": 121.7419, "zoom": 13},
    "桃園市":  {"lat": 24.9937, "lng": 121.3009, "zoom": 11},
    "新竹市":  {"lat": 24.8138, "lng": 120.9675, "zoom": 13},
    "新竹縣":  {"lat": 24.7036, "lng": 121.1542, "zoom": 11},
    "苗栗縣":  {"lat": 24.5602, "lng": 120.8214, "zoom": 11},
    "臺中市":  {"lat": 24.1477, "lng": 120.6736, "zoom": 12},
    "彰化縣":  {"lat": 23.9921, "lng": 120.5161, "zoom": 11},
    "南投縣":  {"lat": 23.9610, "lng": 120.9718, "zoom": 11},
    "雲林縣":  {"lat": 23.7092, "lng": 120.4313, "zoom": 11},
    "嘉義市":  {"lat": 23.4801, "lng": 120.4491, "zoom": 13},
    "嘉義縣":  {"lat": 23.4518, "lng": 120.2555, "zoom": 11},
    "臺南市":  {"lat": 22.9999, "lng": 120.2270, "zoom": 11},
    "高雄市":  {"lat": 22.6273, "lng": 120.3014, "zoom": 11},
    "屏東縣":  {"lat": 22.5519, "lng": 120.5487, "zoom": 11},
    "宜蘭縣":  {"lat": 24.7021, "lng": 121.7378, "zoom": 11},
    "花蓮縣":  {"lat": 23.9871, "lng": 121.6015, "zoom": 10},
    "臺東縣":  {"lat": 22.7972, "lng": 121.0713, "zoom": 10},
    "澎湖縣":  {"lat": 23.5654, "lng": 119.5793, "zoom": 12},
    "金門縣":  {"lat": 24.4493, "lng": 118.3765, "zoom": 12},
    "連江縣":  {"lat": 26.1605, "lng": 119.9497, "zoom": 13},
    "全台灣":  {"lat": 23.9739, "lng": 120.9820, "zoom": 8},
}

# 全台灣特殊值（用於前端判斷）
ALL_TAIWAN = "全台灣"

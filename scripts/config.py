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

# 台中市關鍵字（用於過濾）
TAICHUNG_KEYWORDS = ["臺中", "台中"]

# 輸出路徑
OUTPUT_DIR = "public/data"
CACHE_DIR = "scripts/.cache"
GEOCODE_CACHE_FILE = "scripts/.cache/geocode_cache.json"
GEOCODE_FAILURES_LOG = "scripts/.cache/geocode_failures.log"

# 來源類型常數（對應 location.type）
LOCATION_TYPES = {
    "shelter": "公立收容所",
    "vet_transit": "中途動物醫院",
    "yiqi": "益起認養吧",
}

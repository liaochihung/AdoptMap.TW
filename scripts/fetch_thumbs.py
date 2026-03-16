# scripts/fetch_thumbs.py
"""
下載並壓縮動物縮圖，儲存至 public/data/thumbs/{animal_id}.webp。
每次執行會：
  1. 下載並壓縮新動物的縮圖（已存在的跳過，除非加 --rebuild）
  2. 刪除不在今日動物清單中的孤立縮圖

用法：
  python fetch_thumbs.py              # 只下載新增的
  python fetch_thumbs.py --rebuild    # 刪除所有現有縮圖後重新下載
"""

import io
import re
import threading
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import THUMBS_DIR, THUMB_SIZE

WORKERS = 6  # 並行下載數


def _safe_filename(animal_id: str) -> str:
    """將 animal_id 轉為安全的檔名（保留英數字、連字號、底線）。"""
    return re.sub(r"[^\w\-]", "_", animal_id)


def _download_one(item: dict, thumbs_dir: Path) -> tuple[bool, str]:
    """下載並儲存單一縮圖，回傳 (success, id)。"""
    try:
        resp = requests.get(item["url"], timeout=15, verify=False)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img.thumbnail(THUMB_SIZE, Image.LANCZOS)
        img.save(thumbs_dir / item["filename"], "WEBP", quality=82)
        return True, item["id"]
    except Exception as e:
        print(f"  ⚠ 縮圖下載失敗 {item['id']}: {e}")
        return False, item["id"]


def fetch_thumbs(animals: list[dict], rebuild: bool = False) -> None:
    """
    animals: 完整的動物清單（已含 id 與 photo_url）。
    rebuild: 若 True，刪除所有現有縮圖後重新下載。
    """
    thumbs_dir = Path(THUMBS_DIR)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    if rebuild:
        existing = list(thumbs_dir.glob("*.webp"))
        if existing:
            for f in existing:
                f.unlink()
            print(f"  🗑 --rebuild：已清除 {len(existing)} 個現有縮圖")

    # 建立今日有效 id → 檔名的對應
    valid_filenames: set[str] = set()
    to_download: list[dict] = []

    for animal in animals:
        if not animal.get("photo_url"):
            continue
        filename = _safe_filename(animal["id"]) + ".webp"
        valid_filenames.add(filename)
        if not (thumbs_dir / filename).exists():
            to_download.append({"id": animal["id"], "url": animal["photo_url"], "filename": filename})

    # 刪除孤立縮圖
    removed = 0
    for existing in thumbs_dir.glob("*.webp"):
        if existing.name not in valid_filenames:
            existing.unlink()
            removed += 1
    if removed:
        print(f"  🗑 已刪除 {removed} 個孤立縮圖")

    # 下載並壓縮新縮圖
    total = len(to_download)
    if total == 0:
        print("  ✅ 縮圖已是最新，無需下載")
        return

    print(f"  開始下載 {total} 張新縮圖（{WORKERS} 執行緒並行）...")
    success = 0
    failed = 0
    counter_lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(_download_one, item, thumbs_dir): item for item in to_download}
        for i, future in enumerate(as_completed(futures), 1):
            ok, _ = future.result()
            with counter_lock:
                if ok:
                    success += 1
                else:
                    failed += 1
            if i % 50 == 0 or i == total:
                print(f"  進度：{i}/{total}（成功 {success}，失敗 {failed}）")

    print(f"  ✅ 縮圖完成：成功 {success}，失敗 {failed}，共 {len(list(thumbs_dir.glob('*.webp')))} 個檔案")


if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path as _Path

    rebuild = "--rebuild" in sys.argv
    data_file = _Path(__file__).resolve().parent.parent / "public" / "data" / "animals_全台.json"
    with open(data_file, encoding="utf-8") as f:
        animals = json.load(f)["animals"]
    print(f"從 animals_全台.json 讀取 {len(animals)} 筆動物")
    fetch_thumbs(animals, rebuild=rebuild)

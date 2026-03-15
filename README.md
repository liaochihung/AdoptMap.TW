# AdoptMap.TW — 領養地圖

以地圖方式瀏覽台灣各地待領養的貓狗資訊，方便找到離你最近的毛孩。

政府的[動物認領養網站](https://www.pet.gov.tw/)在搜尋和瀏覽體驗上不太方便，這個專案將資料整合到互動式地圖上，讓查找更直覺。

## 功能

- 在地圖上顯示全台待領養動物的分佈位置
- 支援依縣市、動物種類（貓/狗）、性別、來源等條件篩選
- 點擊地點標記可瀏覽該處所有待領養動物的照片與資訊
- 提供 GPS 定位，快速找到附近的領養地點
- 響應式設計，手機與桌面皆可使用

## 資料來源

- [農業部動物認領養開放資料](https://data.moa.gov.tw/Service/OpenData/TransService.aspx?UnitId=QcbUEzN6E6DL) — 全台公立收容所待領養動物
- [台中市動物保護防疫處](https://www.animal.taichung.gov.tw/) — 民眾送養佈告欄、中途動物醫院

資料透過 GitHub Actions 每日自動更新。

## 技術

- **前端**：Vue 3 + Vite + Tailwind CSS
- **地圖**：Leaflet + MarkerCluster
- **資料處理**：Python（爬取 API / 網頁、Geocoding）
- **部署**：GitHub Pages

## 開發

```bash
# 安裝依賴
pnpm install

# 啟動開發伺服器
pnpm run dev
```

### 更新資料（本地）

```bash
cd scripts
pip install -r requirements.txt
python build_data.py
```

## 授權

程式碼採用 [MIT License](LICENSE) 授權。

資料依據[政府資料開放授權條款第 1 版](https://data.gov.tw/license)使用。

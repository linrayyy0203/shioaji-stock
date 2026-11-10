# 永豐 Shioaji 台股行情工具

用永豐金 Shioaji API 抓台股行情與歷史資料（只讀資料，不下單）。

## 內容

- `fetch_quote.py` — 抓即時報價快照
- `fetch_kbars.py` — 抓 K 線 / 歷史資料（日線、分鐘線），存成 CSV
- `common.py` — 共用的登入邏輯（會自動修正金鑰裡的同形字）

## 安裝

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 設定金鑰

把 `.env.example` 複製成 `.env`，填入永豐 API 後台拿到的金鑰：

```
API_KEY="你的APIKey"
SECRET_KEY="你的SecretKey"
```

> `.env` 不會被上傳到 GitHub（已被 .gitignore 排除）。

## 使用

即時報價：
```bash
./venv/bin/python fetch_quote.py 2330 2317 0050
```

最近 30 天日線：
```bash
./venv/bin/python fetch_kbars.py 2330
```

指定區間日線：
```bash
./venv/bin/python fetch_kbars.py 2330 2025-09-01 2025-11-10
```

分鐘線：
```bash
./venv/bin/python fetch_kbars.py 2330 2025-11-10 2025-11-10 --min
```

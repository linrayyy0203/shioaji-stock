# 台股行情工具

抓台股即時報價與日線歷史（只讀資料，不下單）。

資料來源：**證交所（上市）／櫃買中心（上櫃）公開 API**，不需要任何金鑰，在雲端和自己電腦上都能跑。

## 內容

- `fetch_quote.py` — 抓即時報價快照（上市、上櫃、ETF 都支援）
- `fetch_kbars.py` — 抓日線歷史，存成 CSV
- `twse.py` — 共用的證交所／櫃買抓取邏輯
- `common.py` — （選用）永豐 Shioaji 登入邏輯，給想在本機抓即時 tick／分鐘線的進階用途

## 安裝

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 使用

即時報價（約 5 秒延遲；非盤中回傳最後收盤快照）：
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

## 關於永豐 Shioaji（選用）

這個工具預設用證交所公開 API，所以**不需要金鑰**。

如果你想要「真正即時」的報價或「分鐘線」，那需要永豐 Shioaji API，但它用的傳輸協定無法在雲端環境運作，**只能在你自己的電腦上跑**：

1. 把 `.env.example` 複製成 `.env`，填入永豐後台的 `API_KEY` / `SECRET_KEY`
2. `.env` 已被 `.gitignore` 排除，不會上傳
3. 以 `common.py` 的 `login()` 搭配 Shioaji 自行取用

> 永豐公開 API 文件：https://sinotrade.github.io/

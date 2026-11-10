"""
抓台股即時報價的小程式（只抓行情，不下單）。
用法：把同資料夾的 .env 填好 API_KEY / SECRET_KEY，然後執行這支程式。
可以在後面加股票代號，例如：python fetch_quote.py 2330 2317 0050
不加的話預設抓台積電 2330。
"""
import os
import sys


def load_env(path):
    """讀同資料夾的 .env，把 KEY=VALUE 存進環境變數。"""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    load_env(os.path.join(here, ".env"))

    api_key = os.environ.get("API_KEY", "")
    secret_key = os.environ.get("SECRET_KEY", "")

    if not api_key or not secret_key:
        print("❌ 還沒填金鑰：請打開同資料夾的 .env，把 API_KEY 和 SECRET_KEY 填進去。")
        sys.exit(1)

    import unicodedata

    def diagnose(label, s):
        bad = [(i, c) for i, c in enumerate(s) if ord(c) >= 128]
        for i, c in bad:
            name = unicodedata.name(c, "未知")
            print(f"   {label} 第 {i+1} 個字是非英數字元：U+{ord(c):04X} {name}")

    # 常見「長得像英文、其實是西里爾字母」的對照表，換回正確英文字母
    CONFUSABLES = {
        "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
        "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X", "У": "Y",
        "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y",
        "х": "x", "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d",
    }

    def fix(s):
        # 1) 換掉西里爾等同形字  2) 全形→半形相容轉換  3) 去掉剩餘非英數字元
        s = "".join(CONFUSABLES.get(ch, ch) for ch in s)
        s = unicodedata.normalize("NFKC", s)
        return "".join(ch for ch in s if ch.isalnum() and ord(ch) < 128)

    for label, raw in (("API_KEY", api_key), ("SECRET_KEY", secret_key)):
        diagnose(label, raw)
        fixed = fix(raw)
        note = "（已自動修正）" if fixed != raw.strip() else "（乾淨）"
        print(f"{label}: 原長 {len(raw)} → 修正後 {len(fixed)} {note}")
    api_key = fix(api_key)
    secret_key = fix(secret_key)
    print()

    # 要查的股票代號；沒指定就用台積電 2330
    codes = sys.argv[1:] or ["2330"]

    import shioaji as sj

    print("登入中…")
    api = sj.Shioaji()
    api.login(api_key=api_key, secret_key=secret_key)
    print("登入成功 ✅\n")

    contracts = []
    for code in codes:
        c = api.Contracts.Stocks.TSE.get(code) or api.Contracts.Stocks.OTC.get(code)
        if c is None:
            print(f"⚠️  找不到代號 {code}，略過")
        else:
            contracts.append(c)

    if not contracts:
        print("沒有可查的標的。")
        api.logout()
        return

    snapshots = api.snapshots(contracts)
    print(f"{'代號':<8}{'名稱':<10}{'成交價':>10}{'漲跌':>10}{'漲跌幅%':>10}{'成交量':>12}")
    print("-" * 62)
    for c, s in zip(contracts, snapshots):
        print(
            f"{c.code:<8}{c.name:<10}{s.close:>10.2f}{s.change_price:>10.2f}"
            f"{s.change_rate:>10.2f}{s.total_volume:>12}"
        )

    api.logout()
    print("\n完成。")


if __name__ == "__main__":
    main()

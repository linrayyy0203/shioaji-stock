"""
抓台股 K 線 / 歷史資料（只讀資料，不下單）。

用法：
  python fetch_kbars.py 2330
      → 台積電最近 30 天「日線」
  python fetch_kbars.py 2330 2025-09-01 2025-11-10
      → 指定區間的日線
  python fetch_kbars.py 2330 2025-11-07 2025-11-10 --min
      → 指定區間的「分鐘線」（區間別抓太長，分鐘資料量很大）

結果會印在畫面上，同時存成 CSV（例如 2330_day.csv）放在同資料夾。
"""
import os
import sys
from datetime import date, timedelta

import pandas as pd

from common import login, get_stock


def parse_args(argv):
    minute = "--min" in argv
    args = [a for a in argv if a != "--min"]
    if not args:
        print("請給股票代號，例如：python fetch_kbars.py 2330")
        sys.exit(1)
    code = args[0]
    today = date.today()
    start = args[1] if len(args) > 1 else str(today - timedelta(days=30))
    end = args[2] if len(args) > 2 else str(today)
    return code, start, end, minute


def main():
    code, start, end, minute = parse_args(sys.argv[1:])
    api = login()

    contract = get_stock(api, code)
    if contract is None:
        print(f"⚠️  找不到代號 {code}")
        api.logout()
        return

    print(f"抓取 {code} {contract.name}  {start} ~ {end}  "
          f"（{'分鐘線' if minute else '日線'}）…")
    kbars = api.kbars(contract, start=start, end=end)

    df = pd.DataFrame({**kbars})
    if df.empty:
        print("這個區間沒有資料（可能是假日或日期超出可查範圍）。")
        api.logout()
        return
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.set_index("ts").sort_index()

    if minute:
        out = df[["Open", "High", "Low", "Close", "Volume"]]
        kind = "min"
    else:
        # 分鐘線彙整成日線
        out = df.resample("1D").agg(
            {"Open": "first", "High": "max", "Low": "min",
             "Close": "last", "Volume": "sum"}
        ).dropna(subset=["Open"])
        kind = "day"

    out = out.round(2)
    out["Volume"] = out["Volume"].astype("int64")

    # 印出（日線全印；分鐘線太多只印頭尾）
    pd.set_option("display.max_rows", 40)
    print(f"\n共 {len(out)} 根 K 棒：\n")
    if kind == "min" and len(out) > 30:
        print(out.head(10))
        print("   …（中間省略）…")
        print(out.tail(10))
    else:
        print(out)

    here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(here, f"{code}_{kind}.csv")
    out.to_csv(csv_path, encoding="utf-8-sig")
    print(f"\n已存檔：{code}_{kind}.csv（共 {len(out)} 筆）")

    api.logout()


if __name__ == "__main__":
    main()

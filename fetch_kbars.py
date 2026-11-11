"""
抓台股日線 K 線 / 歷史資料（只讀資料，不下單）。
資料來源：證交所（上市）／櫃買中心（上櫃）公開 API，不需要金鑰。

用法：
  python fetch_kbars.py 2330
      → 台積電最近 30 天日線
  python fetch_kbars.py 2330 2025-09-01 2025-11-10
      → 指定區間的日線

結果會印在畫面上，同時存成 CSV（例如 2330_day.csv）放在同資料夾。

註：此公開來源只提供「日線」。若需要「分鐘線」，請在本機用 Shioaji
    （fetch_kbars 的舊版 / common.py）搭配永豐金鑰抓取。
"""
import os
import sys
from datetime import date, timedelta

import pandas as pd

from twse import daily


def parse_args(argv):
    if "--min" in argv:
        print("⚠️  這個公開來源只提供日線，沒有分鐘線。")
        print("   分鐘線請在本機用 Shioaji + 永豐金鑰抓取。")
        argv = [a for a in argv if a != "--min"]
    if not argv:
        print("請給股票代號，例如：python fetch_kbars.py 2330")
        sys.exit(1)
    code = argv[0]
    today = date.today()
    start = argv[1] if len(argv) > 1 else str(today - timedelta(days=30))
    end = argv[2] if len(argv) > 2 else str(today)
    return code, start, end


def main():
    code, start, end = parse_args(sys.argv[1:])

    print(f"抓取 {code}  {start} ~ {end}（日線，證交所公開行情）…")
    rows = daily(code, start, end)

    if not rows:
        print("查無資料：可能是代號錯誤、區間全是假日，或日期超出可查範圍。")
        return

    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df = df.set_index("Date").sort_index()

    pd.set_option("display.max_rows", 60)
    print(f"\n共 {len(df)} 根 K 棒：\n")
    print(df)

    here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(here, f"{code}_day.csv")
    df.to_csv(csv_path, encoding="utf-8-sig")
    print(f"\n已存檔：{code}_day.csv（共 {len(df)} 筆）")


if __name__ == "__main__":
    main()

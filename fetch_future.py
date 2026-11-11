"""
抓台股個股／ETF 期貨每日行情（只讀資料，不下單）。
資料來源：期交所（TAIFEX）公開資料，不需要金鑰。

用法：
  python fetch_future.py 0052
      → 0052（富邦科技ETF期貨）今天各到期月份的成交量
  python fetch_future.py 2330 2026-11-11
      → 指定日期

註：期交所是「收盤後」才有當日資料；盤中或假日查不到。
"""
import sys
from datetime import date

from taifex import daily


def main():
    args = sys.argv[1:]
    if not args:
        print("請給個股/ETF 代號，例如：python fetch_future.py 0052")
        sys.exit(1)
    code = args[0]
    day = args[1] if len(args) > 1 else str(date.today())

    print(f"查詢 {code} 期貨  {day}（期交所公開資料）…")
    name, rows = daily(code, day)

    if name is None:
        print(f"⚠️  找不到 {code} 的期貨商品（這個標的可能沒有上市期貨）。")
        return
    if not rows:
        print(f"{name}：{day} 查無資料（可能是假日、盤中尚未收盤，或日期超出範圍）。")
        return

    # 單一到期月份（排除跨月價差單）
    months = [r for r in rows if not r["is_spread"]]
    # 近月＝最小的到期月份
    near = min((r["month"] for r in months), default=None)

    print(f"\n{name}\n")
    print(f"{'到期月份':<12}{'收盤':>8}{'漲跌':>8}{'成交量(口)':>12}{'未平倉':>9}{'時段':>7}")
    print("-" * 58)
    for r in sorted(months, key=lambda x: (x["month"], x["session"])):
        mark = "  ← 近月" if r["month"] == near else ""
        print(f"{r['month']:<12}{r['close']:>8}{r['change']:>8}{r['volume']:>12,}{r['oi']:>9}{r['session']:>7}{mark}")

    # 近月總成交量（含一般＋盤後各時段）
    near_vol = sum(r["volume"] for r in months if r["month"] == near)
    total_vol = sum(r["volume"] for r in months)
    print("-" * 58)
    print(f"近月（{near}）總成交量：{near_vol:,} 口")
    print(f"全部月份總成交量：{total_vol:,} 口")


if __name__ == "__main__":
    main()

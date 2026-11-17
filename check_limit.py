"""
偵測個股「漲停／跌停」狀態：鎖死、打開、還是沒碰到（只讀資料，不下單）。
資料來源：證交所當日「每日收盤行情」，不需要金鑰。

用法：
  python check_limit.py 2454 3443 3661
      → 判斷這幾檔今天的漲跌停狀態
  python check_limit.py 2454 3443 3661 2026-11-13
      → 指定日期（最後一個參數是日期時自動辨識）

判讀邏輯（用當日開高低收）：
  收盤＝漲停價            → 鎖漲停（尾盤仍鎖住）
  最高＝漲停價、收盤<漲停  → 漲停打開（盤中觸及但沒鎖住）
  （跌停同理）
註：日資料看不出盤中「打開→再鎖」的次數，只能判斷「收盤有沒有鎖、盤中有沒有碰到」。
"""
import sys
from datetime import date

from twse import market_ohlc, limit_status


def main():
    args = sys.argv[1:]
    if not args:
        print("請給股票代號，例如：python check_limit.py 2454 3443 3661")
        sys.exit(1)

    # 最後一個參數若像日期（YYYY-MM-DD）就當日期
    day = str(date.today())
    if len(args) > 1 and args[-1].count("-") == 2:
        day = args[-1]
        args = args[:-1]
    codes = args

    print(f"查詢漲跌停狀態  {day}（證交所公開資料）…")
    market = market_ohlc(day)
    if not market:
        print("查無當日資料（可能是假日、尚未收盤，或日期超出範圍）。")
        return

    print()
    print(f"{'代號':<7}{'名稱':<12}{'狀態':<10}{'收盤':>9}{'漲停價':>9}{'最高':>9}{'最低':>9}")
    print("-" * 70)
    for code in codes:
        info = market.get(code)
        if not info:
            print(f"{code:<7}（查無此上市個股當日資料）")
            continue
        st = limit_status(info)
        name = info["name"]
        name_pad = name + "　" * max(0, (6 - len(name)))
        flag = {"鎖漲停": "🔒", "漲停打開": "🔓", "鎖跌停": "🔒", "跌停打開": "🔓"}.get(st["status"], "  ")
        # 一般上市個股是 4 碼數字；權證(6碼)、部分 ETF 漲跌停規則不同，標注提醒
        warn = "" if (len(code) == 4 and code.isdigit()) else "  ⚠非一般個股,規則可能不同"
        print(f"{code:<7}{name_pad}{flag}{st['status']:<8}"
              f"{info['close']:>9.2f}{st['limit_up']:>9.2f}{info['high']:>9.2f}{info['low']:>9.2f}{warn}")

    print("\n🔒=收盤鎖住　🔓=盤中觸及但打開（一般個股漲跌停為 ±10%）")


if __name__ == "__main__":
    main()

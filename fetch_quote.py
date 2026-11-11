"""
抓台股即時報價（只讀行情，不下單）。
資料來源：證交所（上市）／櫃買中心（上櫃）公開 API，不需要金鑰。

用法：
  python fetch_quote.py 2330 2317 0050
不加代號時，預設抓台積電 2330。

註：交易所公開報價約有 5 秒延遲；非盤中時間回傳的是最後一筆收盤快照。
"""
import sys

from twse import realtime


def main():
    codes = sys.argv[1:] or ["2330"]

    print("查詢中…（證交所公開行情）")
    results, missing = realtime(codes)

    for code in missing:
        print(f"⚠️  找不到代號 {code}，略過")

    if not results:
        print("沒有可查的標的。")
        return

    print()
    print(f"{'代號':<8}{'名稱':<12}{'市場':<6}{'成交價':>10}{'漲跌':>9}{'漲跌幅%':>9}{'成交量(張)':>12}  {'時間':<10}")
    print("-" * 82)
    for r in results:
        price = f"{r['price']:.2f}" if r["price"] is not None else "-"
        change = f"{r['change']:+.2f}" if r["change"] is not None else "-"
        pct = f"{r['change_pct']:+.2f}" if r["change_pct"] is not None else "-"
        vol = f"{int(r['volume']):,}" if r["volume"] is not None else "-"
        # 名稱是中文（寬字元），用手動補空格對齊
        name = r["name"] or ""
        name_pad = name + "　" * max(0, (6 - len(name)))
        print(f"{r['code']:<8}{name_pad}{r['market']:<6}{price:>10}{change:>9}{pct:>9}{vol:>12}  {r['time'] or '-':<10}")

    print("\n完成。")


if __name__ == "__main__":
    main()

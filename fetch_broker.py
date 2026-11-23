"""
抓某一券商分點「買賣超了哪些股票」（分點籌碼，只讀資料）。
資料來源：富邦理財網（嘉實資訊）公開頁面，不需要金鑰。

用法：
  python fetch_broker.py 9600
      → 富邦證券(9600)總公司分點，今日買超/賣超的股票
  python fetch_broker.py 9600 9602
      → 指定分點（a=券商、b=分點代號）

註：參數是「券商代號」不是股票代號；金額單位為「仟元」。
    此為收盤後資料、給人瀏覽的網頁，請勿高頻抓取。
"""
import sys

from broker import branch_flows

TOP = 15


def _fmt(n):
    """仟元 → 億元，附千分位。"""
    return f"{n/100000:,.2f} 億"


def main():
    args = sys.argv[1:]
    if not args:
        print("請給券商代號，例如：python fetch_broker.py 9600")
        sys.exit(1)
    broker = args[0]
    branch = args[1] if len(args) > 1 else None

    print(f"查詢券商分點 {broker}" + (f"-{branch}" if branch else "") + " 的分點進出…")
    date, rows = branch_flows(broker, branch)

    if not rows:
        print("查無資料：可能是券商代號錯誤、當日無交易，或尚未收盤。")
        return

    buys = sorted([r for r in rows if r["net"] > 0], key=lambda r: -r["net"])
    sells = sorted([r for r in rows if r["net"] < 0], key=lambda r: r["net"])

    print(f"\n資料日期：{date}　（金額單位：仟元）\n")

    def show(title, data):
        print(f"── {title}（前 {min(TOP, len(data))} 名）" + "─" * 20)
        print(f"{'代號':<7}{'名稱':<12}{'買進':>12}{'賣出':>12}{'淨額(仟元)':>14}{'淨額':>12}")
        for r in data[:TOP]:
            nm = r["name"] + "　" * max(0, 6 - len(r["name"]))
            print(f"{r['code']:<7}{nm}{r['buy']:>12,}{r['sell']:>12,}{r['net']:>14,}{_fmt(r['net']):>12}")
        print()

    show("🔴 買超股票", buys)
    show("🟢 賣超股票", sells)


if __name__ == "__main__":
    main()

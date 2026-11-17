"""
證交所（上市）／櫃買中心（上櫃）公開行情。
只讀資料、不需要任何金鑰，雲端與本機都能用。

- realtime(codes)：即時報價快照（約 5 秒延遲，交易所公開資料）
- daily(code, start, end)：日線歷史（自動判斷上市/上櫃）
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (stock data fetch)",
    "Referer": "https://mis.twse.com.tw/stock/index.jsp",
}


def _get(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def _f(x):
    """字串轉 float，轉不動回 None。"""
    try:
        return float(str(x).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _roc_date(s):
    """民國日期字串 '115/11/02' → date(2026, 11, 2)。"""
    y, m, d = s.strip().split("/")
    return date(int(y) + 1911, int(m), int(d))


def _parse_date(s):
    """接受 '2026-11-02' 或 date 物件。"""
    if isinstance(s, date):
        return s
    return datetime.strptime(s, "%Y-%m-%d").date()


# ---------- 即時報價 ----------

def realtime(codes):
    """
    回傳 (results, missing)：
      results：list of dict，欄位 code/name/price/prev_close/change/change_pct/volume/market/time
      missing：查不到的代號 list
    """
    # 同時問上市與上櫃，交易所只會回實際存在的那一個
    parts = [f"tse_{c}.tw" for c in codes] + [f"otc_{c}.tw" for c in codes]
    ex_ch = urllib.parse.quote("|".join(parts))
    url = ("https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
           f"?json=1&delay=0&ex_ch={ex_ch}")
    data = _get(url)

    found = {}
    for m in data.get("msgArray", []):
        code = m.get("c")
        if not code or code in found:
            continue
        price = _f(m.get("z"))          # 成交價
        if price is None:                # 尚無成交：用最佳買價，再退而用昨收
            price = _f(m.get("b", "-").split("_")[0]) or _f(m.get("y"))
        prev = _f(m.get("y"))            # 昨收
        change = price - prev if price is not None and prev is not None else None
        pct = change / prev * 100 if change is not None and prev else None
        found[code] = {
            "code": code,
            "name": m.get("n"),
            "price": price,
            "prev_close": prev,
            "change": change,
            "change_pct": pct,
            "volume": _f(m.get("v")),           # 累計成交量（張）
            "market": "上市" if m.get("ex") == "tse" else "上櫃",
            "time": m.get("t") or m.get("%"),   # 最後成交時間
        }

    results = [found[c] for c in codes if c in found]
    missing = [c for c in codes if c not in found]
    return results, missing


# ---------- 日線歷史 ----------

def _month_tse(code, year, month):
    """上市單月日線，回傳 list of (date, o, h, l, c, 張)；非上市或無資料回 None。

    證交所 STOCK_DAY 有流量限制，連續查詢可能被暫時擋下（stat 非 OK）。
    這裡遇到被擋就自動重試（遞增等待），真的查不到才回 None。
    """
    url = ("https://www.twse.com.tw/exchangeReport/STOCK_DAY"
           f"?response=json&date={year}{month:02d}01&stockNo={code}")
    data = None
    for attempt in range(6):
        try:
            data = _get(url)
        except Exception:
            data = None            # 被限流時常回傳非 JSON 錯誤頁 → 當作需重試
        if isinstance(data, dict):
            stat = data.get("stat", "")
            if stat == "OK":
                break
            if "沒有" in stat or "查無" in stat:   # 真的查無此上市代號 → 交給櫃買
                return None
        time.sleep(2 * (attempt + 1))   # 例外或被限流：等一下再試
    if not isinstance(data, dict) or data.get("stat") != "OK" or not data.get("data"):
        return None
    rows = []
    for r in data["data"]:
        try:
            d = _roc_date(r[0])
        except Exception:
            continue
        o, h, l, c = _f(r[3]), _f(r[4]), _f(r[5]), _f(r[6])
        shares = _f(r[1])
        if o is None:          # 當天無交易
            continue
        lots = int(round(shares / 1000)) if shares else 0
        rows.append((d, o, h, l, c, lots))
    return rows


def _month_tpex(code, year, month):
    """上櫃單月日線，回傳 list of (date, o, h, l, c, 張)；查不到回 None。"""
    url = ("https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"
           f"?code={code}&date={year}/{month:02d}/01&response=json")
    try:
        data = _get(url)
    except Exception:
        return None
    tables = data.get("tables") or []
    rows_in = tables[0].get("data") if tables else None
    if not rows_in:
        return None
    rows = []
    for r in rows_in:
        try:
            d = _roc_date(r[0])
        except Exception:
            continue
        o, h, l, c = _f(r[3]), _f(r[4]), _f(r[5]), _f(r[6])
        lots = _f(r[1])        # 櫃買的成交量單位是「仟股」＝張
        if o is None:
            continue
        rows.append((d, o, h, l, c, int(lots) if lots else 0))
    return rows


def daily(code, start, end):
    """
    回傳日線 rows：list of (date, open, high, low, close, volume_張)，涵蓋 start~end（含）。
    自動判斷上市/上櫃。start、end 可為 'YYYY-MM-DD' 或 date。
    """
    start_d, end_d = _parse_date(start), _parse_date(end)
    rows, seen = [], set()
    cur = date(start_d.year, start_d.month, 1)
    is_tpex = None
    while cur <= end_d:
        if is_tpex is None:
            got = _month_tse(code, cur.year, cur.month)
            if got is None:
                got = _month_tpex(code, cur.year, cur.month)
                if got is not None:
                    is_tpex = True
            else:
                is_tpex = False
        elif is_tpex:
            got = _month_tpex(code, cur.year, cur.month)
        else:
            got = _month_tse(code, cur.year, cur.month)

        for r in got or []:
            if start_d <= r[0] <= end_d and r[0] not in seen:
                seen.add(r[0])
                rows.append(r)

        cur = date(cur.year + 1, 1, 1) if cur.month == 12 else date(cur.year, cur.month + 1, 1)
        time.sleep(0.5)   # 禮貌間隔，降低被證交所限流的機會

    rows.sort(key=lambda r: r[0])
    return rows


# ---------- 全市場當日 OHLC 與漲跌停偵測 ----------

import math as _math
import re as _re

_MI_URL = ("https://www.twse.com.tw/exchangeReport/MI_INDEX"
           "?response=json&type=ALL&date={}")


def _tick(p):
    """台股股票的升降單位（檔位）。"""
    if p < 10:
        return 0.01
    if p < 50:
        return 0.05
    if p < 100:
        return 0.1
    if p < 500:
        return 0.5
    if p < 1000:
        return 1.0
    return 5.0


def limit_up(prev_close):
    """漲停價＝昨收 ×1.1，無條件捨去到檔位。"""
    t = _tick(prev_close * 1.1)
    return round(_math.floor(prev_close * 1.1 / t + 1e-9) * t, 2)


def limit_down(prev_close):
    """跌停價＝昨收 ×0.9，無條件進位到檔位。"""
    t = _tick(prev_close * 0.9)
    return round(_math.ceil(prev_close * 0.9 / t - 1e-9) * t, 2)


def market_ohlc(day=None):
    """
    抓某日「全部上市個股」的 OHLC。回傳 dict：
      code -> {name, open, high, low, close, prev}
    day 可為 'YYYY-MM-DD' 或 date，預設今天。查無資料回空 dict。
    """
    if day is None:
        d = date.today()
    elif isinstance(day, date):
        d = day
    else:
        d = datetime.strptime(day, "%Y-%m-%d").date()
    url = _MI_URL.format(f"{d.year}{d.month:02d}{d.day:02d}")

    data = None
    for attempt in range(6):
        try:
            data = _get(url)           # 被限流時常回非 JSON → 丟例外 → 重試
        except Exception:
            data = None
        if isinstance(data, dict) and data.get("stat") == "OK":
            break
        time.sleep(2 * (attempt + 1))
    if not isinstance(data, dict) or data.get("stat") != "OK":
        return {}

    table = None
    for t in data.get("tables", []):
        if "每日收盤行情" in t.get("title", ""):
            table = t
            break
    if not table:
        return {}

    def num(x):
        x = _re.sub("<[^>]+>", "", str(x)).replace(",", "").strip()
        try:
            return float(x)
        except ValueError:
            return None

    out = {}
    for r in table["data"]:
        code = r[0].strip()
        o, h, l, c = num(r[5]), num(r[6]), num(r[7]), num(r[8])
        sign = _re.sub("<[^>]+>", "", str(r[9]))      # 漲跌 +/-（可能含色碼）
        diff = num(r[10])
        if c is None or diff is None:
            continue
        signed = -diff if "-" in sign else diff
        out[code] = {
            "name": r[1].strip(),
            "open": o, "high": h, "low": l, "close": c,
            "prev": round(c - signed, 2),
        }
    return out


def limit_status(info):
    """
    依單日 OHLC 判斷漲跌停狀態。
    回傳 dict：up/down 漲跌停價、狀態字串、是否曾觸及、收盤是否鎖住。
    狀態：鎖漲停 / 漲停打開 / 曾觸漲停 / 鎖跌停 / 跌停打開 / 正常。
    """
    prev = info["prev"]
    hi, lo, c = info["high"], info["low"], info["close"]
    up, dn = limit_up(prev), limit_down(prev)
    eq = lambda a, b: a is not None and abs(a - b) < 1e-6

    touched_up = eq(hi, up)
    locked_up = eq(c, up)
    touched_dn = eq(lo, dn)
    locked_dn = eq(c, dn)

    if locked_up:
        status = "鎖漲停"
    elif touched_up:
        status = "漲停打開"       # 盤中觸漲停、收盤沒鎖住
    elif locked_dn:
        status = "鎖跌停"
    elif touched_dn:
        status = "跌停打開"
    else:
        status = "正常"

    return {
        "limit_up": up, "limit_down": dn,
        "status": status,
        "touched_up": touched_up, "locked_up": locked_up,
        "touched_down": touched_dn, "locked_down": locked_dn,
    }

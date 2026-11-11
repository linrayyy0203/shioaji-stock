"""
期交所（TAIFEX）股票／ETF 期貨每日行情。
只讀資料、不需要金鑰。

- resolve(code)：把個股/ETF 代號（如 '0052'）對應到期貨商品代碼（如 'VHF'）
- daily(code, date)：抓某日各到期月份的行情（收盤、成交量、未平倉）

資料為期交所「收盤後」當日官方統計；盤中查不到當天資料。
"""
import urllib.parse
import urllib.request
from datetime import date as _date
from datetime import datetime

_HEADERS = {"User-Agent": "stock data fetch"}
_REPORT_URL = "https://www.taifex.com.tw/cht/3/futDailyMarketReport"
_DOWN_URL = "https://www.taifex.com.tw/cht/3/futDataDown"

_product_cache = None


def _get(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def _post(url, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def _products():
    """回傳 dict：個股/ETF 代號 → (期貨商品代碼, 期貨名稱)。只抓一次並快取。"""
    global _product_cache
    if _product_cache is not None:
        return _product_cache
    import re
    html = _get(_REPORT_URL).decode("utf-8", "replace")
    # 例： value="VHF">0052富邦科技ETF期貨   /   value="CDF">2330台積電期貨
    pattern = re.compile(r'value="([A-Z0-9]{2,4})">(\d{4})([^<(]*?期貨)')
    mapping = {}
    for cid, ticker, name in pattern.findall(html):
        mapping.setdefault(ticker, (cid, ticker + name))
    _product_cache = mapping
    return mapping


def resolve(code):
    """個股/ETF 代號 → (期貨商品代碼, 名稱)；查不到回 None。"""
    return _products().get(str(code).strip())


def daily(code, date=None):
    """
    抓某日該標的各到期月份期貨行情。
    date 可為 'YYYY-MM-DD' 或 date，預設今天。
    回傳 (name, rows)：
      name：期貨商品名稱（查不到商品時為 None）
      rows：list of dict，欄位 month/session/close/change/volume/oi/settle/is_spread
    """
    info = resolve(code)
    if info is None:
        return None, []
    cid, name = info

    if date is None:
        d = _date.today()
    elif isinstance(date, _date):
        d = date
    else:
        d = datetime.strptime(date, "%Y-%m-%d").date()
    ds = f"{d.year}/{d.month:02d}/{d.day:02d}"

    raw = _post(_DOWN_URL, {
        "down_type": "1",
        "commodity_id": cid,
        "commodity_id2": "",
        "queryStartDate": ds,
        "queryEndDate": ds,
    }).decode("big5", "replace")

    rows = []
    for line in raw.splitlines():
        parts = line.split(",")
        if len(parts) < 12 or parts[1].strip() != cid:
            continue
        month = parts[2].strip()
        rows.append({
            "month": month,
            "session": parts[17].strip() if len(parts) > 17 else "",
            "close": parts[6].strip(),
            "change": parts[7].strip(),
            "volume": int(parts[9]) if parts[9].strip().isdigit() else 0,
            "oi": parts[11].strip(),
            "settle": parts[10].strip(),
            "is_spread": "/" in month,   # 跨月價差單
        })
    return name, rows

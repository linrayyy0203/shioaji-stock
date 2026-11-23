"""
券商分點進出（分點籌碼）：某一券商分點「買賣超了哪些股票」。
資料來源：富邦理財網（嘉實資訊）公開頁面，不需要金鑰。

說明：
- 參數是「券商代號」，不是股票代號（例：9600＝富邦證券）。
- 金額單位為「仟元」（＝千元）。
- 這是給人瀏覽的網頁，請勿高頻抓取；資料為收盤後統計。
"""
import html
import re
import urllib.request

_URL = "https://fubon-ebrokerdj.fbs.com.tw/z/zg/zgb/zgb0.djhtm?a={a}&b={b}"
_HEADERS = {"User-Agent": "stock data fetch"}


def _get(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("big5", "replace")   # djhtm 頁為 Big5


def branch_flows(broker, branch=None):
    """
    回傳 (date, rows)：
      date：資料日期字串（YYYYMMDD）
      rows：list of dict {code, name, buy, sell, net}，金額單位＝仟元
            net = buy - sell（正＝買超，負＝賣超）
    broker／branch 皆為券商代號；branch 預設同 broker（總公司分點）。
    """
    b = branch or broker
    page = _get(_URL.format(a=broker, b=b))

    m = re.search(r"資料日期：([0-9/]+)", page)
    date = (m.group(1) if m else "").replace("/", "")

    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        link = re.search(r"GenLink2stk\('AS(\w+)','([^']*)'\)", tr)
        if not link:
            continue
        code, name = link.group(1), link.group(2)
        nums = re.findall(r"-?[\d,]+", re.sub(r"<[^>]+>", " ", tr))
        nums = [int(n.replace(",", "")) for n in nums if n.replace(",", "").lstrip("-").isdigit()]
        if len(nums) < 2:
            continue
        buy, sell = nums[0], nums[1]       # 買進金額、賣出金額（仟元）
        rows.append({"code": code, "name": html.unescape(name),
                     "buy": buy, "sell": sell, "net": buy - sell})
    return date, rows

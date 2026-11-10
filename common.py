"""共用：讀金鑰、自動修正同形字、登入 Shioaji。"""
import os
import sys
import unicodedata

# 常見「長得像英文、其實是西里爾字母」的對照表
CONFUSABLES = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X", "У": "Y",
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y",
    "х": "x", "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d",
}


def _fix(s):
    """把同形字換回英文、全形轉半形、去掉剩餘非英數字元。"""
    s = "".join(CONFUSABLES.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in s if ch.isalnum() and ord(ch) < 128)


def _load_env(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def login(verbose=True):
    """讀 .env、修正金鑰、登入，回傳已登入的 api 物件。"""
    here = os.path.dirname(os.path.abspath(__file__))
    _load_env(os.path.join(here, ".env"))

    api_key = _fix(os.environ.get("API_KEY", ""))
    secret_key = _fix(os.environ.get("SECRET_KEY", ""))
    if not api_key or not secret_key:
        print("❌ 還沒填金鑰：請打開同資料夾的 .env，把 API_KEY 和 SECRET_KEY 填進去。")
        sys.exit(1)

    import shioaji as sj

    if verbose:
        print("登入中…")
    api = sj.Shioaji()
    api.login(api_key=api_key, secret_key=secret_key)
    if verbose:
        print("登入成功 ✅\n")
    return api


def get_stock(api, code):
    """用代號取得上市或上櫃股票合約，找不到回傳 None。"""
    return api.Contracts.Stocks.TSE.get(code) or api.Contracts.Stocks.OTC.get(code)

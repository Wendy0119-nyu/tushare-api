from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse

TUSHARE_TOKEN = "a11d0a906b4085f62bd841135364028d51ae34a5254910687c68c280"
TUSHARE_URL = "http://api.tushare.pro"

def tushare_call(api_name, params, fields):
    payload = {
        "api_name": api_name,
        "token": TUSHARE_TOKEN,
        "params": params,
        "fields": fields
    }
    req = urllib.request.Request(
        TUSHARE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    data = raw.get("data") or {}
    fields_list = data.get("fields") or []
    items = data.get("items") or []
    return [dict(zip(fields_list, item)) for item in items]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        ts_code = params.get("code", [""])[0]

        try:
            # Get daily price (last 30 trading days)
            rows = tushare_call(
                "daily",
                {"ts_code": ts_code, "limit": 30},
                "ts_code,trade_date,open,high,low,close,vol,pct_chg,amount"
            )
            rows.sort(key=lambda x: x.get("trade_date", ""), reverse=True)

            if not rows:
                # Try basic info
                result = {"error": "no data", "code": ts_code}
            else:
                latest = rows[0]
                prev = rows[1] if len(rows) > 1 else latest
                close = float(latest.get("close") or 0)
                prev_close = float(prev.get("close") or close)
                chg = close - prev_close
                pct = (chg / prev_close * 100) if prev_close else 0

                result = {
                    "code": ts_code,
                    "price": round(close, 2),
                    "open": round(float(latest.get("open") or 0), 2),
                    "high": round(float(latest.get("high") or 0), 2),
                    "low": round(float(latest.get("low") or 0), 2),
                    "chg": round(chg, 2),
                    "pct": round(float(latest.get("pct_chg") or pct), 2),
                    "vol": latest.get("vol"),
                    "trade_date": latest.get("trade_date"),
                    "history": [round(float(r.get("close") or 0), 2) for r in reversed(rows)]
                }

            body = json.dumps(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

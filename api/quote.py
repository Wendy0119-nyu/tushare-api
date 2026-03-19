from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse

TUSHARE_TOKEN = "a11d0a906b4085f62bd841135364028d51ae34a5254910687c68c280"
TUSHARE_URL = "http://api.tushare.pro"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        ts_code = params.get("code", [""])[0]

        payload = {
            "api_name": "daily",
            "token": TUSHARE_TOKEN,
            "params": {
                "ts_code": ts_code,
                "limit": 30
            },
            "fields": "ts_code,trade_date,open,high,low,close,vol,pct_chg"
        }

        req = urllib.request.Request(
            TUSHARE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            items = raw.get("data", {}).get("items", [])
            fields = raw.get("data", {}).get("fields", [])
            rows = [dict(zip(fields, item)) for item in items]
            rows.sort(key=lambda x: x.get("trade_date",""), reverse=True)

            if rows:
                latest = rows[0]
                result = {
                    "code": ts_code,
                    "price": latest.get("close"),
                    "open": latest.get("open"),
                    "high": latest.get("high"),
                    "low": latest.get("low"),
                    "pct_chg": latest.get("pct_chg"),
                    "vol": latest.get("vol"),
                    "trade_date": latest.get("trade_date"),
                    "history": [r.get("close") for r in reversed(rows)]
                }
            else:
                result = {"error": "no data"}

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

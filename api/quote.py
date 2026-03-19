from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse

TUSHARE_TOKEN = "a11d0a906b4085f62bd841135364028d51ae34a5254910687c68c280"
TUSHARE_URL = "http://api.tushare.pro"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        ts_code = params.get("code", ["600519.SH"])[0]

        payload = {
            "api_name": "daily",
            "token": TUSHARE_TOKEN,
            "params": {"ts_code": ts_code, "limit": 30},
            "fields": "ts_code,trade_date,open,high,low,close,vol,pct_chg"
        }

        try:
            req = urllib.request.Request(
                TUSHARE_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode("utf-8"))

            # Return raw response so we can see the structure
            result = {"debug": raw}

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

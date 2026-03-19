from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse, datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", ["000001"])[0]

        # Strip .SZ/.SH suffix if present, keep just the 6-digit code
        raw_code = code.split(".")[0]
        suffix = code.split(".")[1].upper() if "." in code else "SH"

        try:
            # Use Sina Finance API - completely free, no key needed
            # Works for both SH and SZ stocks
            symbol = ("sh" if suffix == "SH" else "sz") + raw_code
            url = "https://hq.sinajs.cn/list=" + symbol
            req = urllib.request.Request(url, headers={
                "Referer": "https://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0"
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("gbk")

            # Parse Sina response format:
            # var hq_str_sh600519="贵州茅台,1820.00,1830.11,1815.00,1825.00,1810.00,..."
            content = raw.split('"')[1] if '"' in raw else ""
            if not content or content == "":
                self.respond({"error": "no data", "code": code})
                return

            parts = content.split(",")
            if len(parts) < 10:
                self.respond({"error": "parse error", "raw": content[:100]})
                return

            name     = parts[0]
            price    = float(parts[3])   # current price
            open_p   = float(parts[1])   # open
            prev     = float(parts[2])   # prev close
            high     = float(parts[4])
            low      = float(parts[5])
            chg      = round(price - prev, 2)
            pct      = round((chg / prev) * 100, 2) if prev else 0
            vol      = int(parts[8]) if parts[8].isdigit() else 0
            amount   = float(parts[9]) if parts[9] else 0
            date     = parts[30] if len(parts) > 30 else ""
            time_str = parts[31] if len(parts) > 31 else ""

            result = {
                "code": code,
                "name": name,
                "price": price,
                "open": open_p,
                "high": high,
                "low": low,
                "prev_close": prev,
                "chg": chg,
                "pct": pct,
                "vol": vol,
                "amount": amount,
                "date": date,
                "time": time_str,
                "history": []
            }
            self.respond(result)

        except Exception as e:
            self.respond({"error": str(e), "code": code})

    def respond(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

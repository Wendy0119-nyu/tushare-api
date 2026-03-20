from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", ["000001.SH"])[0]

        try:
            symbol = self.to_sina_symbol(code)
            url = "https://hq.sinajs.cn/list=" + symbol
            req = urllib.request.Request(url, headers={
                "Referer": "https://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0"
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("gbk")

            content = raw.split('"')[1] if '"' in raw else ""
            if not content:
                self.respond({"error": "no data", "code": code, "symbol": symbol})
                return

            parts = content.split(",")

            # HK stocks have different field order than A shares
            if code.upper().endswith(".HK"):
                result = self.parse_hk(code, parts)
            else:
                result = self.parse_a(code, parts)

            self.respond(result)

        except Exception as e:
            self.respond({"error": str(e), "code": code})

    def to_sina_symbol(self, code):
        code_upper = code.upper()
        if code_upper.endswith(".SH"):
            return "sh" + code.split(".")[0]
        elif code_upper.endswith(".SZ"):
            return "sz" + code.split(".")[0]
        elif code_upper.endswith(".HK"):
            # Sina HK format: hk00700, hk02097 (always 5 digits, zero-padded)
            num = code.split(".")[0].lstrip("0")
            return "hk" + num.zfill(5)
        else:
            return "sh" + code

    def parse_a(self, code, parts):
        if len(parts) < 10:
            return {"error": "parse error", "code": code}
        prev  = float(parts[2]) if parts[2] else 0
        price = float(parts[3]) if parts[3] else 0
        chg   = round(price - prev, 2)
        pct   = round((chg / prev) * 100, 2) if prev else 0
        return {
            "code": code, "name": parts[0],
            "price": price, "open": float(parts[1] or 0),
            "high": float(parts[4] or 0), "low": float(parts[5] or 0),
            "prev_close": prev, "chg": chg, "pct": pct,
            "vol": int(parts[8]) if parts[8].isdigit() else 0,
            "date": parts[30] if len(parts) > 30 else "",
            "time": parts[31] if len(parts) > 31 else ""
        }

    def parse_hk(self, code, parts):
        # Sina HK format: name,yesterday_close,today_open,high,low,price,...
        if len(parts) < 8:
            return {"error": "parse error hk", "code": code, "parts_len": len(parts)}
        try:
            name  = parts[1] if len(parts) > 1 else code
            prev  = float(parts[3]) if parts[3] else 0
            price = float(parts[6]) if parts[6] else 0
            open_ = float(parts[4]) if parts[4] else 0
            high  = float(parts[5]) if parts[5] else 0
            low   = float(parts[7]) if parts[7] else 0
            chg   = round(price - prev, 3)
            pct   = round((chg / prev) * 100, 2) if prev else 0
            return {
                "code": code, "name": name,
                "price": price, "open": open_,
                "high": high, "low": low,
                "prev_close": prev, "chg": chg, "pct": pct,
                "date": parts[17] if len(parts) > 17 else "",
                "time": parts[18] if len(parts) > 18 else ""
            }
        except Exception as e:
            return {"error": "hk parse: "+str(e), "parts": parts[:10]}

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

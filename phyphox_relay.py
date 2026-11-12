cat << 'EOF' > phyphox_relay.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading, json

# Default response formatted identically to phyphox
latest_payload = b'{"buffer": {"mag_x": {"buffer": [0.0]}, "mag_y": {"buffer": [0.0]}, "mag_z": {"buffer": [0.0]}}}'

def extract_val(v):
    if isinstance(v, list):
        return float(v[-1]) if v else 0.0
    if isinstance(v, dict) and "buffer" in v:
        return float(v["buffer"][-1]) if v["buffer"] else 0.0
    return float(v) if v is not None else 0.0

# 1. Server on port 5000 that catches HTTP POST data from usb_mag.phyphox
class PhyphoxReceiver(BaseHTTPRequestHandler):
    def do_POST(self):
        global latest_payload
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8', errors='ignore')
        try:
            data = json.loads(body)
            bx = extract_val(data.get("mag_x", 0.0))
            by = extract_val(data.get("mag_y", 0.0))
            bz = extract_val(data.get("mag_z", 0.0))
            
            latest_payload = json.dumps({
                "buffer": {
                    "mag_x": {"buffer": [bx]},
                    "mag_y": {"buffer": [by]},
                    "mag_z": {"buffer": [bz]}
                }
            }).encode('utf-8')
        except Exception as e:
            print("Parse error:", e)
        
        self.send_response(200)
        self.send_header("Connection", "close")
        self.end_headers()

    def log_message(self, format, *args):
        pass

# 2. Server on port 8080 that answers requests from your laptop over USB-C
class LaptopSender(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(latest_payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(latest_payload)

    def log_message(self, format, *args):
        pass

threading.Thread(
    target=lambda: HTTPServer(('127.0.0.1', 5000), PhyphoxReceiver).serve_forever(),
    daemon=True
).start()

print("Relay active! Catching phyphox on :5000 -> Serving USB on :8080...")
HTTPServer(('127.0.0.1', 8080), LaptopSender).serve_forever()
EOF
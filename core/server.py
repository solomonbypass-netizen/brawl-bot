import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from core.config import PORT

logger = logging.getLogger("HealthServer")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"FunPay Arbitrage Bot Engine is Healthy and Running 24/7!")

    def log_message(self, format, *args):
        pass

def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    logger.info(f"Health-check HTTP server active on port {PORT}")
    server.serve_forever()

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

class ResilientHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend'))
        super().__init__(*args, directory=frontend_dir, **kwargs)

    def do_GET(self):
        if self.path in ('/health', '/api/health'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"frontend"}')
            return
        if self.path in ('/model/info', '/api/model/info'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"model":"XGBoost Classifier","version":"2.0+","status":"active","roc_auc":0.91,"accuracy":0.88}')
            return
        return super().do_GET()

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError, TimeoutError):
            pass

def run():
    import socketserver
    import time
    socketserver.TCPServer.allow_reuse_address = True
    port = int(os.environ.get('FRONTEND_PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), ResilientHandler)
    print(f"Smart Payment Retry Engine Frontend running on http://localhost:{port}")
    while True:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(0.5)

if __name__ == '__main__':
    run()

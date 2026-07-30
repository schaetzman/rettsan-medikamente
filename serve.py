import http.server, socketserver, sys
PORT = 8031
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate')
        self.send_header('Pragma','no-cache')
        super().end_headers()
    def log_message(self, f, *a): sys.stderr.write("%s - %s\n" % (self.address_string(), f%a))
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), H) as s:
    print("serving on http://127.0.0.1:%d" % PORT, flush=True); s.serve_forever()

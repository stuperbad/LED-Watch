"""Dev server for the simulator: like http.server but tells the browser never to cache (so edits show on reload)."""
import http.server, sys
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
http.server.ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()

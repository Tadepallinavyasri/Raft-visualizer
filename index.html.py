import http.server
import socketserver
import json

PORT = 8000

class RaftChaosHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API endpoint to serve live cluster status and telemetry
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            cluster_data = {
                "cluster_status": "HEALTHY",
                "total_nodes": 5,
                "active_nodes": 5,
                "nodes": {
                    "N1": {"name": "Node 1", "role": "Leader", "status": "Online", "rate": "100 req/s"},
                    "N2": {"name": "Node 2", "role": "Follower", "status": "Online", "rate": "100 req/s"},
                    "N3": {"name": "Node 3", "role": "Follower", "status": "Online", "rate": "120 req/s"},
                    "N4": {"name": "Node 4", "role": "Follower", "status": "Online", "rate": "100 req/s"},
                    "N5": {"name": "Node 5", "role": "Follower", "status": "Online", "rate": "110 req/s"}
                }
            }
            self.wfile.write(json.dumps(cluster_data).encode('utf-8'))
        else:
            # Serve static files (like index.html) normally
            super().do_GET()

if __name__ == "__main__":
    print(f"[*] Starting PS-13 Consensus Server on http://localhost:{PORT}")
    print("[*] Press Ctrl+C to stop the server.")
    with socketserver.TCPServer(("", PORT), RaftChaosHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server stopped.")
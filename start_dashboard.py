import http.server
import socketserver
import os
import webbrowser

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_server():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"OTC Treasury Dashboard serving at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        webbrowser.open(f"http://localhost:{PORT}/dashboard/index.html")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()

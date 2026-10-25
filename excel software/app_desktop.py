"""
VYAS - Vedic Yield Astrology System
Commercial Desktop Application Wrapper
Author: पं. निखिल व्यास, MA (ज्योतिष) | 9414121172 | inikhilvyas@gmail.com
"""
import sys
import os
import threading
import http.server
import socketserver
import webbrowser

PORT = 8998
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    def log_message(self, format, *args):
        pass # silent

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"VYAS Astrology System running on http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    # Start local background server
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    
    url = f"http://localhost:{PORT}/vyas_astrology_system.html"
    print(f"Opening VYAS Astrology System: {url}")
    
    # Try webview for native desktop window experience if installed, else default browser
    try:
        import webview
        webview.create_window('VYAS - Vedic Yield Astrology System (Commercial Edition)', url, width=1280, height=850)
        webview.start()
    except ImportError:
        webbrowser.open(url)
        print("Running in browser. Press Ctrl+C to close.")
        try:
            t.join()
        except KeyboardInterrupt:
            print("Shutting down VYAS.")

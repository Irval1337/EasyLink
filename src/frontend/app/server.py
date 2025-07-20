import http.server
import socketserver
import os
import urllib.parse
from pathlib import Path
import json
import requests

PORT = 3000

HOP_BY_HOP = {
    'host', 'connection', 'keep-alive', 'proxy-authenticate',
    'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade'
}

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def _forward_headers(self):
        return {
            k: v
            for k, v in self.headers.items()
            if k.lower() not in HOP_BY_HOP
        }
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        print(1)
        # --- SPA‑роуты ------------------------------------------------------
        if path == '/activate-email':
            self.path = '/activate-email.html'
            return super().do_GET()
        if path == '/password':
            self.path = '/password.html'
            return super().do_GET()
        if path == '/':
            self.path = '/index.html'
            return super().do_GET()

        # --- статика -------------------------------------------------------
        static_file = Path('.' + path)
        if static_file.is_file():
            return super().do_GET()

        # --- короткая ссылка ----------------------------------------------
        short_code = path.lstrip('/')
        headers = self._forward_headers()
        headers.setdefault('Accept', '*/*')
        if short_code:
            api_url = f"http://traefik/api/urls/{short_code}?json_response=true"
            try:
                resp = requests.get(api_url, timeout=3, proxies={"http": None, "https": None}, headers=headers)
    
            except Exception as e:
                self._simple(500, f'Backend error: {e}')
                return

            status = resp.status_code
            body   = resp.text  # читаем ДО resp.close()
            # resp.close()  # можно, но после чтения

            # 404
            if status == 404:
                self._simple(404, '<h1>404 Not Found</h1>', 'text/html')
                return


            # 401 пароль — редирект на страницу ввода пароля с передачей short_code
            if status == 401 and (resp.json().get('detail')
                                  == "Password required. Add password param"):
                # Перенаправляем на /password?code=short_code
                self.send_response(302)
                self.send_header('Location', f'/password?code={short_code}')
                self.end_headers()
                return

            # 410 gone
            if status == 410:
                self._simple(410, '<h1>410 URL is no longer active</h1>', 'text/html')
                return

            # --- редирект через json (новый API) -------------------------
            if status == 200:
                try:
                    data = json.loads(body)
                    location = data.get('url')
                except Exception:
                    location = None
                if location:
                    self.send_response(302)
                    self.send_header('Location', location)
                    self.end_headers()
                    self.wfile.write(f'Redirecting to {location}'.encode())
                    return
                self.send_response(200)
                if "content-length" not in (h.lower() for h in resp.headers):
                    self.send_header("Content-Length", str(len(resp.content)))
                self.end_headers()
                self.wfile.write(resp.content)
                return
            self._simple(502, '<h1>502 Bad Gateway</h1>', 'text/html')
            return

        # --- дефолт --------------------------------------------------------
        super().do_GET()

    # util
    def _simple(self, code: int, body: str, ctype: str='text/plain; charset=utf-8'):
        payload = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    
    def guess_type(self, path):
        mimetype = super().guess_type(path)
        # Ensure HTML files are served with correct content type
        if path.endswith('.html'):
            return 'text/html'
        return mimetype

if __name__ == "__main__":
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    print(f"Files in directory: {list(script_dir.glob('*'))}")
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Frontend server running at http://localhost:{PORT}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            httpd.shutdown()

"""World Between Worlds's private loopback UI. No third-party server dependencies."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import urlsplit
import webbrowser

import blackwing_catalog
import blackwing_service
from blackwing_version import TITLE, VERSION

ROOT = Path(__file__).resolve().parent
MAX_REQUEST = 128 * 1024
STATIC = {'/ui/app.js': ('ui/app.js', 'text/javascript; charset=utf-8'),
          '/ui/styles.css': ('ui/styles.css', 'text/css; charset=utf-8')}
DOCS = ('README.md', 'COMMUNITY_RC1.md', 'VALIDATION.md', 'NOTICE.md',
        'SUPPORTED_CUSTOM_SOURCES.txt', 'TESTING.md', 'NINJA_KAGE.md',
        'RECIPES.md', 'SCREENSHOTS.md')


class BlackwingServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, *, data_dir=None):
        self.token = secrets.token_hex(32)
        self.data_dir = data_dir or blackwing_service.user_data_dir()
        self.jobs = blackwing_service.JobManager()
        super().__init__(address, Handler)

    @property
    def origin(self):
        return 'http://127.0.0.1:' + str(self.server_port)


class Handler(BaseHTTPRequestHandler):
    server_version = 'WorldBetweenWorlds'
    sys_version = ''

    def log_message(self, format, *args):
        # Access logs would retain user-local path query strings unnecessarily.
        pass

    def reply(self, code, body=b'', content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def origin_allowed(self):
        expected = '127.0.0.1:' + str(self.server.server_port)
        if self.headers.get('Host') != expected:
            self.reply(403, {'error': 'Untrusted Host header.'})
            return False
        origin = self.headers.get('Origin')
        if origin is not None and origin != self.server.origin:
            self.reply(403, {'error': 'Cross-origin requests are not allowed.'})
            return False
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            self.reply(403, {'error': 'Cross-site requests are not allowed.'})
            return False
        return True

    def authenticated(self):
        value = self.headers.get('X-Blackwing-Token', '')
        if not hmac.compare_digest(value, self.server.token):
            self.reply(403, {'error': 'This window has expired. Reopen World Between Worlds.'})
            return False
        return True

    def do_GET(self):
        if not self.origin_allowed():
            return
        path = urlsplit(self.path).path
        try:
            if path == '/':
                index = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
                self.reply(200, index.replace('{{TOKEN}}', self.server.token).encode('utf-8'), 'text/html; charset=utf-8')
                return
            if path in STATIC:
                filename, mime = STATIC[path]
                self.reply(200, (ROOT / filename).read_bytes(), mime)
                return
            if path.startswith('/docs/') and path.removeprefix('/docs/') in DOCS:
                self.reply(200, (ROOT / path.removeprefix('/docs/')).read_bytes(), 'text/plain; charset=utf-8')
                return
            if path == '/api/health':
                self.reply(200, {'title': TITLE, 'version': VERSION, 'status': 'ready'})
                return
            if path.startswith('/api/') and not self.authenticated():
                return
            if path == '/api/catalog':
                self.reply(200, blackwing_catalog.catalog())
            elif path == '/api/settings':
                self.reply(200, blackwing_service.load_settings(self.server.data_dir))
            elif path.startswith('/api/recipes/'):
                self.reply(200, blackwing_catalog.recipe_details(path.removeprefix('/api/recipes/')))
            elif path.startswith('/api/jobs/'):
                self.reply(200, self.server.jobs.snapshot(path.removeprefix('/api/jobs/')))
            elif path == '/api/updates':
                self.reply(200, {'version': VERSION, 'state': os.environ.get('BLACKWING_UPDATE_STATUS', 'Managed by the launcher at startup.')})
            else:
                self.reply(404, {'error': 'Not found.'})
        except (ValueError, OSError, KeyError) as exc:
            self.reply(400, {'error': str(exc)})

    def read_json(self):
        if self.headers.get('Content-Type', '').split(';', 1)[0].strip() != 'application/json':
            raise ValueError('Expected application/json.')
        if self.headers.get('Transfer-Encoding'):
            raise ValueError('Chunked requests are not supported.')
        try:
            length = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            raise ValueError('Invalid content length.') from None
        if length < 0 or length > MAX_REQUEST:
            raise ValueError('Request is too large or has no content length.')
        return json.loads(self.rfile.read(length))

    def do_POST(self):
        if not self.origin_allowed() or not self.authenticated():
            return
        try:
            value = self.read_json()
            path = urlsplit(self.path).path
            if path == '/api/settings':
                self.reply(200, blackwing_service.save_settings(value, self.server.data_dir))
            elif path == '/api/convert':
                self.reply(202, {'job_id': self.server.jobs.start(value)})
            elif path == '/api/export':
                if not isinstance(value, dict):
                    raise ValueError('Export request must be an object.')
                self.reply(200, blackwing_catalog.export_plan(value.get('ids')))
            else:
                self.reply(404, {'error': 'Not found.'})
        except (ValueError, OSError, KeyError) as exc:
            self.reply(400, {'error': str(exc)})


def main(argv=None):
    parser = argparse.ArgumentParser(description='World Between Worlds — local JK to MotS conversion workbench')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--no-browser', action='store_true', help='Print the private local URL without opening a browser')
    parser.add_argument('--no-update', action='store_true', help='Accepted for direct app launch; the launcher manages updates')
    parser.add_argument('--host', choices=['127.0.0.1'], default='127.0.0.1')
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error('Port must be between 0 and 65535.')
    server = BlackwingServer((args.host, args.port))
    url = server.origin + '/'
    ready = os.environ.get('BLACKWING_READY_FILE')
    if ready:
        path = Path(ready)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'pid': os.getpid(), 'url': url, 'version': VERSION}), encoding='utf-8')
    print(TITLE + ' ' + VERSION + ' — ' + url, flush=True)
    if not args.no_browser:
        threading.Timer(0.1, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

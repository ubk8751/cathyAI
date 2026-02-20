import http.server
import socket
import time

DOCKER_SOCK = "/var/run/docker.sock"
UI_HOST = "webbui_chat"
UI_PORT = 8000

CONTAINERS = [
    "cathyai_webbui_chat",
    "cathyai_webbui_auth_api",
]

def ui_up(timeout=0.3) -> bool:
    try:
        with socket.create_connection((UI_HOST, UI_PORT), timeout=timeout):
            return True
    except OSError:
        return False

def docker_post(path: str) -> None:
    req = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: docker\r\n"
        f"Content-Length: 0\r\n"
        f"Connection: close\r\n\r\n"
    ).encode()

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(DOCKER_SOCK)
    s.sendall(req)
    # drain response
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
    s.close()

def start_container(name: str) -> None:
    docker_post(f"/containers/{name}/start")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Start only if down
        if not ui_up():
            for c in CONTAINERS:
                try:
                    start_container(c)
                except Exception:
                    pass

            deadline = time.time() + 60
            while time.time() < deadline and not ui_up():
                time.sleep(0.5)

        # Redirect the client back to the same URL path.
        # Browser will retry; by then UI should be up.
        self.send_response(302)
        self.send_header("Location", self.path or "/")
        self.end_headers()

http.server.ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

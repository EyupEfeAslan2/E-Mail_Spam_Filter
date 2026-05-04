"""
One-command launcher for the SpamGuard web app.

This starts the FastAPI backend programmatically and opens the browser, so users
do not need to remember the uvicorn command.
"""

import socket
import threading
import time
import webbrowser

import uvicorn


HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def find_free_port(start_port: int = DEFAULT_PORT) -> int:
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, port)) != 0:
                return port
    raise RuntimeError("Uygun boş port bulunamadı.")


def open_browser(url: str) -> None:
    time.sleep(1.5)
    webbrowser.open(url)


def main() -> None:
    port = find_free_port()
    url = f"http://{HOST}:{port}"
    print(f"SpamGuard başlatılıyor: {url}")
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    uvicorn.run("api.main:app", host=HOST, port=port, reload=False)


if __name__ == "__main__":
    main()

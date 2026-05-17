import threading
import time
import webbrowser
import socket
import server

PORT = server.PORT


def _wait_for_server():
    for _ in range(40):
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def _run_flask():
    server.app.run(debug=False, port=PORT, use_reloader=False)


if __name__ == '__main__':
    t = threading.Thread(target=_run_flask, daemon=True)
    t.start()

    if _wait_for_server():
        webbrowser.open(f'http://localhost:{PORT}')
    else:
        import sys
        print('Server konnte nicht gestartet werden.', file=sys.stderr)
        sys.exit(1)

    t.join()

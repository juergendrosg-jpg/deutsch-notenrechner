import threading
import time
import webbrowser
import socket
import server

PORT = server.PORT


def _port_open():
    try:
        with socket.create_connection(('127.0.0.1', PORT), timeout=0.5):
            return True
    except OSError:
        return False


def _wait_for_server():
    for _ in range(40):
        if _port_open():
            return True
        time.sleep(0.25)
    return False


def _run_flask():
    server.app.run(debug=False, port=PORT, use_reloader=False)


if __name__ == '__main__':
    # Läuft das Notenbuch schon (z. B. zweiter Doppelklick), nur den Browser öffnen
    if _port_open():
        webbrowser.open(f'http://localhost:{PORT}')
        raise SystemExit(0)

    t = threading.Thread(target=_run_flask, daemon=True)
    t.start()

    if _wait_for_server():
        webbrowser.open(f'http://localhost:{PORT}')
    else:
        import sys
        print('Server konnte nicht gestartet werden.', file=sys.stderr)
        sys.exit(1)

    t.join()

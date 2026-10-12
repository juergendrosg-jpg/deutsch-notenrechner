from flask import Flask, jsonify, request, Response
from datetime import datetime
import json
import os
import re
import sys
import shutil

PORT = 8765

# Mac-App (PyInstaller): mitgelieferte Dateien liegen in Contents/Resources,
# Daten und per Update geladene index.html in ~/Library/Application Support/Notenbuch.
# NOTENBUCH_APPDIR simuliert diesen Modus beim Entwickeln (z. B. zum Testen der Updates).
if getattr(sys, 'frozen', False):
    STATIC_DIR = os.path.normpath(os.path.join(os.path.dirname(sys.executable), '..', 'Resources'))
    APP_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Notenbuch')
elif os.environ.get('NOTENBUCH_APPDIR'):
    STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = os.environ['NOTENBUCH_APPDIR']
else:
    STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = None

if APP_DIR:
    os.makedirs(APP_DIR, exist_ok=True)
    DATA_FILE = os.path.join(APP_DIR, 'data.json')
    # Frühe Versionen hießen „Notenrechner“ und speicherten dort
    _legacy = os.path.join(os.path.dirname(APP_DIR), 'Notenrechner', 'data.json')
    _bundled = os.path.join(STATIC_DIR, 'data.json')
    for _src in (_legacy, _bundled):
        if not os.path.exists(DATA_FILE) and os.path.exists(_src):
            shutil.copy2(_src, DATA_FILE)
else:
    DATA_FILE = os.path.join(STATIC_DIR, 'data.json')

BUNDLED_HTML = os.path.join(STATIC_DIR, 'index.html')
UPDATE_HTML = os.path.join(APP_DIR, 'index.html') if APP_DIR else None
PREV_HTML = os.path.join(APP_DIR, 'index_vorher.html') if APP_DIR else None
BACKUP_DIR = os.path.join(APP_DIR, 'backups') if APP_DIR else None
MAX_BACKUPS = 20

VERSION_RE = re.compile(r'<meta name="app-version" content="([0-9.]+)"')

app = Flask(__name__)


def _read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _version_of(html):
    m = VERSION_RE.search(html)
    return m.group(1) if m else '0'


def _vtuple(v):
    return tuple(int(x) for x in v.split('.') if x.isdigit())


def _file_version(path):
    if not path or not os.path.exists(path):
        return None
    return _version_of(_read(path))


def _active_html_path():
    # Die per Update geladene Datei gilt nur, solange sie nicht älter ist als die mitgelieferte
    # (sonst würde eine neu installierte App von einem alten Update überdeckt).
    upd = _file_version(UPDATE_HTML)
    if upd and _vtuple(upd) >= _vtuple(_file_version(BUNDLED_HTML) or '0'):
        return UPDATE_HTML
    return BUNDLED_HTML


def _write_atomic(path, text):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)


def _backup_data(label):
    if not os.path.exists(DATA_FILE):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    name = f"data_{label}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    shutil.copy2(DATA_FILE, os.path.join(BACKUP_DIR, name))
    old = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith('data_'))
    for f in old[:-MAX_BACKUPS]:
        os.remove(os.path.join(BACKUP_DIR, f))
    return name


@app.route('/')
def index():
    return Response(_read(_active_html_path()), mimetype='text/html',
                    headers={'Cache-Control': 'no-store'})


@app.route('/api/data', methods=['GET'])
def get_data():
    if not os.path.exists(DATA_FILE):
        return jsonify({'classes': []})
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/data', methods=['POST'])
def save_data():
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})


@app.route('/api/app-info', methods=['GET'])
def app_info():
    return jsonify({
        'version': _file_version(_active_html_path()),
        'updatable': APP_DIR is not None,
        'prevVersion': _file_version(PREV_HTML),
    })


# Nur application/json (kein force=True): fremde Webseiten können ohne CORS-Freigabe
# keinen solchen Request an localhost schicken.
@app.route('/api/update', methods=['POST'])
def install_update():
    if not APP_DIR:
        return jsonify({'error': 'Updates sind nur in der Mac-App möglich.'}), 400
    payload = request.get_json(silent=True) or {}
    html, version = payload.get('html'), payload.get('version')
    if not isinstance(html, str) or not isinstance(version, str):
        return jsonify({'error': 'Ungültige Anfrage.'}), 400
    if _version_of(html) != version or len(html) < 50000 or '/api/data' not in html:
        return jsonify({'error': 'Die heruntergeladene Datei ist unvollständig oder beschädigt.'}), 400
    current_path = _active_html_path()
    current = _version_of(_read(current_path))
    if _vtuple(version) <= _vtuple(current):
        return jsonify({'error': f'Version {version} ist nicht neuer als {current}.'}), 400

    backup = _backup_data(f'v{current}')
    shutil.copy2(current_path, PREV_HTML)
    _write_atomic(UPDATE_HTML, html)
    return jsonify({'ok': True, 'version': version, 'backup': backup})


@app.route('/api/rollback', methods=['POST'])
def rollback():
    if not APP_DIR or not request.is_json:
        return jsonify({'error': 'Ungültige Anfrage.'}), 400
    prev = _file_version(PREV_HTML)
    if not prev:
        return jsonify({'error': 'Keine vorherige Version vorhanden.'}), 400
    _backup_data(f'v{_file_version(_active_html_path())}')
    # Ist die vorherige Version älter als die mitgelieferte, reicht es, das Update zu entfernen.
    if _vtuple(prev) < _vtuple(_file_version(BUNDLED_HTML) or '0'):
        if os.path.exists(UPDATE_HTML):
            os.remove(UPDATE_HTML)
    else:
        _write_atomic(UPDATE_HTML, _read(PREV_HTML))
    os.remove(PREV_HTML)
    return jsonify({'ok': True, 'version': prev})


if __name__ == '__main__':
    # Entwicklung: http://localhost:5000 – die Mac-App startet über launcher.py auf PORT
    app.run(debug=True)

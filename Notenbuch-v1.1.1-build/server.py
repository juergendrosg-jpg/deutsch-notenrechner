from flask import Flask, jsonify, request, Response
import json
import os
import sys
import shutil

PORT = 8765

if getattr(sys, 'frozen', False):
    # Pfad zur ausfuehrbaren Datei: Contents/MacOS/Notenbuch
    # index.html liegt in:          Contents/Resources/index.html
    _exe_dir = os.path.dirname(sys.executable)
    STATIC_DIR = os.path.normpath(os.path.join(_exe_dir, '..', 'Resources'))
    APP_SUPPORT = os.path.join(
        os.path.expanduser('~'), 'Library', 'Application Support', 'Notenbuch'
    )
    os.makedirs(APP_SUPPORT, exist_ok=True)
    DATA_FILE = os.path.join(APP_SUPPORT, 'data.json')
    _bundled = os.path.join(STATIC_DIR, 'data.json')
    if not os.path.exists(DATA_FILE) and os.path.exists(_bundled):
        shutil.copy2(_bundled, DATA_FILE)
else:
    STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FILE = os.path.join(STATIC_DIR, 'data.json')

app = Flask(__name__)

@app.route('/')
def index():
    path = os.path.join(STATIC_DIR, 'index.html')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return Response(content, mimetype='text/html')

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

if __name__ == '__main__':
    app.run(debug=False, port=PORT)
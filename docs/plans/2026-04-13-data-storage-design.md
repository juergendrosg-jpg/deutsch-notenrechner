# Data Storage Design — Python Flask + JSON File

**Date:** 2026-04-13
**Project:** Deutsch Notenrechner (`index.html`)
**Status:** Approved

---

## Problem

`localStorage` is tied to a single browser on a single machine. Data is lost when the browser is cleared or when the app is used on a different device. The app needs durable, portable storage that also works when deployed to a server later.

---

## Decision

**Option A — Python Flask + JSON file**

A minimal Python Flask server serves the app and exposes two REST endpoints for loading and saving all application data. Data is stored in a single `data.json` file on disk.

---

## Architecture

```
Browser (index.html)  ←→  Flask (server.py)  ←→  data.json
```

- The browser opens `http://localhost:5000`
- Flask serves `index.html` as a static file
- All data is read/written via REST API calls

---

## API Endpoints

| Method | Path        | Description                          |
|--------|-------------|--------------------------------------|
| GET    | `/api/data` | Returns full app state as JSON       |
| POST   | `/api/data` | Receives full app state, writes to `data.json` |

Both endpoints use `Content-Type: application/json`.

---

## File Structure

```
claudeapp/
  index.html       # frontend (unchanged UI)
  server.py        # Flask server
  data.json        # persisted data (git-ignored)
  requirements.txt # flask dependency
  docs/
    plans/
      2026-04-13-data-storage-design.md
```

---

## Frontend Changes (`index.html`)

Replace `localStorage` calls with `fetch`:

**Before:**
```js
function loadData() {
    const r = localStorage.getItem(STORAGE_KEY);
    if (r) data = JSON.parse(r);
    migrateData();
}

function saveData() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    showToast();
}
```

**After:**
```js
async function loadData() {
    const r = await fetch('/api/data');
    if (r.ok) data = await r.json();
    migrateData();
}

async function saveData() {
    await fetch('/api/data', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    showToast();
}
```

All call sites of `saveData()` and `loadData()` must be updated to `await` the async calls (or use `.then()`).

---

## Server (`server.py`)

```python
from flask import Flask, jsonify, request, send_from_directory
import json, os

app = Flask(__name__)
DATA_FILE = 'data.json'

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    if not os.path.exists(DATA_FILE):
        return jsonify({'classes': []})
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/api/data', methods=['POST'])
def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(request.get_json(), f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Setup

```bash
pip install flask
python server.py
# open http://localhost:5000
```

---

## Migration to Real Server

When deploying:
1. Copy `server.py` + `index.html` + `data.json` to the server
2. Set `DATA_FILE` to an absolute path (e.g. `/var/data/notenrechner.json`)
3. Run with a production WSGI server (e.g. `gunicorn server:app`)

To migrate to a real database later: only `server.py` changes — the frontend API calls stay identical.

---

## What Does NOT Change

- All UI, grade calculation logic, and modals remain untouched
- The data structure (`data.classes`, students, grades) stays the same
- `migrateData()` continues to work as before

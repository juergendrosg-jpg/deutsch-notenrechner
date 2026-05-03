# Flask Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace localStorage with a Python Flask server that reads/writes `data.json`, so data persists permanently and can later be deployed to a real server.

**Architecture:** A minimal Flask app serves `index.html` and exposes `GET /api/data` and `POST /api/data`. The frontend replaces all `localStorage` calls with `fetch` calls to these endpoints. `saveData()` is fire-and-forget async; `loadData()` is awaited once at startup.

**Tech Stack:** Python 3, Flask, vanilla JS (fetch API)

---

### Task 1: Create `requirements.txt`

**Files:**
- Create: `requirements.txt`

**Step 1: Create the file**

```
flask>=3.0
```

**Step 2: Verify Flask installs**

Run: `pip install -r requirements.txt`
Expected: Flask installs without errors.

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add flask dependency"
```

---

### Task 2: Create `server.py`

**Files:**
- Create: `server.py`

**Step 1: Write `server.py`**

```python
from flask import Flask, jsonify, request, send_from_directory
import json, os

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')

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

**Step 2: Start the server**

Run: `python server.py`
Expected: `Running on http://127.0.0.1:5000`

**Step 3: Test GET endpoint (empty state)**

Run: `curl http://localhost:5000/api/data`
Expected: `{"classes": []}`

**Step 4: Test POST + GET roundtrip**

Run:
```bash
curl -X POST http://localhost:5000/api/data \
  -H "Content-Type: application/json" \
  -d '{"classes": [{"id": "test", "name": "Test"}]}'
curl http://localhost:5000/api/data
```
Expected: second curl returns the saved data.

**Step 5: Commit**

```bash
git add server.py
git commit -m "feat: add Flask server with GET/POST /api/data"
```

---

### Task 3: Create `.gitignore`

**Files:**
- Create: `.gitignore`

**Step 1: Write `.gitignore`**

```
data.json
__pycache__/
*.pyc
.env
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore, exclude data.json"
```

---

### Task 4: Update `loadData()` in `index.html`

**Files:**
- Modify: `index.html` lines 635–637

The current code (line 635–637):
```js
function loadData() {
    try { const r = localStorage.getItem(STORAGE_KEY); if (r) data = JSON.parse(r); } catch(e) {}
    migrateData();
}
```

**Step 1: Replace `loadData()` with async fetch version**

```js
async function loadData() {
    try {
        const r = await fetch('/api/data');
        if (r.ok) data = await r.json();
    } catch(e) { console.error('loadData failed', e); }
    migrateData();
}
```

**Step 2: Update the DOMContentLoaded handler** (line 1706–1707) to await loadData:

Before:
```js
document.addEventListener('DOMContentLoaded', () => {
    loadData();
```

After:
```js
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
```

**Step 3: Verify in browser**

Open `http://localhost:5000`. App should load without JS errors. Previously saved data (if any) should appear.

**Step 4: Commit**

```bash
git add index.html
git commit -m "feat: load data from /api/data instead of localStorage"
```

---

### Task 5: Update `saveData()` in `index.html`

**Files:**
- Modify: `index.html` lines 640–642

The current code (line 640–642):
```js
function saveData() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); showToast(); } catch(e) {}
}
```

**Step 1: Replace `saveData()` with fire-and-forget fetch version**

```js
function saveData() {
    fetch('/api/data', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(() => showToast()).catch(e => console.error('saveData failed', e));
}
```

Note: This is intentionally NOT async/await — it fires the request and continues. No call sites need changing.

**Step 2: Verify in browser**

Make a change (add a class, edit a grade). The toast should appear. Reload the page — data should still be there. Check that `data.json` was created/updated on disk.

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: save data to /api/data instead of localStorage"
```

---

### Task 6: Remove `localStorage` and `STORAGE_KEY`

**Files:**
- Modify: `index.html` line 606

**Step 1: Delete the STORAGE_KEY constant** (line 606):

```js
const STORAGE_KEY = 'deutschNotenrechner_v1';
```

Remove this line entirely.

**Step 2: Search for any remaining localStorage references**

Search in `index.html` for `localStorage` — there should be none left after Tasks 4 and 5.

**Step 3: Verify in browser**

Full smoke test:
- Open `http://localhost:5000`
- Add a class, add students, enter grades
- Reload page — data persists
- Stop and restart `python server.py`, reload — data still persists
- Check browser console — no errors

**Step 4: Commit**

```bash
git add index.html
git commit -m "chore: remove localStorage and STORAGE_KEY"
```

---

## Done

The app now:
- Runs at `http://localhost:5000`
- Persists data in `data.json` on disk
- Survives browser clears, different browsers, machine restarts
- Is ready to deploy to a server by copying `server.py` + `index.html` + `data.json`

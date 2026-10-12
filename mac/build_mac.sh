#!/usr/bin/env bash
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"

# Gebaut wird in einem temporären Ordner: Liegt der entpackte Ordner in einem
# iCloud-synchronisierten Verzeichnis (z. B. Dokumente), hängt macOS laufend
# Zusatzattribute an und codesign bricht mit "detritus not allowed" ab.
WORK="$(mktemp -d /tmp/notenbuch-build.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
cp "$SRC/index.html" "$SRC/server.py" "$SRC/launcher.py" "$SRC/notenbuch.spec" "$WORK/"
cd "$WORK"

echo "==> Metadaten entfernen ..."
xattr -cr .

echo "==> Abhaengigkeiten installieren ..."
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet flask pyinstaller

echo "==> Bundle bauen ..."
.venv/bin/python -m PyInstaller notenbuch.spec --clean --noconfirm

echo "==> App signieren ..."
xattr -cr dist/Notenbuch.app
codesign --force --deep --sign - dist/Notenbuch.app

echo "==> App installieren ..."
osascript -e 'quit app "Notenbuch"' 2>/dev/null || true
pkill -f "Notenbuch.app/Contents/MacOS/Notenbuch" 2>/dev/null || true
rm -rf /Applications/Notenbuch.app
ditto dist/Notenbuch.app /Applications/Notenbuch.app

echo ""
echo "Fertig! Notenbuch ist unter Programme installiert."
echo "Einfach im Finder unter Programme doppelklicken."
echo "Kuenftige Updates gibt es direkt in der App (Versionsnummer unten links anklicken)."

#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

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
cp -R dist/Notenbuch.app /Applications/Notenbuch.app

echo ""
echo "Fertig! Notenbuch ist unter Programme installiert."
echo "Einfach im Finder unter Programme doppelklicken."
echo "Kuenftige Updates gibt es direkt in der App (Versionsnummer unten links anklicken)."

#!/usr/bin/env bash
set -e

echo "==> Metadaten entfernen ..."
xattr -cr .

echo "==> Abhaengigkeiten installieren ..."
pip3 install --quiet flask pyinstaller

echo "==> Bundle bauen ..."
python3 -m PyInstaller notenbuch.spec --clean --noconfirm

echo "==> App signieren ..."
xattr -cr dist/Notenbuch.app
codesign --force --deep --sign - dist/Notenbuch.app

echo "==> App installieren ..."
cp -r dist/Notenbuch.app /Applications/Notenbuch.app

echo ""
echo "Fertig! Notenbuch ist unter Programme installiert."
echo "Einfach im Finder unter Programme doppelklicken."
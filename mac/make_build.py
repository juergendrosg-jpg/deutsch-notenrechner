"""Stellt das Installationspaket für den Mac zusammen: dist-mac/Notenbuch-v<version>.zip

Nur nötig für die Erstinstallation oder wenn sich server.py / launcher.py ändern –
reine index.html-Änderungen kommen per GitHub-Release als In-App-Update.
"""
import os
import re
import shutil
import zipfile

MAC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(MAC_DIR)


def main():
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    version = re.search(r'<meta name="app-version" content="([0-9.]+)"', html).group(1)
    name = f'Notenbuch-v{version}'
    out_dir = os.path.join(ROOT, 'dist-mac', name)
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)

    files = {
        'index.html': os.path.join(ROOT, 'index.html'),
        'server.py': os.path.join(ROOT, 'server.py'),
        'launcher.py': os.path.join(MAC_DIR, 'launcher.py'),
        'notenbuch.spec': os.path.join(MAC_DIR, 'notenbuch.spec'),
        'build_mac.sh': os.path.join(MAC_DIR, 'build_mac.sh'),
        'ANLEITUNG.txt': os.path.join(MAC_DIR, 'ANLEITUNG.txt'),
    }
    for target, src in files.items():
        text = open(src, encoding='utf-8').read().replace('__VERSION__', version)
        # Unix-Zeilenenden, sonst scheitert build_mac.sh auf dem Mac
        with open(os.path.join(out_dir, target), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text.replace('\r\n', '\n'))

    zip_path = out_dir + '.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for target in files:
            z.write(os.path.join(out_dir, target), f'{name}/{target}')
    print(zip_path)


if __name__ == '__main__':
    main()

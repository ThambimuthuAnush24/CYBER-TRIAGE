"""Build only public static assets into dist/. Run from any working directory."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'dist'

def build():
    kb = json.loads((ROOT / 'knowledge.json').read_text(encoding='utf-8'))
    json.loads((ROOT / 'scenarios.json').read_text(encoding='utf-8'))
    html = (ROOT / 'web/index.html').read_text(encoding='utf-8')
    marker = 'data-mode="server"'
    if html.count(marker) != 1:
        raise ValueError('Expected exactly one server mode marker in web/index.html')
    if DEST.is_symlink():
        raise ValueError('dist must not be a symbolic link')
    if DEST.exists():
        shutil.rmtree(DEST)  # dist is a fixed generated directory, never a caller-supplied path.
    DEST.mkdir()
    html = html.replace(marker, 'data-mode="browser"')
    (DEST / 'index.html').write_text(html, encoding='utf-8')
    for name in ['app.js', 'style.css', 'engine.mjs', 'runtime.mjs']:
        shutil.copyfile(ROOT / 'web' / name, DEST / name)
    for name in ['knowledge.json', 'scenarios.json']:
        shutil.copyfile(ROOT / name, DEST / name)
    (DEST / '.nojekyll').touch()
    print(f'Built {DEST} with {len(kb["facts"])} observations and {len(kb["rules"])} rules.')

if __name__ == '__main__':
    build()

"""Download the unmodified assets provided by Figma's design context."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
assets = json.loads((ROOT / 'reference/assets.json').read_text())
jobs = [(item['url'], ROOT / item['path']) for page in assets.values() for item in page.values()]
jobs += [
    ('https://raw.githubusercontent.com/google/fonts/main/ofl/publicsans/PublicSans%5Bwght%5D.ttf', ROOT / 'static/dokyugo/fonts/PublicSans.ttf'),
    ('https://raw.githubusercontent.com/google/fonts/main/ofl/publicsans/OFL.txt', ROOT / 'static/dokyugo/fonts/PublicSans-OFL.txt'),
    ('https://raw.githubusercontent.com/google/fonts/main/ofl/geistmono/GeistMono%5Bwght%5D.ttf', ROOT / 'static/dokyugo/fonts/GeistMono.ttf'),
    ('https://raw.githubusercontent.com/google/fonts/main/ofl/geistmono/OFL.txt', ROOT / 'static/dokyugo/fonts/GeistMono-OFL.txt'),
]

def download(job):
    url, path = job
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        return
    with urlopen(Request(url, headers={'User-Agent': 'DokyuGo local build'}), timeout=45) as response:
        data = response.read()
    if not data or data.lstrip().startswith(b'<!DOCTYPE html'):
        raise ValueError(f'Invalid asset: {path.name}')
    path.write_bytes(data)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, jobs))
    print(f'Verified {len(jobs)} local design assets and font files.')

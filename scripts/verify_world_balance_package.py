"""Independent Issue39 ZIP extraction, inline-source and asset byte receipt."""
import base64
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/review/world-balance-audit'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    html = ROOT / 'dist/heli_trio_galaxy_test.html'
    archive = html.with_suffix('.zip')
    payload = html.read_bytes()
    with tempfile.TemporaryDirectory(prefix='issue39-unzip-') as folder:
        with zipfile.ZipFile(archive) as zipped:
            assert zipped.namelist() == [html.name]
            assert zipped.testzip() is None
            assert not zipped.getinfo(html.name).flag_bits & 1
            extracted = Path(zipped.extract(html.name, folder))
        assert extracted.read_bytes() == payload
    text = payload.decode('utf-8')
    sources = {
        'galaxy-worlds-js': 'assets/worlds/worlds.js',
        'galaxy-score-js': 'assets/score/score.js',
        'galaxy-selection-js': 'assets/selection/selection.js',
    }
    for identity, path in sources.items():
        inline = re.search(r'<script id="' + identity + r'">(.*?)</script>', text, re.S)
        assert inline and inline[1] == (ROOT / path).read_text(), path
    scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', text, re.S)
    assert len(scripts) == 27
    for script in scripts:
        subprocess.run(['node', '--check'], input=script, text=True, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    build = json.loads((OUT / 'build.json').read_text())
    embedded = {}
    for path in build['embedded_external_png_files'] + build['embedded_external_audio_files']:
        data = (ROOT / path).read_bytes()
        assert base64.b64encode(data) in payload, path
        embedded[path] = sha(data)
    assert sha(payload) == build['sha256']
    receipt = {
        'html_bytes': len(payload), 'html_sha256': sha(payload),
        'zip_bytes': archive.stat().st_size, 'zip_sha256': sha(archive.read_bytes()),
        'entries': [html.name], 'CRC': 'passed',
        'separate_directory_extraction_full_byte_equality': True,
        'changed_JS_source_exactly_embedded': sources,
        'JavaScript_blocks_node_syntax_passed': len(scripts),
        'original_asset_bytes_embedded': embedded,
        'offline_browser_evidence': [
            'tests/world_balance_labels-offline/test-results.json',
            'tests/galaxy_standalone/test-results.json',
        ],
        'local_file_navigation_limit': 'Managed Chrome file navigation was not bypassed. Exact HTML is injected into an isolated origin with network disabled. Real Galaxy file association and speaker listening remain unverified.',
    }
    (OUT / 'standalone-integrity.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'original_asset_bytes_embedded'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    verify()

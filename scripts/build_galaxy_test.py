"""Build a self-contained Galaxy test HTML without editing game source files."""
import base64
import hashlib
import json
import mimetypes
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist/heli_trio_galaxy_test.html'


def build():
    source = (ROOT / 'index.html').read_text()
    css_path = ROOT / 'assets/selection/selection.css'
    js_path = ROOT / 'assets/selection/selection.js'
    embedded = {}

    def data_url(path):
        path = path.resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError(f'Asset must be inside the repository: {path}')
        if path not in embedded:
            mime = mimetypes.guess_type(path.name)[0]
            if not mime:
                raise ValueError(f'Unknown asset type: {path.name}')
            embedded[path] = f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
        return embedded[path]

    def inline_css_url(match):
        value = match.group(1).strip().strip('\"\'')
        if value.startswith('data:') or value.startswith('#'):
            return match.group(0)
        return 'url("' + data_url(css_path.parent / value) + '")'

    css = re.sub(r'url\(([^)]+)\)', inline_css_url, css_path.read_text())
    javascript = js_path.read_text()
    score_css = (ROOT / 'assets/score/score.css').read_text()
    score_javascript = (ROOT / 'assets/score/score.js').read_text()
    assert '</style' not in (css + score_css).lower() and '</script' not in (javascript + score_javascript).lower()
    stylesheet = '<link rel="stylesheet" href="assets/selection/selection.css">'
    script = '<script src="assets/selection/selection.js"></script>'
    assert source.count(stylesheet) == 1 and source.count(script) == 1
    # Suppress Android's native rectangular tap flash, without touching source CSS.
    mobile_css = '#menu .select-hit{-webkit-tap-highlight-color:transparent}'
    result = source.replace(stylesheet, '<style id="galaxy-selection-css">' + css +
                            '</style><style id="galaxy-mobile-touch">' + mobile_css + '</style>')
    result = result.replace(script, '<script id="galaxy-selection-js">' + javascript + '</script>')
    result = result.replace('<link rel="stylesheet" href="assets/score/score.css">',
                            '<style id="galaxy-score-css">' + score_css + '</style>')
    result = result.replace('<script src="assets/score/score.js"></script>',
                            '<script id="galaxy-score-js">' + score_javascript + '</script>')

    def inline_resource(match):
        return match.group(1) + data_url(ROOT / match.group(2)) + match.group(3)

    result = re.sub(r'((?:src|href|xlink:href)=[\"\'])(assets/(?:selection|audio|score)/[^\"\']+)([\"\'])', inline_resource, result)
    original_scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S)
    built_scripts = re.findall(r'<script[^>]*>(.*?)</script>', result, re.S)
    assert built_scripts == original_scripts + [score_javascript, javascript], 'Current source scripts changed during packaging'

    class DependencyCheck(HTMLParser):
        def handle_starttag(self, tag, attributes):
            for key, value in attributes:
                if key in ['src', 'href', 'xlink:href'] and value:
                    assert value.startswith(('data:', '#')), f'External dependency: {tag} {key}={value}'

    DependencyCheck().feed(result)
    for value in re.findall(r'url\(([^)]+)\)', result):
        assert value.strip('\"\' ').startswith(('data:', '#')), 'External CSS dependency'
    assert not re.search(r'@import\s', result, re.I)
    note = '\n<!-- Self-contained Galaxy test build: current source scripts preserved; all resources embedded. -->\n'
    result = result.replace('<!doctype html>', '<!doctype html>' + note, 1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(result)
    return {
        'output': str(OUTPUT.relative_to(ROOT)),
        'bytes': OUTPUT.stat().st_size,
        'sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'preserved_source_inline_scripts': len(original_scripts),
        'inlined_selection_scripts': 1,
        'inlined_selection_stylesheets': 1,
        'inlined_score_scripts': 1,
        'inlined_score_stylesheets': 1,
        'embedded_external_png_files': [str(path.relative_to(ROOT)) for path in sorted(embedded) if path.suffix.lower()=='.png'],
        'embedded_external_audio_files': [str(path.relative_to(ROOT)) for path in sorted(embedded) if path.suffix.lower()=='.mp3'],
        'external_dependencies': 0,
        'galaxy_only_style': 'Disable the browser native selection-button tap flash; packaging does not edit source files.',
    }


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))

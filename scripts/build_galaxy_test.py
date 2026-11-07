"""Build a self-contained Galaxy test HTML without editing game source files."""
import base64
import hashlib
import json
import mimetypes
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist/heli_trio_galaxy_test.html'


def build():
    source = (ROOT / 'index.html').read_text()
    manifest_path = ROOT / 'assets/snowfield/asset_manifest.json'
    manifest_text = manifest_path.read_text()
    manifest = json.loads(manifest_text)
    embedded_manifest = re.search(r'<template id="snowfieldManifest">(.*?)</template>', source, re.S)
    assert embedded_manifest and unescape(embedded_manifest[1]) == manifest_text, 'Native/standalone must use the supplied manifest unchanged'
    assert hashlib.sha256((manifest_path.parent / manifest['background']['path']).read_bytes()).hexdigest() == manifest['background']['sha256'], 'Preserve the approved snowfield background'
    volcano_path = ROOT / 'assets/volcano/asset_manifest.json'
    volcano_text = volcano_path.read_text()
    volcano_template = re.search(r'<template id="volcanoManifest">(.*?)</template>', source, re.S)
    assert volcano_template and unescape(volcano_template[1]) == volcano_text, 'Preserve the exact volcano frame manifest'
    volcano_manifest = json.loads(volcano_text)
    assert hashlib.sha256((volcano_path.parent / volcano_manifest['background']['path']).read_bytes()).hexdigest() == volcano_manifest['background']['sha256']
    for actor in volcano_manifest['monsters']:
        for kind in ['base', 'atlas']:
            assert hashlib.sha256((volcano_path.parent / actor[kind]).read_bytes()).hexdigest() == actor[kind+'_sha256']
    breath_path = ROOT / 'assets/volcano/effects/magma_dragon_breath_static.png'
    assert hashlib.sha256(breath_path.read_bytes()).hexdigest() == 'a9600ff8d4c827d8d5ac200c5c508ff636d008398ec985a5fb259c65913fa979', 'Preserve the supplied static breath PNG'
    storm_path = ROOT / 'assets/storm_sky/asset_manifest.json'
    storm_text = storm_path.read_text()
    storm_manifest = json.loads(storm_text)
    storm_template = re.search(r'<template id="stormSkyManifest">(.*?)</template>', source, re.S)
    assert storm_template and unescape(storm_template[1]) == storm_text
    for asset in [storm_manifest['background']] + storm_manifest['monsters']:
        name = asset.get('path', asset.get('base'))
        assert hashlib.sha256((storm_path.parent/name).read_bytes()).hexdigest() == asset['sha256']
    storm_names = ['config', 'spawns', 'storm_sky', 'combat', 'boss_combat']
    storm_scripts = {name: (storm_path.parent/(name+'.js')).read_text() for name in storm_names}
    assert all('</script' not in value.lower() for value in storm_scripts.values())
    machine_path = ROOT / 'assets/machine_fortress/asset_manifest.json'
    machine_text = machine_path.read_text()
    machine_manifest = json.loads(machine_text)
    machine_template = re.search(r'<template id="machineFortressManifest">(.*?)</template>', source, re.S)
    assert machine_template and unescape(machine_template[1]) == machine_text
    assert hashlib.sha256((machine_path.parent/'background/machine_fortress_background_approved.png').read_bytes()).hexdigest() == '89990eeac3ae96c8ed5c2d9af2d90a5f3d8e51e95ccecf3757db1f9e21f9f124'
    for row in machine_manifest['files']:
        assert hashlib.sha256((machine_path.parent/row['path']).read_bytes()).hexdigest() == row['sha256']
    machine_javascript = (machine_path.parent/'machine_fortress.js').read_text()
    assert '</script' not in machine_javascript.lower()
    machine_combat_scripts = {name:(machine_path.parent/(name+'.js')).read_text() for name in ['config','spawns','combat','boss_combat']}
    assert all('</script' not in value.lower() for value in machine_combat_scripts.values())
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
    item_javascript = (ROOT / 'assets/item_monster/item_monster.js').read_text()
    controls_css = (ROOT / 'assets/controls/controls.css').read_text()
    controls_javascript = (ROOT / 'assets/controls/controls.js').read_text()
    world_css = (ROOT / 'assets/worlds/worlds.css').read_text()
    world_javascript = (ROOT / 'assets/worlds/worlds.js').read_text()
    difficulty_javascript = (ROOT / 'assets/worlds/difficulty.js').read_text()
    snowfield_javascript = (ROOT / 'assets/snowfield/snowfield.js').read_text()
    volcano_spawns_javascript = (ROOT / 'assets/volcano/spawns.js').read_text()
    volcano_javascript = (ROOT / 'assets/volcano/volcano.js').read_text()
    volcano_combat_javascript = (ROOT / 'assets/volcano/combat.js').read_text()
    volcano_boss_javascript = (ROOT / 'assets/volcano/boss_combat.js').read_text()
    snow_spawns_javascript = (ROOT / 'assets/snowfield/spawns.js').read_text()
    snow_combat_javascript = (ROOT / 'assets/snowfield/combat.js').read_text()
    snow_boss_javascript = (ROOT / 'assets/snowfield/boss_combat.js').read_text()
    assert '</style' not in (css + score_css + controls_css + world_css).lower() and '</script' not in (javascript + score_javascript + item_javascript + controls_javascript + world_javascript + difficulty_javascript + volcano_spawns_javascript + snowfield_javascript + volcano_javascript + volcano_combat_javascript + volcano_boss_javascript + snow_combat_javascript + snow_boss_javascript + snow_spawns_javascript).lower()
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
    result = result.replace('<script src="assets/item_monster/item_monster.js"></script>',
                            '<script id="galaxy-item-monster-js">' + item_javascript + '</script>')
    result = result.replace('<link rel="stylesheet" href="assets/controls/controls.css">',
                            '<style id="galaxy-controls-css">' + controls_css + '</style>')
    result = result.replace('<script src="assets/controls/controls.js"></script>',
                            '<script id="galaxy-controls-js">' + controls_javascript + '</script>')
    result = result.replace('<link rel="stylesheet" href="assets/worlds/worlds.css">',
                            '<style id="galaxy-worlds-css">' + world_css + '</style>')
    result = result.replace('<script src="assets/worlds/worlds.js"></script>',
                            '<script id="galaxy-worlds-js">' + world_javascript + '</script>')

    result = result.replace('<script src="assets/worlds/difficulty.js"></script>',
                            '<script id="galaxy-difficulty-js">' + difficulty_javascript + '</script>')
    result = result.replace('<script src="assets/volcano/spawns.js"></script>',
                            '<script id="galaxy-volcano-spawns-js">' + volcano_spawns_javascript + '</script>')
    result = result.replace('<script src="assets/snowfield/snowfield.js"></script>',
                            '<script id="galaxy-snowfield-js">' + snowfield_javascript + '</script>')
    result = result.replace('<script src="assets/volcano/volcano.js"></script>',
                            '<script id="galaxy-volcano-js">' + volcano_javascript + '</script>')
    result = result.replace('<script src="assets/volcano/combat.js"></script>',
                            '<script id="galaxy-volcano-combat-js">' + volcano_combat_javascript + '</script>')
    result = result.replace('<script src="assets/volcano/boss_combat.js"></script>',
                            '<script id="galaxy-volcano-boss-js">' + volcano_boss_javascript + '</script>')
    result = result.replace('<script src="assets/snowfield/spawns.js"></script>',
                            '<script id="galaxy-snow-spawns-js">' + snow_spawns_javascript + '</script>')
    result = result.replace('<script src="assets/snowfield/combat.js"></script>',
                            '<script id="galaxy-snow-combat-js">' + snow_combat_javascript + '</script>')
    result = result.replace('<script src="assets/snowfield/boss_combat.js"></script>',
                            '<script id="galaxy-snow-boss-js">' + snow_boss_javascript + '</script>')

    for name, text in storm_scripts.items():
        tag = '<script src="assets/storm_sky/'+name+'.js"></script>'
        assert result.count(tag) == 1
        result = result.replace(tag, '<script id="galaxy-storm-'+name+'-js">'+text+'</script>')
    result = result.replace('<script src="assets/machine_fortress/machine_fortress.js"></script>',
                            '<script id="galaxy-machine-fortress-js">'+machine_javascript+'</script>')
    for name,text in machine_combat_scripts.items():
        result = result.replace('<script src="assets/machine_fortress/'+name+'.js"></script>',
                                '<script id="galaxy-machine-'+name+'-js">'+text+'</script>')

    def inline_resource(match):
        return match.group(1) + data_url(ROOT / match.group(2)) + match.group(3)

    result = re.sub(r'((?:src|href|xlink:href)=[\"\'])(assets/(?:selection|audio|score|item_monster|snowfield|volcano|storm_sky|machine_fortress)/[^\"\']+)([\"\'])', inline_resource, result)
    volcano_audio = ['assets/audio/volcano_stage.wav', 'assets/audio/volcano_boss.wav']
    for name in volcano_audio:
        assert data_url(ROOT / name) in result, 'Embed the current Volcano WAV unchanged'
    storm_audio = ['assets/audio/storm_sky_stage.wav', 'assets/audio/storm_sky_boss.wav']
    for name in storm_audio:
        assert data_url(ROOT / name) in result, 'Embed both current Storm Sky trial WAVs unchanged'
    original_scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S)
    built_scripts = re.findall(r'<script[^>]*>(.*?)</script>', result, re.S)
    assert built_scripts == [world_javascript, difficulty_javascript, machine_combat_scripts['config'], machine_combat_scripts['spawns'], storm_scripts['config'], storm_scripts['spawns'], volcano_spawns_javascript, snowfield_javascript, volcano_javascript, volcano_combat_javascript, volcano_boss_javascript, snow_spawns_javascript, snow_combat_javascript, snow_boss_javascript, storm_scripts['storm_sky'], storm_scripts['combat'], storm_scripts['boss_combat'], machine_javascript, machine_combat_scripts['combat'], machine_combat_scripts['boss_combat'], item_javascript, controls_javascript] + original_scripts + [score_javascript, javascript], 'Current source scripts changed during packaging'

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
        'inlined_item_monster_scripts': 1,
        'inlined_controls_scripts': 1,
        'inlined_controls_stylesheets': 1,
        'inlined_world_scripts': 1,
        'inlined_regional_difficulty_scripts': 1,
        'inlined_snowfield_scripts': 1,
        'inlined_volcano_scripts': 1,
        'inlined_volcano_spawns_scripts': 1,
        'inlined_volcano_combat_scripts': 1,
        'inlined_volcano_boss_scripts': 1,
        'embedded_static_breath_png': True,
        'embedded_volcano_manifest': True,
        'embedded_volcano_frames': sum(actor['frame_count'] for actor in volcano_manifest['monsters']),
        'inlined_snow_combat_scripts': 1,
        'inlined_snow_spawns_scripts': 1,
        'inlined_snow_boss_scripts': 1,
        'embedded_snowfield_manifest': True,
        'inlined_world_stylesheets': 1,
        'embedded_external_png_files': [str(path.relative_to(ROOT)) for path in sorted(embedded) if path.suffix.lower()=='.png'],
        'embedded_external_audio_files': [str(path.relative_to(ROOT)) for path in sorted(embedded) if path.suffix.lower() in ['.mp3', '.wav']],
        'embedded_volcano_bgm': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in volcano_audio},
        'embedded_storm_sky_bgm': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in storm_audio},
        'embedded_machine_fortress': {'pngs': len(machine_manifest['files'])+1, 'normal_combat_trial': True, 'boss_patterns_and_overdrive_trial': True, 'original_manifest': True, 'scripts': 5},
        'embedded_storm_sky': {'scripts':len(storm_scripts),'source_atlases':len(storm_manifest['monsters']),'transform_keyframes':sum(len(a['frames']) for row in storm_manifest['monsters'] for a in row['animations'].values())},
        'external_dependencies': 0,
        'galaxy_only_style': 'Disable the browser native selection-button tap flash; packaging does not edit source files.',
    }


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))

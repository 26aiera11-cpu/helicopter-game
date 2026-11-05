"""Package the current standalone HTML as one standard, verified ZIP entry."""
import hashlib
import json
import stat
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def package():
    html=ROOT/'dist/heli_trio_galaxy_test.html'
    output=html.with_suffix('.zip')
    payload=html.read_bytes()
    assert b"button.id = 'fullscreenToggle'" in payload, 'Build the current fullscreen-enabled HTML first'
    assert b"dialog.id = 'gameExitDialog'" in payload, 'Build the current in-page exit dialog first'
    assert b"if(!confirm(" not in payload, 'Native exit confirmation must not be packaged'
    assert b'id="selectionBgm"' in payload and b'src="data:audio/mpeg;base64,' in payload, 'Embed the supplied selection MP3 before packaging'
    assert b'id="galaxy-score-js"' in payload and b'heliTrio.top10.v1' in payload, 'Include the current local TOP 10 implementation'
    assert b'id="galaxy-item-monster-js"' in payload and b'id="itemMonsterAtlas" src="data:image/png;base64,' in payload, 'Embed independent item monster code and supplied atlas'
    assert b'id="galaxy-controls-js"' in payload and b'id="rotationJoystick"' in payload, 'Embed current analog controls'
    assert b'id="galaxy-worlds-js"' in payload and b'world-2:snowfield' in payload and b'heliTrio.world2Trial.top10.v1' in payload, 'Include opt-in snowfield routing and isolated trial records'
    assert b'id="galaxy-snowfield-js"' in payload and b'id="snowfieldManifest"' in payload and b'blizzard_king' in payload, 'Include the approved snowfield atlas renderer and original manifest'
    assert b'id="galaxy-volcano-js"' in payload and b'id="volcanoManifest"' in payload and b'world-2:volcano' in payload and b'magma_dragon' in payload, 'Include the volcano region and individual-frame renderer'
    assert b'id="galaxy-volcano-combat-js"' in payload and b'gameVolcanoCombat' in payload, 'Include volcano normal combat'
    assert b'id="galaxy-volcano-boss-js"' in payload and b'gameVolcanoBoss' in payload and b'breathDuration' in payload, 'Include volcano dragon patterns/rotation'
    assert b'id="galaxy-snow-combat-js"' in payload and b'penguin_raider' in payload, 'Include first-trial snowfield normal combat'
    assert b'id="galaxy-snow-boss-js"' in payload and b'gameSnowfieldBoss' in payload, 'Include snow boss patterns'
    assert b'id="galaxy-snow-spawns-js"' in payload and b'gameSnowfieldSpawns' in payload, 'Include independently weighted snow species'
    assert b'developerStartToggle' in payload and b'developerTest' in payload, "Include the developer region start and disabled-recording guard"
    assert b'id="left"' not in payload and b'id="right"' not in payload, 'Do not package retired rotation buttons'
    assert b'id="galaxy-difficulty-js"' in payload and b'gameRegionDifficulty' in payload, 'Include current regional tuning'
    assert "const names = ['뾰코', '빙글', '탱코'];".encode() in payload and 'aria-label="뾰코 선택:'.encode() in payload, 'Include the canonical ID0 display name'
    assert b'.select-screen::before' in payload and b'clip-path:polygon(37% 2.4%,41.8% 2.4%,41.8% 11.2%,37% 11.2%)' in payload, 'Include the local title-vowel correction'
    info=zipfile.ZipInfo.from_file(html,arcname=html.name)
    info.compress_type=zipfile.ZIP_DEFLATED
    info.external_attr=(stat.S_IFREG|0o644)<<16
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        archive.writestr(info,payload,compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist()==[html.name] and archive.testzip() is None
        assert archive.read(html.name)==payload
    assert html.read_bytes()==payload
    return {'archive':str(output.relative_to(ROOT)),'archive_bytes':output.stat().st_size,
            'archive_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'entries':[html.name],'entry_count':1,'html_bytes':len(payload),
            'html_sha256':hashlib.sha256(payload).hexdigest(),'compression':'ZIP DEFLATE',
            'encrypted':False,'crc_check':'passed','extracted_html_byte_equality':'passed','volcano_art_included':True,'volcano_normal_combat_included':True,'volcano_boss_combat_included':True,
            'html_unchanged_by_packaging':True,'fullscreen_control_included':True,
            'in_page_exit_dialog_included':True,'selection_bgm_embedded':True,'local_top10_included':True,'independent_item_monsters_included':True,'analog_rotation_controls_included':True,'developer_region_start_included':True,'snowfield_normal_combat_included':True,'snowfield_boss_patterns_included':True,'snowfield_mixed_spawns_included':True,'regional_difficulty_included':True,'ppyoko_name_included':True,'corrected_hel_title_included':True,'approved_snowfield_art_included':True,'opt_in_world2_included':True,'native_exit_confirm_absent':True}


if __name__=='__main__':
    print(json.dumps(package(),ensure_ascii=False,indent=2))

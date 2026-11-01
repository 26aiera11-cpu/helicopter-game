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
            'encrypted':False,'crc_check':'passed','extracted_html_byte_equality':'passed',
            'html_unchanged_by_packaging':True,'fullscreen_control_included':True}


if __name__=='__main__':
    print(json.dumps(package(),ensure_ascii=False,indent=2))

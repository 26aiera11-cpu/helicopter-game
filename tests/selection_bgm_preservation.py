"""Permit only reviewed music routing changes and the supplied unmodified MP3."""
from pathlib import Path
import json,hashlib
BGM_ASSET='assets/audio/heli_trio_selection_bgm_track2.mp3'
BGM_SHA256='ca7e760a474db29eed29f0e0f6e34406d0415f0143aa3075953e98096ff8ba53'


def assert_selection_bgm_asset():
    data=(Path(__file__).resolve().parents[1]/BGM_ASSET).read_bytes()
    assert len(data)==990740 and hashlib.sha256(data).hexdigest()==BGM_SHA256
    return data


def without_selection_bgm_changes(source):
    for old,new in reversed(json.loads(Path(__file__).with_name('selection_bgm_changes.json').read_text())):
        assert source.count(new)==1,new[:100]
        source=source.replace(new,old,1)
    return source

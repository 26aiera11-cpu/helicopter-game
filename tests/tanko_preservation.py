"""Permit only the supplied Tanko PNG replacement, never a renderer change."""
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TANKO_ASSET = 'assets/gameplay/tanko_gameplay_cannon_restored.png'
TANKO_SHA256 = '77c71f6efe44020e6fcaa04888f0cc1758d49fbed3f315f47638ac591e413db2'
TANKO_BACKUP = 'backups/tanko-gameplay.before-cannon-restoration.png'
TANKO_OLD_SHA256 = 'f541a1141d440e12e1812cb3bd782e751efe082071dce730a2cdeebc00870747'


def assert_tanko_asset():
    data = (ROOT / TANKO_ASSET).read_bytes()
    assert hashlib.sha256(data).hexdigest() == TANKO_SHA256
    return data


def without_tanko_restore(source):
    new = 'data:image/png;base64,' + base64.b64encode(assert_tanko_asset()).decode()
    data = (ROOT / TANKO_BACKUP).read_bytes()
    assert hashlib.sha256(data).hexdigest() == TANKO_OLD_SHA256
    old = 'data:image/png;base64,' + base64.b64encode(data).decode()
    assert source.count(new) == 1
    return source.replace(new, old, 1)

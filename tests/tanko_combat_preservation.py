"""Reverse only the reviewed Tanko combat deltas for historical byte assertions."""
import json
from pathlib import Path


def without_tanko_cadence_changes(source):
    for old,new in reversed(json.loads(Path(__file__).with_name('tanko_cadence_changes.json').read_text())):
        assert source.count(new)==1,new[:90]
        source=source.replace(new,old,1)
    return source


def without_tanko_interception_changes(source):
    source=without_tanko_cadence_changes(source)
    for old,new in reversed(json.loads(Path(__file__).with_name('tanko_interception_changes.json').read_text())):
        assert source.count(new)==1,new[:90]
        source=source.replace(new,old,1)
    return source


def without_tanko_combat_changes(source):
    source=without_tanko_interception_changes(source)
    for old,new in reversed(json.loads(Path(__file__).with_name('tanko_combat_changes.json').read_text())):
        assert source.count(new)==1,new[:90]
        source=source.replace(new,old,1)
    return source

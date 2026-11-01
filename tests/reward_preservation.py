"""Allow the boss-reward addition while preserving every other source byte."""
import re


def without_boss_reward_changes(source):
    marker = r'\n// Automatic boss reward; regular item drops and pickups stay unchanged\.\nfunction grantBossReward\(defeatedBoss\)\{.*?\n\}\n(?=const tactics=)'
    source, count = re.subn(marker, '\n', source, flags=re.S)
    assert count == 1, 'Expected exactly one isolated automatic reward function'
    new = 'grantBossReward(boss);boss=null;score+=10;nextPhase();break'
    old = 'dropItem(boss.x,boss.y,true);boss=null;score+=10;nextPhase();break'
    assert source.count(new) == 1
    return source.replace(new, old, 1)


def without_reward_notice(source, name):
    markers = {
        'assets/selection/selection.js': '\n/* Boss reward notice only; gameplay owns reward selection and application. */',
        'assets/selection/selection.css': '/* Compact boss reward notice. */',
    }
    marker = markers.get(name)
    if marker is None:
        return source
    assert source.count(marker) == 1
    return source[:source.index(marker)]

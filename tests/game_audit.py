"""Controlled functional audit, without changing product game code.

python tests/game_audit.py --artifacts /absolute/path/to/review
"""
import argparse
import json
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
report = {'passed': [], 'blocking_findings': [], 'nonblocking_findings': [],
          'limits': ['Controlled automated game-state/input checks, not a manual difficulty/balance playthrough.',
                     'Physical Galaxy/Samsung Internet, sensors and audible output require device checks.']}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width':1280,'height':720})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        page.evaluate('''() => {
            window.auditReset = (type=0) => {
                start(type); spawn=999;transition=0;invuln=999;fireCooldown=0;
                keys.left=keys.right=keys.fire=false;tilt={x:0,y:0};
            };
            window.auditEnemy = (x,y,hp=1,special=false) => ({x,y,hp,special,r:16,
                life:999,turn:999,kind:0,speed:0,shot:999,t:0,mode:'chase',charge:999,vx:0,vy:0});
            window.auditItem = type => ({x:player.x,y:player.y,type,life:16,r:13,t:0,vx:0,vy:0,turn:999});
        }''')

        weapons = page.evaluate('''() => {
            const values=[];
            for(let type=0;type<3;type++) for(let level=0;level<=5;level++) {
                auditReset(type);player.upgrade=level;shoot();
                values.push({type,level,count:bullets.length,homing:bullets.filter(b=>b.homing).length,
                    damage:bullets[0].damage,pierce:bullets[0].pierce,speed:bullets[0].speed});
            }
            return values;
        }''')
        for value in weapons:
            t,u=value['type'],value['level']
            assert value['count'] == ([1,2,3,4,5,5][u] if t==0 else (1 if u<2 else 3) if t==1 else (1 if u<2 else 2))
            assert value['homing'] == ([0,0,0,1,2,3][u] if t==1 else 0)
            assert value['damage'] == (2 if t==2 else 1)
            assert value['speed'] == [535,480,410][t]
            assert value['pierce'] == ([2,3,3,5,6,7][u] if t==2 else (2 if t==0 and u==5 else 1))
        report['weapon_matrix']=weapons
        passed('All three helicopters and upgrade levels 0–5 produce the expected shot counts, damage, speed, homing and piercing configuration.')

        fire = page.evaluate('''() => {
            const original=shoot;let count=0;shoot=()=>{count++;original()};const values=[];
            try {for(let type=0;type<3;type++) {
                const pair=[];
                for(const level of [0,1]) {auditReset(type);player.upgrade=level;count=0;keys.fire=true;
                    for(let i=0;i<100;i++)update(.01);pair.push(count);}
                values.push(pair);
            }} finally {shoot=original;keys.fire=false;}
            return values;
        }''')
        assert fire[0][0]>fire[1][0]>fire[2][0] and all(up>base for base,up in fire)
        report['shots_per_controlled_second']=fire
        passed('Continuous-fire timing preserves Trio/Bingle/Tanko rate ordering and first-upgrade fire-rate increase.')

        collision = page.evaluate('''() => {
            auditReset(2);enemies=[auditEnemy(100,100),auditEnemy(100,100),auditEnemy(100,100)];
            shoot();Object.assign(bullets[0],{x:100,y:100,vx:0,vy:0});update(.001);
            const pierced={kills:phaseKills,score,enemies:enemies.length};
            const narrow=bulletHitsCircle({kind:2,x:0,y:0,vx:1,vy:0,upgrade:0},0,15,1);
            const wide=bulletHitsCircle({kind:2,x:0,y:0,vx:1,vy:0,upgrade:5},0,15,1);
            auditReset(1);player.upgrade=3;enemies=[auditEnemy(player.x+100,player.y-100,20)];shoot();
            const homing=bullets.find(b=>b.homing);update(.04);
            return {pierced,narrow,wide,homingTurn:homing.vx>0};
        }''')
        assert collision['pierced']=={'kills':2,'score':2,'enemies':1}
        assert not collision['narrow'] and collision['wide'] and collision['homingTurn']
        passed('Actual collision updates support Tanko piercing, upgraded projectile width and Bingle homing turns.')

        patterns = page.evaluate('''() => {
            const values=[];
            for(let index=0;index<4;index++) {
                auditReset(0);stage=index;phase=5;
                boss={x:W/2,y:90,r:48,hp:20+15*index,maxHp:20+15*index,t:0,shot:0};
                update(.001);values.push({stage:index,count:enemyBullets.length,
                    speed:Math.hypot(enemyBullets[0].vx,enemyBullets[0].vy)});
            }return values;
        }''')
        for value, count, speed in zip(patterns,[1,3,3,5],[117,142,162,187]):
            assert value['count']==count and abs(value['speed']-speed)<.001
        report['boss_projectile_patterns']=patterns
        passed('The four bosses emit their original one/three/three/five-shot patterns with the configured stage/phase projectile speeds.')

        items = page.evaluate('''() => {
            auditReset(0);hp=1;items=[auditItem('hp')];update(.001);const healed=hp;
            items=[auditItem('hp')];update(.001);const capped=hp;
            player.upgrade=4;items=[auditItem('power')];update(.001);
            items=[auditItem('power')];update(.001);const upgrade=player.upgrade;
            auditReset(0);enemies=[auditEnemy(100,100,1,true)];shoot();
            Object.assign(bullets[0],{x:100,y:100,vx:0,vy:0});update(.001);
            return {healed,capped,upgrade,specialDrop:items.length,specialScore:score,particles:particles.length};
        }''')
        assert items=={'healed':3,'capped':4,'upgrade':5,'specialDrop':1,'specialScore':1,'particles':9}
        passed('Health pickups heal by two and respect max HP; upgrades cap at five; special-enemy destruction scores, drops an item and emits particles.')

        damage = page.evaluate('''() => {
            auditReset(0);invuln=0;
            const incoming=()=>({x:player.x,y:player.y,vx:0,vy:0,life:3.4,r:5});
            enemyBullets=[incoming()];update(.001);const first=hp;
            enemyBullets=[incoming()];update(.001);const protectedHP=hp;
            invuln=0;enemies=[auditEnemy(player.x,player.y,10)];update(.001);const body=hp;
            enemies=[];hp=1;invuln=0;enemyBullets=[incoming()];update(.001);
            return {first,protectedHP,body,gameOver:!started,menuVisible:!menu.classList.contains('hidden'),audioFlag:window.gameAudioStarted};
        }''')
        assert damage['first']==3 and damage['protectedHP']==3 and damage['body']==2
        assert damage['gameOver'] and damage['menuVisible']
        expect(page.locator('#selectionResult')).to_contain_text('게임 오버')
        passed('Enemy bullet/body damage and invulnerability work; zero health returns to the selection screen and displays the score.')
        if damage['audioFlag']:
            report['nonblocking_findings'].append({'id':'N1','issue':'Game-over path leaves gameAudioStarted true and does not pause the soundtrack.','status':'existing, not changed','blocks_progress':False})

        progression = page.evaluate('''() => {
            auditReset(0);const waves=[];let safety=0;
            while(started&&safety++<25) {
                const before={stage,phase};transition=0;spawn=999;
                for(let kill=0;kill<6;kill++) {
                    warnEnemy();warnings[warnings.length-1].special=false;
                    for(let frame=0;frame<36;frame++)update(.04);
                    const target=enemies[0];if(!target)throw Error('Warning did not produce an enemy');
                    let shots=0;
                    while(target.hp>0&&shots++<5) {
                        bullets=[];shoot();Object.assign(bullets[0],{x:target.x,y:target.y,vx:0,vy:0});update(.001);
                    }
                    if(target.hp>0)throw Error('Enemy could not be destroyed');
                }
                let bossDefeated=false;
                if(before.phase===5) {
                    update(.001);if(!boss)throw Error('Boss did not spawn');transition=0;
                    let shots=0;
                    while(boss&&shots++<80) {
                        bullets=[];shoot();Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(.001);
                    }
                    if(boss)throw Error('Boss could not be defeated');bossDefeated=true;
                }
                waves.push({...before,bossDefeated});
                if(started&&stage===before.stage&&phase===before.phase)throw Error('Stage progression stalled');
            }
            draw();return {waves,score,started,stage,phase,message:menu.querySelector('h1').textContent};
        }''')
        assert len(progression['waves'])==20 and sum(w['bossDefeated'] for w in progression['waves'])==4
        assert progression['score']==160 and not progression['started'] and '모든 지역 클리어' in progression['message']
        report['controlled_progression']=progression
        passed('All 20 waves and four bosses clear through real warning/spawn, shooting/collision and update-driven transitions; score reaches 160 without a progression blocker.')

        reward = page.evaluate('''() => {
            auditReset(0);phase=5;phaseKills=requiredKills;
            boss={x:100,y:100,r:48,hp:1,maxHp:20,t:0,shot:999};
            const original=dropItem;let requested=0;dropItem=(...args)=>{requested++;return original(...args)};
            try {shoot();Object.assign(bullets[0],{x:100,y:100,vx:0,vy:0});update(.001);}
            finally {dropItem=original;}
            return {requested,remaining:items.length,nextStage:stage,nextPhase:phase};
        }''')
        assert reward['requested']==1 and reward['remaining']==0 and reward['nextStage']==1
        report['nonblocking_findings'].append({'id':'N2','issue':'Boss reward is created then cleared by nextPhase before collection.','status':'existing, not changed','blocks_progress':False})
        passed('Existing boss-reward disappearance reproduced and classified as nonblocking; next-stage entry still succeeds.')

        sensors = page.evaluate('''() => {
            auditReset(0);sensorOn=true;neutral=null;applyTilt(10,20,'방향');const neutralTilt={...tilt};
            applyTilt(27,20,'방향');const magnitude=Math.hypot(tilt.x,tilt.y);
            document.querySelector('#sensor').click();const reset={...tilt};sensorOn=false;
            return {neutralTilt,magnitude,reset};
        }''')
        assert sensors['neutralTilt']=={'x':0,'y':0} and abs(sensors['magnitude']-1)<.001 and sensors['reset']=={'x':0,'y':0}
        passed('Synthetic sensor samples calibrate a neutral point, clamp motion and reset; physical sensor permission remains untested.')
        page.evaluate('auditReset(0)')
        assert page.evaluate('stage===0&&phase===1&&score===0&&hp===4&&player.upgrade===0')
        passed('Restart after defeat/clear resets stage, score, health and weapon upgrades.')
        assert not errors, errors
        passed('No uncaught JavaScript errors in the controlled full-function audit.')
        browser.close()
finally:
    server.shutdown()
    server.server_close()

(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

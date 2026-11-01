"""Isolate the final Trio PNG and its aspect-preserving draw rectangle."""
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL_TRIO_ASSET = 'assets/gameplay/trio_gameplay_final.png'
FINAL_TRIO_SHA256 = 'b7bdc4d0a393e46436b214fda435e288c48f147c0272d85cc93658dd811f983e'
OLD_TRIO_DRAW = 'ctx.drawImage(sprites[player.type],-16.33,-16.33,32.67,32.67);'
FINAL_TRIO_DRAW = '''{
 const body=sprites[player.type];
 if(player.type===0){
  // Preserve the complete PNG ratio; center the visible body without cropping.
  const height=33.75,width=height*body.naturalWidth/body.naturalHeight;
  ctx.drawImage(body,-width/2,-height*547.5/1122,width,height);
 }else ctx.drawImage(body,-16.33,-16.33,32.67,32.67);
}'''


def assert_final_trio_asset():
    data = (ROOT / FINAL_TRIO_ASSET).read_bytes()
    assert hashlib.sha256(data).hexdigest() == FINAL_TRIO_SHA256
    return data


def without_final_trio_changes(source):
    data = assert_final_trio_asset()
    final = 'data:image/png;base64,' + base64.b64encode(data).decode()
    previous = 'data:image/png;base64,' + base64.b64encode((ROOT / 'assets/gameplay/trio-body-pointed.png').read_bytes()).decode()
    assert source.count(final) == 1 and source.count(FINAL_TRIO_DRAW) == 1
    return source.replace(final, previous, 1).replace(FINAL_TRIO_DRAW, OLD_TRIO_DRAW, 1)

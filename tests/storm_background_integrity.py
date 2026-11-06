"""Decode integrity of the supplied PNG; never repair/re-encode or invent pixels."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def inspect_source():
    path=ROOT/'assets/storm_sky/storm_sky_background_1920x864.png';data=path.read_bytes();issues=[];offset=8;payload=[];iend=False;header=None
    if data[:8]!=b'\x89PNG\r\n\x1a\n':issues.append('Invalid PNG signature')
    while offset+8<=len(data):
        n=int.from_bytes(data[offset:offset+4],'big');tag=data[offset+4:offset+8];body=data[offset+8:offset+8+n]
        if tag==b'IHDR' and len(body)==13:header=struct.unpack('>IIBBBBB',body)
        if tag==b'IDAT':payload.append(body)
        if offset+12+n>len(data):issues.append('Truncated '+tag.decode('ascii','replace')+' chunk: payload or CRC is missing');break
        crc=int.from_bytes(data[offset+8+n:offset+12+n],'big')
        if zlib.crc32(tag+body)&0xffffffff!=crc:issues.append('CRC mismatch: '+tag.decode('ascii','replace'))
        if tag==b'IEND':iend=True;break
        offset+=12+n
    if not iend:issues.append('PNG IEND is missing')
    decoder=zlib.decompressobj();decoded=b''
    try:decoded=decoder.decompress(b''.join(payload))
    except zlib.error as e:issues.append('Invalid image deflate stream: '+str(e))
    if not decoder.eof:issues.append('Image deflate stream ended before the full raster was stored')
    channels={0:1,2:3,3:1,4:2,6:4};expected=None;rows=None
    if header:
        w,h,depth,color,compression,filtering,interlace=header
        if interlace==0 and color in channels:
            row_bytes=(w*depth*channels[color]+7)//8+1;expected=row_bytes*h;rows=len(decoded)//row_bytes
            if len(decoded)!=expected:issues.append(f'Incomplete decoded raster: {len(decoded)} of {expected} bytes')
    try:
        with Image.open(path) as im:im.load()
    except (OSError,ValueError,SyntaxError) as e:issues.append('Full Pillow decoding failed: '+str(e))
    return {'path':str(path.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'dimensions':list(header[:2]) if header else None,'decoded_complete_rows':rows,'decoded_bytes':len(decoded),'expected_decoded_bytes':expected,'zlib_stream_complete':decoder.eof,'png_iend_present':iend,'complete':not issues,'issues':issues,'policy':'The original PNG stays byte-identical. No partial-load flag, reconstruction, regeneration or replacement was used.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True);result=inspect_source();report={'passed':['Original PNG has a complete valid raster'] if result['complete'] else [],'failed':[] if result['complete'] else ['Supplied source PNG is truncated; a complete original is required'],'source_png':result,'all_passed':result['complete']};(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(('PASS:' if result['complete'] else 'FAIL:')+' '+('PNG integrity' if result['complete'] else report['failed'][0]));raise SystemExit(0 if result['complete'] else 1)

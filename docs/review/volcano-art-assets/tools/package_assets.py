"""Deterministic graphics-only ZIP, exact extraction/hash/reference checks."""
from pathlib import Path
import hashlib
import io
import json
import tempfile
import zipfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[4]
REVIEW=ROOT/'docs/review/volcano-art-assets'
ASSET=ROOT/'assets/volcano'


def main():
    destination=REVIEW/'volcano-art-assets-review-v1.zip'
    paths=sorted([p for p in ASSET.rglob('*') if p.is_file()]+[p for p in (REVIEW/'references').rglob('*') if p.is_file()])
    payload={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    payload['README_VOLCANO_REVIEW.md']=('''# 화산 그래픽 검토팩 v1

이 ZIP은 게임이 아니라 그래픽 자산/참조 자료입니다. 새 리소스의 최종 외형 승인은 아직 받지 않았고 게임에는 연결하지 않았습니다.

- assets/volcano: 배경1920x864, 배경 생성원본, 투명기본PNG5개, 아틀라스5개, 총69프레임의 매니페스트와 사용 규약.
- docs/review/volcano-art-assets/references: 제공된 디자인 참조4개, 원본 바이트 보존.
- 매니페스트의 경로는 assets/volcano를 기준으로 해석합니다. rect_px와 sprite_source_rect_px를 사용하고 행/열 곱셈으로 읽지 마세요.
- PNG는 실제RGBA이며 알파1~7의 미세 원본 잔여 픽셀은 보존됩니다. 표시 윤곽/여백 검사는 알파8 이상 기준입니다.
- PNG/프레임 검증은 완료했지만 전용손그림/8방향시트 또는 게임통합/실기기전투 검증을 뜻하지 않습니다.
- 기존 게임/갤럭시 HTML/ZIP은 이 팩에 포함하지 않았습니다. 헬기 비교 뷰어는 전체 저장소에서 실행합니다.
- 자산 설명의 보고서 링크는 아래 저장소의 전체 검토 자료를 가리킵니다.

검토 보고서와 화면:
https://github.com/26aiera11-cpu/helicopter-game/blob/feature/volcano-art-assets/docs/review/volcano-art-assets/README.md

main 병합/Pages 배포/화산 전투 개발은 하지 않았습니다.
''').encode()
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(payload.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,11,4,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,data,compresslevel=9)
    with zipfile.ZipFile(destination) as archive,tempfile.TemporaryDirectory(prefix='volcano-verify-') as tmp:
        assert archive.testzip() is None
        assert sorted(archive.namelist())==sorted(payload)
        for name in archive.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert archive.read(name)==payload[name]
            if name.endswith('.png'):Image.open(io.BytesIO(archive.read(name))).verify()
        archive.extractall(tmp)
        assert all((Path(tmp)/name).read_bytes()==data for name,data in payload.items())
        manifest=json.loads((Path(tmp)/'assets/volcano/asset_manifest.json').read_text())
        a=Path(tmp)/'assets/volcano'
        for ref in manifest['references']:
            assert hashlib.sha256((a/ref['path']).resolve().read_bytes()).hexdigest()==ref['sha256']
        for actor in manifest['monsters']:
            for field in ['base','atlas']:
                assert hashlib.sha256((a/actor[field]).read_bytes()).hexdigest()==actor[field+'_sha256']
        for path,hash_key in [('path','sha256'),('source','source_sha256')]:
            assert hashlib.sha256((a/manifest['background'][path]).read_bytes()).hexdigest()==manifest['background'][hash_key]
    report={'passed':True,'path':str(destination.relative_to(ROOT)),'bytes':destination.stat().st_size,
            'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'entries':len(payload),
            'checks':['ZIP CRC','safe paths','all entries exact bytes','PNG decode after ZIP read','separate extraction exact bytes','all manifest resource/reference hashes resolve after extraction'],
            'contains_game_html':False,'contains_existing_game_changes':False,
            'files':[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sorted(payload.items())]}
    (REVIEW/'package-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','bytes','sha256','entries']}))


if __name__=='__main__':
    main()

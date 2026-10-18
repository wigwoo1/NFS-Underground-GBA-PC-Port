import sys,json,hashlib,ctypes as C
from pathlib import Path
from types import SimpleNamespace
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'captured_setup','exec'))
from owned_sky_boundary import SceneSky
from owned_sky_frame import attach_sky as baseline
from owned_sky_frame_reuse_candidate import attach_sky as candidate
results=[]
for frame,scene in zip(frames,scenes):
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundary=SkyBoundary(record['epoch'],record['copy_refresh'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136])
 asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);sky=SceneSky(boundary,record['serial'],record['begin'],record['end'],asset)
 attached=SimpleNamespace(sky=sky,graph=scene.graph,identity=scene.identity)
 expected=baseline(frame,attached);actual=candidate(frame,attached);assert actual==expected
 assert candidate(actual,attached) is actual
 bad=bytearray(actual);import struct;header=struct.unpack_from('<6I2Q',bad);start=40+header[2]+header[3]+10560;bad[start]^=1
 try:candidate(bytes(bad),attached)
 except ValueError:pass
 else:raise AssertionError('Conflicting sky accepted')
 copied=C.string_at(C.create_string_buffer(frame),len(frame));assert candidate(copied,attached)==actual
 results.append(dict(bytes=len(frame),initial_reused=actual is frame,verified_reused=True,sha256=hashlib.sha256(actual).hexdigest()))
out=dict(result='PASS_CAPTURED_SKY_ATTACHMENT_REUSE',samples=results,scope='Actual captured scene attachment bytes and conflict guards; repeated verified immutable sky reuses frame, no live cadence proof.')
Path('work/camera/prototype-runs/sky-attachment-reuse-20261008.json').write_text(json.dumps(out,indent=2));print(out)

import runpy,struct,json
from pathlib import Path
from types import SimpleNamespace as NS
from owned_sky_frame import attach_sky
s=runpy.run_path('work/camera/test_completed_sky_candidate.py');sky=s['owned_assets'][0];boundary=sky.boundary
frame=bytearray(Path('work/camera/prototype-runs/sky-rejected-sampled-frame.bin').read_bytes());h=list(struct.unpack_from('<6I2Q',frame));h[1]=sky.end+1;h[6]=boundary.epoch;h[7]=h[1]*280896;frame[:40]=struct.pack('<6I2Q',*h)
graph=NS(epoch=boundary.epoch,refresh=sky.end+1,graph=NS(refresh=sky.begin));scene=NS(sky=sky,graph=graph,identity=(graph.epoch,graph.refresh));original=bytes(frame);result=attach_sky(frame,scene);offset=40+h[2]+h[3]
assert frame==original and len(result)==len(original)
assert result[:offset+10560]==original[:offset+10560] and result[offset+25696:offset+38400+10560]==original[offset+25696:offset+38400+10560] and result[offset+38400+25696:]==original[offset+38400+25696:]
assert result[offset+10560:offset+25696]==boundary.indices and result[offset+38400+10560:offset+38400+25696]==bytes([1])*15136
assert attach_sky(result,scene)==result
negative=0
cases=[b'',original[:-1]]
for index,value in ((0,0),(1,h[1]+1),(6,h[6]+1),(7,h[7]+1),(4,0)):
 bad=bytearray(original);header=h.copy();header[index]=value;bad[:40]=struct.pack('<6I2Q',*header);cases.append(bad)
bad=bytearray(result);bad[offset+10560]^=255;cases.append(bad)
bad=bytearray(result);bad[offset+38400+10560]=2;cases.append(bad)
for bad in cases:
 before=bytes(bad)
 try:attach_sky(bad,scene)
 except ValueError:negative+=1
 else:raise AssertionError('Invalid frame accepted')
 assert bytes(bad)==before
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-frame-attachment-tests-20261006');cp.mkdir(exist_ok=True)
for name in ('owned_sky_frame.py','test_owned_sky_frame.py'):(cp/name).write_text((Path('work/camera')/name).read_text())
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',negative_checks=negative,footprint=15136,scope='Actual owned native sky bytes attached to captured frame layout with matched metadata; all outside bytes exact, input untouched, idempotent, invalid epoch/refresh/ticks/size/coverage/conflict reject'),indent=2));print('PASS sky frame attachment',negative)

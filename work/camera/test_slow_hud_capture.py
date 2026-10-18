import ctypes as C,json,struct,time,hashlib
from pathlib import Path
from types import SimpleNamespace
from owned_slow_hud_capture import SlowHudCapture
items=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-wrap-capture-20261006/captures.json').read_text());folder=Path(items[0]['folder']);frame=(folder/'frame.bin').read_bytes();arrays=[(C.c_double*(len((folder/(n+'.bin')).read_bytes())//8)).from_buffer_copy((folder/(n+'.bin')).read_bytes()) for n in ('camera','models','bounds')];value=(frame,*arrays,dict(geometry_records=len(arrays[2])//4));sky=SimpleNamespace(lower=bytearray(15136),upper=bytearray(15136),weight=.5)
capture=SlowHudCapture(limit=1);assert capture.add(dict(alpha=.5),value,sky,[0]*16)
assert not capture.add(dict(alpha=.5),value,sky,[0]*16)
before=bytes(arrays[0]);arrays[0][0]=999;sky.lower[0]=255
assert capture.records[0][1]['camera']==before and capture.records[0][1]['lower'][0]==0
small=SlowHudCapture(budget=1);assert not small.add({},value,sky,[0]*16) and not small.records and small.bytes==0
try:SlowHudCapture().add({},(b'x',*arrays,value[-1]),sky,[0]*16)
except ValueError:pass
else:raise AssertionError('Truncated frame accepted')
p=Path(capture.save(Path('work/camera/prototype-runs')/('slow-hud-component-'+str(time.time_ns()))));r=json.loads(p.read_text());assert len(r['records'])==1
for f in r['records'][0]['files'].values():
 data=Path(f['path']).read_bytes();assert len(data)==f['bytes'] and hashlib.sha256(data).hexdigest()==f['sha256']
assert not capture.records and capture.bytes==0
print('PASS exact captured frame: private arrays/sky, duplicate and budget bounds, truncated rejection, verified export and release')

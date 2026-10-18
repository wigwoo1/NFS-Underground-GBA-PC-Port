import ctypes as C,json,time,statistics,random,struct
from pathlib import Path
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/layer-hash-candidate-20261007')
libs=[]
for name in ['layer-snapshot-baseline-benchmark.dll','layer-snapshot-hash-candidate.dll']:
 d=C.CDLL(str((p/name).resolve()));d.nf_layer_snapshot_create.restype=C.c_void_p;d.nf_layer_snapshot_clone.argtypes=[C.c_void_p];d.nf_layer_snapshot_clone.restype=C.c_void_p
 for fn,args in [('destroy',[C.c_void_p]),('reset',[C.c_void_p]),('add',[C.c_void_p,C.c_void_p]),('read',[C.c_void_p,C.c_uint,C.c_void_p])]:getattr(d,'nf_layer_snapshot_'+fn).argtypes=args
 libs.append(d)
raw=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/capture-cycles-20261007/actual-storage-rows.bin').read_bytes();assert len(raw)==160*100480
rng=random.Random(134);cases={'actual':[raw[i*100480:(i+1)*100480] for i in range(160)],'max_distinct':[struct.pack('<II',1000,y)+bytes(120)+rng.randbytes(100352) for y in range(160)]};results=[]
for label,rows in cases.items():
 buffers=[C.create_string_buffer(r,len(r)) for r in rows];times=[[],[]]
 for trial in range(6):
  for index in ([0,1] if trial%2==0 else [1,0]):
   d=libs[index];s=d.nf_layer_snapshot_create();clone=None;out=C.create_string_buffer(100480)
   try:
    begin=time.perf_counter_ns()
    for b in buffers:assert d.nf_layer_snapshot_add(s,b)
    times[index].append((time.perf_counter_ns()-begin)/1e6)
    for y,r in enumerate(rows):assert d.nf_layer_snapshot_read(s,y,out) and out.raw==r
    clone=d.nf_layer_snapshot_clone(s);assert clone and d.nf_layer_snapshot_reset(s)
    assert not d.nf_layer_snapshot_read(s,0,out)
    for y,r in enumerate(rows):assert d.nf_layer_snapshot_read(clone,y,out) and out.raw==r
    for b in buffers:assert d.nf_layer_snapshot_add(s,b)
    for y,r in enumerate(rows):assert d.nf_layer_snapshot_read(s,y,out) and out.raw==r
   finally:
    if clone:d.nf_layer_snapshot_destroy(clone)
    d.nf_layer_snapshot_destroy(s)
 results.append(dict(case=label,times_ms=times,baseline_median_ms=statistics.median(times[0]),candidate_median_ms=statistics.median(times[1])))
(cp/'matched-storage-benchmark.json').write_text(json.dumps(dict(result='PASS',cases=results,scope='Alternating six trials identical actual160rowcapture and4000page synthetic input. Complete reconstruction/clone after original reset/rebuild exact; component costs only, not live60fps performance'),indent=2));print(json.dumps(results,indent=2))

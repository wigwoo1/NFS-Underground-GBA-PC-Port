import ctypes as C,struct,json,statistics
from pathlib import Path
raw=Path('work/camera/motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];rows=[]
for name in ('owned-frame-handoff.dll','owned-handoff-copy-candidate.dll'):
 d=C.CDLL(str(Path('work/camera',name).resolve()));P=C.c_void_p;Z=C.c_size_t;U=C.c_uint64;d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_pop.argtypes=[P,P];d.nf_owned_handoff_pop.restype=P;d.nf_owned_frame_free.argtypes=[P];d.nf_owned_handoff_destroy.argtypes=[P]
 candidate='candidate' in name;fn=d.nf_owned_handoff_push_stages if candidate else d.nf_owned_handoff_push_timed;fn.argtypes=[P,P,Z,P];q=d.nf_owned_handoff_create(epoch)
 try:
  for i in range(100):
   t=(U*(8 if candidate else 4))();assert fn(q,raw,len(raw),t)==1;n=Z();p=d.nf_owned_handoff_pop(q,C.byref(n));assert p and C.string_at(p,n.value)==raw;d.nf_owned_frame_free(p)
   if candidate:assert t[6]>0 and t[5]>=sum(t[:5]);hold=t[4]*1000/t[6];total=t[5]*1000/t[6];copy=t[2]*1000/t[6]
   else:hold=t[1]*1000/t[3];total=t[2]*1000/t[3];copy=None
   rows.append(dict(renderer=name,hold_ms=hold,total_ms=total,copy_ms=copy))
 finally:d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_COMPLETE_FRAME_STAGE_TIMING',packet_bytes=len(raw),scope='Sequential component copies and exact full-packet checks; not live contention or60fps evidence',medians={name:{k:statistics.median(r[k] for r in rows if r['renderer']==name) for k in ('hold_ms','total_ms')} for name in {r['renderer'] for r in rows}},rows=rows)
Path('work/camera/handoff-copy-stage-benchmark.json').write_text(json.dumps(out,indent=2));print(out['medians'])

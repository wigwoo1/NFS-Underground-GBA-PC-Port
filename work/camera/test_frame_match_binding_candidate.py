import ctypes as C,json
from pathlib import Path
p=Path('work/camera/owned-handoff-request-authority-candidate.dll').resolve();results=[]
for loader in (C.CDLL,C.PyDLL):
 d=loader(str(p));f=d.nf_owned_frame_matches;f.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];f.restype=C.c_int
 a=C.create_string_buffer(b'a'*7328801);b=C.create_string_buffer(b'a'*7328801)
 assert f(a,7328801,b,7328801)==1
 for pos in (0,39,3664400,7328800):
  b[pos]=b'b';assert f(a,7328801,b,7328801)==0;b[pos]=b'a'
 assert f(None,7328801,b,7328801)==0 and f(a,39,b,39)==0 and f(a,7328801,b,7328800)==0
 results.append(dict(binding=loader.__name__,equal=1,mismatch_positions=[0,39,3664400,7328800],invalid_cases=3))
out=dict(result='PASS_IDENTICAL_FRAME_EQUALITY_BINDINGS',library=str(p),results=results,scope='Actual native routine7.3MB equal/mismatched/null/size cases; not scheduling benefit or playable cadence proof.');Path('work/camera/prototype-runs/frame-match-binding-component-20261010.json').write_text(json.dumps(out,indent=2));print(out['result'])

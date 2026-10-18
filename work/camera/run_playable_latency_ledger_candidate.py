import ctypes as C,runpy
from pathlib import Path
mapping={'owned-dx-source-diagnostic-bridge.dll':'owned-dx-source-latency-candidate.dll','owned-frame-handoff.dll':'owned-frame-handoff-precise-candidate.dll','owned-draw-commit-candidate.dll':'owned-draw-commit-precise-candidate.dll','owned-batch-present-candidate.dll':'owned-batch-present-precise-candidate.dll'}
root=Path('work/camera').resolve();original_cdll=C.CDLL;original_pydll=C.PyDLL
loads=[]
def mapped(name):
 p=Path(name)
 if p.parent.resolve()==root and p.name in mapping:
  replacement=str(p.with_name(mapping[p.name]));loads.append([str(p),replacement]);return replacement
 return name
C.CDLL=lambda name,*a,**k:original_cdll(mapped(name),*a,**k)
C.PyDLL=lambda name,*a,**k:original_pydll(mapped(name),*a,**k)
try:runpy.run_path('work/camera/run_playable_input_dxgi_candidate.py',run_name='__main__')
finally:
 import json,time
 Path('work/camera/prototype-runs/precise-loads-'+str(time.time_ns())+'.json').write_text(json.dumps(loads,indent=2));print('precise libraries',loads)


 d=original_cdll(str(root/'owned-dx-source-latency-candidate.dll'));d.nf_dx_display_read.argtypes=[C.c_uint,C.c_void_p];rows=[]
 for i in range(d.nf_dx_display_count()):
  row=(C.c_uint64*14)();assert d.nf_dx_display_read(i,row)==0;rows.append(list(row))
 path=Path('work/camera/prototype-runs/display-ledger-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=rows,dropped=d.nf_dx_display_dropped()),indent=2));print(path)


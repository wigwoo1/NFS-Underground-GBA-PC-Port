"""Observe actual native owner/authority library loads in current live renderer."""
import ctypes as C,runpy,json
from pathlib import Path
original=C.CDLL;loads=[]
def observed(path,*args,**kwargs):
 d=original(path,*args,**kwargs);name=Path(str(path)).name
 if 'handoff' in name or 'draw-commit' in name:loads.append(dict(requested=str(path),loaded=str(d._name)))
 return d
C.CDLL=observed
try:runpy.run_path('work/camera/run_native_sky_reader_bulk.py',run_name='__main__')
finally:
 C.CDLL=original
 out=dict(result='OBSERVED_LIVE_NATIVE_LIBRARY_LOADS',loads=loads,scope='Actual current run loads only; does not yet prove which handle allocates owner or shares owner layout. No renderer change or retirement enabled.')
 path=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/expired-slot-accounting-component-20261010/live-owner-loads.json');path.write_text(json.dumps(out,indent=2));print('OWNER_AUTHORITY_LOADS',sorted(set(Path(x['loaded']).name for x in loads)),flush=True)

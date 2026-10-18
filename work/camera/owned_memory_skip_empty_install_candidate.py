"""Explicit opt-in empty-extension elimination, retaining current memory API."""
import os
from pathlib import Path
assert os.environ.get('NFSUG_MEMORY_SKIP_EMPTY_EXTEND')=='1'
import owned_closed_scene_memory as memory
from owned_closed_scene_bulk_candidate import ClosedSceneMemory as Candidate
baseline=Path(memory.__file__).read_text();expected=baseline.replace('    old.extend(data[max(0,skip):])','    if skip<len(data):old.extend(data[max(0,skip):])')
assert expected==Path(__file__).with_name('owned_closed_scene_bulk_candidate.py').read_text()
memory.ClosedSceneMemory=Candidate
memory._scene_memory_local.entries=[]

stats=dict(constructions=0)
original=Candidate.__init__
def constructed(self,*args,**kwargs):
 result=original(self,*args,**kwargs);stats['constructions']+=1;return result
Candidate.__init__=constructed

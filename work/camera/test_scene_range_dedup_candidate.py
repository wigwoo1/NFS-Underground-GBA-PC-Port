import sys,json,struct,types
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'savedscene','exec'))
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_scene_range_dedup_candidate import ClosedSceneMemory as Candidate
checks=0;hits=[]
try:
 for scene in scenes:
  a=Baseline(scene.graph,rom);b=Candidate(scene.graph,rom);hits.append(b.range_dedup_hits)
  assert a._ranges==b._ranges and a._starts==b._starts and a.owned_byte_count==b.owned_byte_count
  for address,data in a._ranges:
   for offset,size in [(0,len(data)),(0,1),(len(data)-1,1)]:assert a.read(address+offset,size)==b.read(address+offset,size);checks+=1
 # Duplicate exact ranges collapse; conflicting bytes at same address still reject.
 context=bytearray(368);struct.pack_into('<I',context,84,0x02000000);struct.pack_into('<I',context,80,0x02000100)
 rec=bytearray(64);struct.pack_into('<4I',rec,0,1,0,0x02001000,0);struct.pack_into('<H',rec,26,65535)
 for conflict in (False,True):
  second=bytearray(rec)
  if conflict:second[40]=1
  g=types.SimpleNamespace(context=bytes(context),geometry=bytes(rec+second),offsets=b'',materials=b'',faces=b'')
  closed=types.SimpleNamespace(graph=g)
  for cls in (Baseline,Candidate):
   try:result=cls(closed,rom)
   except ValueError:assert conflict
   else:assert not conflict
 out=dict(result='PASS_EXACT_SCENE_RANGE_DEDUP',saved_scenes=len(scenes),exact_duplicate_ranges=hits,read_checks=checks,conflicting_duplicate_rejected=True,scope='Exact sparse ranges/starts/accounting and reads for two actual snapshots plus duplicate/conflict guards; no full4K/live benefit claim.')
 Path('work/camera/prototype-runs/scene-range-dedup-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:history.close()

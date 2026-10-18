import sys,runpy,json,struct,gc,hashlib
from pathlib import Path
import owned_sampled_world_frame as assembly
from owned_segmented_frame_candidate import SegmentedFrame
owners=[]
def join(header,geometry,base,offset):
 value=SegmentedFrame.join(header,geometry,base,offset)
 assert value.tail.readonly and value.tail.obj is base
 assert value.materialize()==b''.join((header,*geometry,memoryview(base)[offset:]))
 owners.append(value)
 return value
assembly.join_frame=join
sys.argv=['verify',sys.argv[1]]
runpy.run_path('work/camera/verify_captured_source_live_replay.py',run_name='__main__')
assert len(owners)==5
gc.collect()
from owned_motion_pairs import records,_decode_records
original_materialize=SegmentedFrame.materialize
parser_checks=0
for owner in owners:
 reference=original_materialize(owner)
 for keys in (True,False):
  baseline=_decode_records(reference,source_keys=keys)
  SegmentedFrame.materialize=lambda self:(_ for _ in ()).throw(AssertionError('Parser copied retained tail'))
  try:actual=_decode_records(owner,source_keys=keys)
  finally:SegmentedFrame.materialize=original_materialize
  assert actual==baseline
  assert all(block.readonly and block.obj is owner.prefix for row in actual['records'] for block in row['blocks'])
  parser_checks+=1
 a=records(owner);b=records(owner)
 assert a==b and a is not b and a['records'] is not b['records']
checks=[]
for value in owners:
 result=value.materialize();assert len(result)==len(value)
 checks.append(dict(frame_bytes=len(value),prefix_bytes=len(value.prefix),retained_tail_bytes=len(value.tail),sha256=hashlib.sha256(result).hexdigest()))
value=owners[0];bad=bytearray(value.prefix);struct.pack_into('<I',bad,4,struct.unpack_from('<I',bad,4)[0]+1)
for args in [(bytes(bad),value.base,value.tail_offset),(value.prefix,value.base,value.tail_offset+1),(bytearray(value.prefix),value.base,value.tail_offset)]:
 try:SegmentedFrame(*args)
 except ValueError:pass
 else:raise AssertionError('Invalid segmented owner accepted')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/segmented-frame-owner-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS',parser_checks=parser_checks,checks=checks,invalid_cases=3,scope='Five complete captured source signatures through diagnostic materialization, tail retained readonly after original preparation closes. Segmented parser/anchors/masks integrated in component replay; GPU ABI integration pending; no performance or60fps claim.')
(cp/'parser-result.json').write_text(json.dumps(result,indent=2));print(result)

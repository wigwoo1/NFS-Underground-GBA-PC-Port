import json,copy
from pathlib import Path
from owned_compact_stage_storage_candidate import pack,unpack
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791557485955035200.json').read_text());records=r['preparation_retention']['slow_process_intervals']['records'];before=[];after=[]
for row in records:
 baseline=copy.deepcopy(row);encoded=json.dumps(pack(row),separators=(',',':'),allow_nan=False);decoded=unpack(json.loads(encoded));assert decoded==baseline
 before.append(len(json.dumps(row,separators=(',',':')).encode()));after.append(len(encoded.encode()));assert after[-1]<=before[-1]
 row.clear();assert decoded==baseline
for row in [{'name':'x','started_ns':4,'completed_ns':7,'wall_ns':2,'thread_cycles':1},{'name':'x','started_ns':4,'completed_ns':6,'wall_ns':2,'thread_cycles':1,'extra':{'a':[1,2]}}]:assert unpack(pack(row))==row
try:pack({'$stage_v1':[]});raise AssertionError('Reserved-key collision accepted')
except AssertionError as e:assert str(e)!='Reserved-key collision accepted'
out=dict(result='PASS_LOSSLESS_COMPLETE_RETAINED_STORAGE',records=len(records),original_max_bytes=max(before),compact_max_bytes=max(after),prior_missing_records=r['preparation_retention']['slow_process_intervals']['dropped'],scope='All available prior slow records exactly reconstructed; prior missing record cannot be recovered; live zero-drop rerun required.')
Path('work/camera/prototype-runs/compact-stage-storage-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

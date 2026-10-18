from pathlib import Path
import json,struct
from owned_motion_pairs import plan_pair
p=Path('work/camera');refs=[8758,8762,8766,8769,8773,8776,8780];frames=[(p/'motion-actual-scanline-assets'/f'{r}-native-complete-frame.bin').read_bytes() for r in refs];checks=[]
for a,b in zip(frames,frames[1:]):
 pair=plan_pair(a,b);counts={str(k):sum(pair['older']['records'][i]['kind']==k for i,j in pair['pairs']) for k in (1,2,3)}
 assert counts['3']==1,'Player source model lost identity'
 checks.append(dict(older=pair['older']['refresh'],newer=pair['newer']['refresh'],paired_by_kind=counts,held=len(pair['held']),births=len(pair['births'])))
bad=bytearray(frames[1]);struct.pack_into('<Q',bad,24,99)
try:plan_pair(frames[0],bad);raise AssertionError('Stale epoch accepted')
except ValueError:pass
try:plan_pair(frames[1],frames[0]);raise AssertionError('Reverse time accepted')
except ValueError:pass
try:plan_pair(frames[0],frames[1][:-1]);raise AssertionError('Truncation accepted')
except ValueError:pass
# Duplicate one raw source record: identity ambiguity must never pair by draw order.
from owned_motion_pairs import records
original=records(frames[0]);first=original['records'][0];record_size=16+sum(4+len(x) for x in first['blocks'])
raw=frames[0];gn=struct.unpack_from('<I',raw,8)[0];header=bytearray(raw[:40]);struct.pack_into('<I',header,8,gn+record_size)
duplicated=bytes(header)+raw[40:40+record_size]+raw[40:]
ambiguous=plan_pair(duplicated,frames[1]);assert not any(i in (0,1) for i,j in ambiguous['pairs']);assert all(ambiguous['held'][i]['reason']=='ambiguous source identity' for i in (0,1))
r=dict(result='PASS_OWNED_RAW_SOURCE_PAIRING' ,checks=checks,epoch_time_truncation_rejected=True,duplicate_identity_not_paired=True,scope='Raw source identity planner only. Visibility/topology births and held geometry need discrete policy; not interpolated GPU or60fps proof.')
(p/'owned-motion-pair-tests.json').write_text(json.dumps(r,indent=2));print(r)

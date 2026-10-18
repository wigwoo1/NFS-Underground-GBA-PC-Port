from region_block import region_block
import json
from pathlib import Path
record=[1,2,3,4,0,0,0,3,0];origin=[0,0,1,2,3,4]
def check(kinds,phases=None,foreign=None):
 commands=[[kind,0,0,0,0,0] for kind in kinds];origins=[origin[:] for _ in kinds];passes=[[0,phase,0] for phase in (phases or [0]*len(kinds))]
 if foreign is not None:origins[foreign][2]=99
 r=record[:];r[7]=len(kinds)
 return region_block(r,commands,origins,passes)
assert check([2,1,2],[0,0,1])==dict(begin=0,end=3,prefix=[0],road=[1],suffix=[2],prefix_tail=1,suffix_tail=3)
assert check([])['prefix_tail']==0
assert check([2,2],[1,1])['suffix']==[0,1]
rejected=0
for args in (([1,1],),([1,2],),([2,1],[1,0]),([3],),([2],[0],0)):
 try:check(*args)
 except ValueError:rejected+=1
assert rejected==5
report=dict(result='PASS',positive_cases=3,rejections=rejected,scope='Captured block structure only; no sampled eligibility inference.')
Path(__file__).with_name('region-block-tests.json').write_text(json.dumps(report,indent=2));print(report)

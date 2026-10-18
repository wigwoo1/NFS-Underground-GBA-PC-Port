"""Audit region runs without conflating road-separated wall passes."""
from pathlib import Path
import json,collections
p=Path('work/camera');r=json.loads((p/'texture-provenance-tests.json').read_text())
reentries=[];runs=0;walls=0
for scene in r['dispatch_samples']:
    seen={};last=None
    assert len(scene['commands'])==len(scene['origins'])
    for index,(c,o) in enumerate(zip(scene['commands'],scene['origins'])):
        if c[0]!=2:
            last=None
            continue
        walls+=1
        key=(c[4],c[3],c[5])
        assert o and len(o)==12
        if last and last[0]==key:
            assert c[2]>last[1], 'nonascending contiguous wall run'
        else:
            runs+=1
            if key in seen:
                previous=seen[key]
                between=scene['commands'][previous+1:index]
                reentries.append(dict(serial=scene['serial'],index=index,previous=previous,
                    source=c[2],previous_source=scene['commands'][previous][2],
                    intervening_kinds=[v[0] for v in between],
                    same_record=scene['origins'][previous][1:6]==o[1:6]))
        seen[key]=index;last=(key,c[2])
assert walls==3176 and runs==1652 and len(reentries)==86
same_record=sum(x['intervening_kinds']==[1] and x['same_record'] for x in reentries)
assert same_record==85
assert [x['serial'] for x in reentries if not x['same_record']]==[53]
descending=sum(x['source']<x['previous_source'] for x in reentries)
assert descending>0
passes=collections.Counter()
by_serial={s['serial']:s for s in r['dispatch_samples']}
for scene in r['dispatch_samples']:
    for c,wp in zip(scene['commands'],scene['wall_passes']):
        if c[0]!=2: assert wp is None; continue
        assert (wp[0],bool(wp[1])) in ((0x0300297c,False),(0x03002b38,True))
        passes['deferred' if wp[1] else 'first']+=1
for x in reentries:
    s=by_serial[x['serial']];a=s['wall_passes'][x['previous']];b=s['wall_passes'][x['index']]
    assert a[0]==0x0300297c
    assert b[0]==(0x03002b38 if x['same_record'] else 0x0300297c)
assert passes=={'first':2910,'deferred':266}
result=dict(result='PASS',scenes=len(r['dispatch_samples']),walls=walls,runs=runs,
    wall_pass_counts=dict(passes),
    region_reentries=len(reentries),same_record_road_separated=same_record,descending_reentries=descending,examples=reentries,
    scope='Explicit wall-entry LR/mask distinguishes first and deferred passes; all85same-record returns verified deferred. Different-record revisit is first pass. Never globally sort a region by source.')
(p/'dispatch-run-tests.json').write_text(json.dumps(result,indent=2))
print({k:v for k,v in result.items() if k!='examples'})

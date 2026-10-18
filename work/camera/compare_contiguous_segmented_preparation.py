"""Balanced-order contiguous/segmented replay of the same captured scene."""
from pathlib import Path
import sys,json,statistics
p=Path('work/camera/replay_captured_preparation_ready.py');s=p.read_text()
s=s.replace('assembly.join_frame=SegmentedFrame.join','contiguous_join=assembly.join_frame')
s=s.replace('from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples','from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples as SegmentedSamples\nfrom owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples as ContiguousSamples')
s=s.replace('for i in range(20):','for i in range(40):\n mode="contiguous" if i%4 in (0,3) else "segmented"\n assembly.join_frame=contiguous_join if mode=="contiguous" else SegmentedFrame.join\n PrecomputedSourceWorldSamples=ContiguousSamples if mode=="contiguous" else SegmentedSamples')
s=s.replace('rows.append(dict(round=i,','rows.append(dict(path=mode,round=i,')
exec(compile(s,str(p),'exec'))
out=Path(sys.argv[1]);result=json.loads(out.read_text());result['comparison']={}
for name in ('contiguous','segmented'):
 group=[x for x in result['rounds'][8:] if x['path']==name]
 result['comparison'][name]=dict(rounds=len(group),median_precompute_ms=statistics.median(x['precompute_ms'] for x in group),median_construct_ms=statistics.median(x['construct_ms'] for x in group),median_frame_join_ms=statistics.median(sum(st.get('immutable_frame_join',0) for st in x['assembly_stages_ms']) for x in group))
result['scope']+=' Balanced ABBA ordering; warm graph/fixture inputs, no independent live benefit claim.'
out.write_text(json.dumps(result,indent=2));print(json.dumps(result['comparison'],indent=2))

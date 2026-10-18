"""Attribute completed live presentation backlog; no scanout certification."""
import json,statistics,sys
from pathlib import Path
path=Path(sys.argv[1]);report=json.loads(path.read_text())
rows=[r for r in report['presentation_samples'] if r.get('interpolated')]
assert rows
origin=min(r['sample_begin_ns'] for r in rows)
def summarize(values):
 values=sorted(values)
 return dict(median=statistics.median(values),p95=values[int(.95*(len(values)-1))],maximum=max(values))
buckets=[]
for second in range(int((max(r['sample_begin_ns'] for r in rows)-origin)/1e9)+1):
 selected=[r for r in rows if second<=(r['sample_begin_ns']-origin)/1e9<second+1]
 if not selected:continue
 buckets.append(dict(second=second,count=len(selected),lateness_ms=summarize([(r['present_end_ns']-r['presentation_deadline_ns'])/1e6 for r in selected]),sample_start_lateness_ms=summarize([(r['sample_begin_ns']-r['presentation_deadline_ns'])/1e6 for r in selected]),presentation_call_ms=summarize([(r['present_end_ns']-r['present_begin_ns'])/1e6 for r in selected])))
indices=[r['display_index'] for r in rows]
result=dict(scope='CPU presentation completion; excludes scanout; buckets relative to first sampled frame',original_updates=report['original_updates'],timing=report['timing'],samples=len(rows),display_indices_contiguous=all(b==a+1 for a,b in zip(indices,indices[1:])),buckets=buckets)
output=path.with_suffix('.presentation-backlog.json');output.write_text(json.dumps(result,indent=2));print(output)
for b in buckets:print(b['second'],b['count'],round(b['lateness_ms']['median'],3),round(b['sample_start_lateness_ms']['median'],3),round(b['presentation_call_ms']['median'],3))

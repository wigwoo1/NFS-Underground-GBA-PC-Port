"""Audit committed 60Hz grid identity per pause generation from a live report."""
import json,sys,statistics
from pathlib import Path
path=Path(sys.argv[1]);report=json.loads(path.read_text());samples=[x for x in report['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented')];groups={}
for row in samples:groups.setdefault((row['epoch'],row['generation']),[]).append(row)
checks=[]
for key,rows in groups.items():
 indices=[x['display_index'] for x in rows]
 duplicates=[b for a,b in zip(indices,indices[1:]) if b<=a]
 gaps=[(a,b) for a,b in zip(indices,indices[1:]) if b!=a+1]
 nonmonotonic=sum(b['present_begin_ns']<=a['present_begin_ns'] for a,b in zip(rows,rows[1:]))
 checks.append(dict(epoch=key[0],generation=key[1],count=len(rows),duplicates=duplicates,gaps=gaps,nonmonotonic_presentations=nonmonotonic))
pauses=report['pause_events'];intervals=sorted((b['present_begin_ns']-a['present_begin_ns'])/1e6 for a,b in zip(samples,samples[1:]) if a['generation']==b['generation'] and not any(a['present_begin_ns']<=p['end_ns'] and b['present_begin_ns']>=p['begin_ns'] for p in pauses))
result=dict(report=str(path),source_result=report['result'],grid_continuity_pass=all(not c['duplicates'] and not c['gaps'] and not c['nonmonotonic_presentations'] for c in checks),generations=checks,interval_ms=dict(count=len(intervals),median=statistics.median(intervals),p95=intervals[int(.95*(len(intervals)-1))],max=max(intervals),over20=sum(x>20 for x in intervals)),scope='CPU commit timestamps and original-cycle sample grid identities only; physical scanout and fullscene visual continuity unverified')
out=path.with_suffix('.continuity.json');out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

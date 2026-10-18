"""Attribute producer submission duration using measured native lock/copy stages."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());rows=r['worker_submit_stage_samples'];keys=('space_wait_ns','snapshot_lock_ns','native_lock_acquire_ns','native_copy_locked_ns','native_push_internal_ns','native_push_ns','preparation_submit_ns','notification_ns')
assert rows
versions=sorted({x.get('native_push_timing_version',1) for x in rows});assert all(v in (1,2) for v in versions)
keys=keys+('native_eligibility_wait_ns','native_eligibility_hold_ns','native_copy_unlocked_ns','native_publish_wait_ns','native_publish_hold_ns')
summary={}
for key in keys:
 values=[x[key]/1e6 for x in rows if key in x]
 if not values:continue
 summary[key]=dict(count=len(values),median_ms=statistics.median(values),max_ms=max(values),total_ms=sum(values))
slow=sorted(rows,key=lambda x:x['submit_end_ns']-x['submit_begin_ns'],reverse=True)[:10]
out=dict(timing_versions=versions,scope='Native queue lock differs from presentation serialization lock; inclusive durations cannot be summed',stages=summary,largest_submissions=[dict(identity=x['scene_identity'],wall_ms=(x['submit_end_ns']-x['submit_begin_ns'])/1e6,**{k:(x[k]/1e6 if k in x else None) for k in keys}) for x in slow])
p.with_suffix('.producer-lock-stages.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

"""Join stall samples to authoritative preparation lifecycle timestamps."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());stalls=json.loads(Path(sys.argv[2]).read_text());samples={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')};checks=[]
for g in stalls['largest']:
 x=samples[g['display_index']];identity=[x['epoch'],x['source_older'],x['refresh']] if 'epoch' in x else None
 candidates=[q for q in r['preparation_queue_samples'] if q.get('identity') is not None and q['identity'][1:]==[x['source_older'],x['refresh']] and q.get('published_ns') is not None and q['published_ns']<=x['pair_ready_ns']]
 assert candidates
 q=max(candidates,key=lambda z:z['published_ns']);assert q['submitted_ns']<=q['enqueued_ns']<=q['dequeued_ns']<=q['started_ns']<=q['finished_ns']<=q['published_ns']<=q['taken_ns']
 checks.append(dict(display_index=g['display_index'],identity=q['identity'],generation=q['generation'],queue_wait_ms=(q['started_ns']-q['enqueued_ns'])/1e6,execution_ms=(q['finished_ns']-q['started_ns'])/1e6,publish_ms=(q['published_ns']-q['finished_ns'])/1e6,ready_lead_before_acquire_ms=(x['pair_begin_ns']-q['published_ns'])/1e6,published_to_taken_ms=(q['taken_ns']-q['published_ns'])/1e6))
out=dict(result='PASS_LIFECYCLE_JOIN',checks=checks,scope='Latest same refresh pair publication before acquire; timestamps ordered. Repeated generation candidates retained and latest selected. Wall time includes scheduling, not CPU/GPU cause or scanout proof.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(out)

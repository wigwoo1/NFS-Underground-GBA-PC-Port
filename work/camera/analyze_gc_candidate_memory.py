import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());e=r['startup_gc_scan_lease'];samples=e['memory_samples'];assert e['restored'] and e['restored_thresholds']==e['previous_thresholds'] and e['remaining_frozen_objects']==e['preexisting_frozen_objects'];assert e['sampler_stopped'] and not e['memory_errors'] and len(samples)>=100
first=samples[0]['time_ns'];bins=[]
for begin in (0,15,30,45):
 values=[s['private_bytes'] for s in samples if begin<=((s['time_ns']-first)/1e9)<begin+15]
 bins.append(dict(seconds=[begin,begin+15],samples=len(values),min_private_bytes=min(values) if values else None,max_private_bytes=max(values) if values else None,median_private_bytes=statistics.median(values) if values else None))
out=dict(result='OBSERVED_GC_CANDIDATE_MEMORY_RESTORATION',samples=len(samples),quarter_minute_private_memory=bins,peak_private_bytes=max(s['private_bytes'] for s in samples),before_final_collection=e['memory_before_final_collection'],after_final_collection=e['memory_after_final_collection'],final_collected=e['final_collected'],final_collection_ms=e['final_collection_ns']/1e6,scope='One minute process-private-memory observation, not long-run boundedness proof or matched baseline comparison. Allocator/D3D retention can remain after collection; restoration checked exactly.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

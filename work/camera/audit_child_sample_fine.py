import json,statistics
from pathlib import Path
a=json.loads(Path('prepared_hud_live_audit.json').read_text());r=json.loads(Path(a['source']).read_text())
requests=[s for s in r['world_preparation_stage_samples'] if s['terminal'][-1]['fine_trace']]
assert requests and all(9385<=s['older']<=9412 for s in requests)
stages={};worst=[]
for request in requests:
    t=request['terminal'][-1]
    assert t['sample_timings']
    for sample in t['sample_timings']:
        for stage in sample['source_sample_stages']:
            stages.setdefault(stage['name'],[]).append(stage)
            if stage['name']!='sample_publication':
                worst.append(dict(pair=[request['older'],request['newer']],alpha=sample['alpha'],stage=stage['name'],wall_ms=stage['wall_ns']/1e6,cpu_ms=stage['thread_cpu_ns']/1e6,assembly=sample['assembly_stages'] if stage['name']=='world_sample' else None))
summary={name:dict(count=len(rows),median_wall_ms=statistics.median(x['wall_ns']/1e6 for x in rows),max_wall_ms=max(x['wall_ns']/1e6 for x in rows),median_cpu_ms=statistics.median(x['thread_cpu_ns']/1e6 for x in rows)) for name,rows in stages.items()}
out=dict(source=a['source'],request_count=len(requests),stages=summary,worst=sorted(worst,key=lambda x:x['wall_ms'],reverse=True)[:8],scope='Existing fine instrumentation bounded to older source refresh9385..9412; caller stage envelopes include tracing and scheduling. Publication includes acknowledgement wait; no baseline cadence claim.')
Path('child_sample_fine_audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(dict(request_count=len(requests),stages=summary,worst=[{k:v for k,v in x.items() if k!='assembly'} for x in out['worst'][:3]])))

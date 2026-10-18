import json
from pathlib import Path
a=json.loads(Path('prepared_hud_live_audit.json').read_text())
r=json.loads(Path(a['source']).read_text())
d=r['bounded_diagnostic_stats']['whole_run_api_intervals']['compact_gap_diagnostic']
assert d['segments_dropped']==0
live=r['live_observation_stats']['whole_run_api_intervals']
segments={(s['epoch'],s['generation']):s for s in live['native_success_segments']['records']}
rows=[];excluded=0
for segment in d['segments']:
    assert len(segment['records'])<=8
    for row in segment['records']:
        epoch,generation,index=row['identity'];s=segments.get((epoch,generation))
        if s is None or not s['first_index']<index<=s['last_index']:
            excluded+=1;continue
        assert s['first_success_ns']<=row['begin_ns']<=row['end_ns']<=s['last_success_ns']
        assert row['end_ns']-row['begin_ns']==row['gap_ns']
        rows.append(row)
assert rows
rows.sort(key=lambda x:x['gap_ns'],reverse=True)
assert rows[0]['gap_ns']/1e6==a['coverage']['active_intervals']['max_ms']
out=dict(result='PASS_COMPACT_LIVE_MAXIMUM_IDENTITY',source=a['source'],cadence=a['coverage']['active_intervals'],
         records=rows,excluded_outside_live_segment=excluded,
         scope='Bounded largest-gap records match independent complete live maximum; not full threshold population or scanout proof.')
Path('compact_gap_live_audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(dict(result=out['result'],cadence=out['cadence'],worst=rows[:3],excluded=excluded)))

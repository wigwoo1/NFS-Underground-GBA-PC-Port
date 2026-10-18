"""Join complete live interval ledger to retained diagnostic identities."""
import json,re
from pathlib import Path
a=json.loads(Path('borrowed_metadata30_audit.json').read_text())
r=json.loads(Path(a['source']).read_text())
raw=Path(a['log']).read_bytes()
log=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
gc=json.loads(Path(re.search(r'PARENT_GC_TRACE (.+)',log).group(1).strip()).read_text())
assert gc['dropped']==0
d=r['bounded_diagnostic_stats']['whole_run_api_intervals']['deadline_diagnostic']
w=r['live_observation_stats']['whole_run_api_intervals']
ledger=w['all_successful_native_long_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
samples={tuple(x['identity']):x for x in d['records']}
rows=[]
for interval in sorted(ledger['records'],key=lambda x:x['interval_ns'],reverse=True):
    key=tuple(interval[k] for k in ('epoch','generation','display_index'))
    sample=samples.get(key)
    item=dict(identity=key,gap_ms=interval['interval_ns']/1e6,diagnostic_retained=sample is not None)
    if sample:
        assert sample['gap_ns']==interval['interval_ns']
        s=sample['caller_stages'];c=sample['caller_timing'];p=sample['prepared']
        spans={'preparation_take':(s['preparation_take_begin_ns'],s['preparation_take_end_ns']),
               'pair':(s['pair_begin_ns'],s['pair_ready_ns']),
               'draw':(c['draw_begin_ns'],c['draw_end_ns']),
               'present':(c['present_begin_ns'],c['present_end_ns']),
               'completion_interval':(interval['begin_ns'],interval['end_ns'])}
        item['spans']={}
        for name,(begin,end) in spans.items():
            assert begin<=end
            hits=[dict(generation=e['generation'],duration_ms=(e['end_ns']-e['start_ns'])/1e6,
                       overlap_ms=(min(end,e['end_ns'])-max(begin,e['start_ns']))/1e6)
                  for e in gc['events'] if max(begin,e['start_ns'])<min(end,e['end_ns'])]
            item['spans'][name]=dict(ms=(end-begin)/1e6,parent_gc=hits)
        item['metadata_caller_ms']=sum(x['end_ns']-x['begin_ns'] for x in p['borrowed_metadata_calls'])/1e6
    rows.append(item)
assert rows and rows[0]['gap_ms']==a['coverage']['active_intervals']['max_ms']
last=w['native_success_boundaries']['last_success_ns']
outside=[x for x in d['records'] if x['transaction']['commit'][6]>last]
out=dict(result='PASS_COMPLETE_ACTIVE_LONG_INTERVAL_JOIN',rows=rows,
         unmatched=sum(not x['diagnostic_retained'] for x in rows),
         diagnostic_after_last_live_success=len(outside),
         scope='Live long-interval ledger complete; diagnostic subset overflow remains. GC overlaps are associations. Post-live diagnostic records are excluded from this cadence population; physical scanout and sustained60 unverified.')
Path('metadata_active_stalls.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
for row in rows[:3]:print(json.dumps(row))

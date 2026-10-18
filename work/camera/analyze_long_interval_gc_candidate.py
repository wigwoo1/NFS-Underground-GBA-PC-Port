import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['gc_trace_dropped']==0
api=r['bounded_diagnostic_stats']['whole_run_api_intervals'];events=api['long_intervals'];assert events['dropped']==0 and events['total']==api['over_33_333ms']==len(events['records'])
def overlap(a,b):
 segments=sorted((max(a,g['start_ns']),min(b,g['end_ns']),g['generation']) for g in r['gc_collection_samples'] if min(b,g['end_ns'])>max(a,g['start_ns']))
 union=0;last=a
 for start,end,gen in segments:
  union+=max(0,end-max(last,start));last=max(last,end)
 return union,segments
rows=[]
for e in events['records']:
 union,segments=overlap(e['begin_ns'],e['end_ns']);hud=e.get('hud_lease_stages') or {};cb=(overlap(hud['callback_begin_ns'],hud['callback_end_ns'])[0] if hud else 0)
 rows.append(dict(index=e['display_index'],interval_ms=e['interval_ns']/1e6,gc_union_ms=union/1e6,gc_generations=sorted({g for a,b,g in segments}),gc_callback_overlap_ms=cb/1e6,source_prepare_ms=e['source_prepare_ns']/1e6 if e['source_prepare_ns'] is not None else None,snapshot_new=hud.get('snapshot_new'),draw_ms=(e['draw_end_ns']-e['draw_begin_ns'])/1e6,present_ms=(e['present_end_ns']-e['present_begin_ns'])/1e6))
out=dict(result='WHOLE_LONG_INTERVAL_GC_CORRELATION',total=len(rows),over50=sum(x['interval_ms']>50 for x in rows),with_gen2=sum(2 in x['gc_generations'] for x in rows),with_gc_over10ms=sum(x['gc_union_ms']>10 for x in rows),without_gc_over1ms=sum(x['gc_union_ms']<=1 for x in rows),rows=sorted(rows,key=lambda x:x['interval_ms'],reverse=True),scope='Whole observed boundedlongintervalledger with completeGCtrace; intervaloverlap correlation, not exclusive causal attribution orpixel cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'});print('slowest',out['rows'][:5])

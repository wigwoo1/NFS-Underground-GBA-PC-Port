from pathlib import Path
import json,sys
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
names=['prior_to_pair','pair_to_take','preparation_future','take_to_hud','hud_future','hud_to_pair_ready','pair_ready_to_slot','sample','sample_to_sky','sky','sky_to_owner','owner','owner_to_lock','lock','lock_to_draw'];rows=[]
for e in ledger['records']:
 a=e['begin_ns'];b=e['caller_timing']['draw_begin_ns'];c=e['caller_stages'];assert a<=b<=e['end_ns']
 values=[a,c['pair_begin_ns'],c['preparation_take_begin_ns'],c['preparation_take_end_ns'],c['hud_prefetch_wait_begin_ns'],c['hud_prefetch_wait_end_ns'],c['pair_ready_ns'],c['slot_begin_ns'],c['sample_end_ns'],c['sky_begin_ns'],c['sky_end_ns'],c['owner_begin_ns'],c['owner_end_ns'],c['lock_begin_ns'],c['lock_acquired_ns'],b]
 values=[max(a,min(b,x)) for x in values];assert values==sorted(values)
 parts=dict(zip(names,[y-x for x,y in zip(values,values[1:])]))
 assert sum(parts.values())==b-a
 old,new=e['transaction']['commit'][2:4]
 matches=[x for x in r['world_preparation_stage_samples'] if (x['older'],x['newer'])==(old,new) and x['started_ns']<=c['slot_begin_ns']]
 request=max(matches,key=lambda x:x['started_ns']) if matches else None
 first_parts=None
 if request is not None and request['parent_sample_rows']:
  terminal=request['terminal'][5];first=terminal['sample_transfer_rows'][0];parent=request['parent_sample_rows'][0]
  begin=c['preparation_take_begin_ns'];end=c['preparation_take_end_ns']
  if parent['published_ns']<=end:
   ticks=[begin,request['started_ns'],terminal['child_started_ns'],terminal['constructed_ns'],first['ready_ns'],parent['received_ns'],parent['published_ns'],end]
   clipped=[max(begin,min(end,t)) for t in ticks];assert clipped==sorted(clipped)
   first_parts=dict(zip(['queue_before_start','input_pack_send_receive','input_decode_construct','first_source_sample','first_transfer_receive','parent_decode_publish','future_return'],[(y-x)/1e6 for x,y in zip(clipped,clipped[1:])]))
   assert abs(sum(first_parts.values())-(end-begin)/1e6)<1e-6
 rows.append(dict(index=e['display_index'],older=old,newer=new,interval_ms=e['interval_ns']/1e6,predraw_ms=(b-a)/1e6,parts_ms={k:v/1e6 for k,v in parts.items()},first_wait_parts_ms=first_parts,request_begin_ns=None if request is None else request['started_ns'],request_completed_before_slot=None if request is None else request['completed_ns']<=c['slot_begin_ns']))
out=dict(result='PASS_PROGRESSIVE_PREDRAW_PARTITIONS',intervals=len(rows),first_wait_totals_ms={k:sum(x['first_wait_parts_ms'].get(k,0) for x in rows if x['first_wait_parts_ms'] is not None) for k in ['queue_before_start','input_pack_send_receive','input_decode_construct','first_source_sample','first_transfer_receive','parent_decode_publish','future_return']},totals_ms={k:sum(x['parts_ms'][k] for x in rows) for k in names},rows=rows,scope='Complete retained >25ms native interval clipped caller partitions; latest chronological source request match, not per-alpha readiness or exclusive CPU attribution.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result']);print(out['totals_ms']);print(out['first_wait_totals_ms'])
for row in sorted(rows,key=lambda x:x['predraw_ms'],reverse=True)[:5]:print(row)

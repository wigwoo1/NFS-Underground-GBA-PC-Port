import json,sys,math
from pathlib import Path
from owned_sky_scroll import source_offset
p=Path(sys.argv[1]);r=json.loads(p.read_text());records=r['sky_capture_records'];retention=r['sky_capture_retention'];assert len(records)==retention['retained_records']
manifest=json.loads(Path(sys.argv[3]).read_text());capture_ids={(x["epoch"],x["generation"],x["index"]) for x in manifest["rows"]}
wraps=[];previous=None
for row in records:
 assert row['source']-row['asset_origin']==source_offset(row['angle'],240,0)
 phase=((row['angle']&16383)*240/4096)%240
 if previous:
  old,op=previous
  assert old['epoch']==row['epoch'] and old['publication']<row['publication']
  delta=((row['angle']-old['angle']+8192)&16383)-8192
  travel=delta*240/4096
  if abs(phase-op)>120:
   assert abs(travel)<120
   wraps.append(dict(older=old['publication'],newer=row['publication'],older_phase=op,newer_phase=phase,unwrapped_travel=travel))
 previous=row,phase
ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
gaps=[]
for e in ledger['records']:
 tx=e['transaction'];caller=e['caller_timing'];a=e['begin_ns'];b=e['end_ns'];prepare=max(0,min(b,caller['draw_end_ns'])-max(a,caller['draw_begin_ns']))
 gaps.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],interval_ms=(b-a)/1e6,prepare_ms=prepare/1e6,prior_to_prepare_ms=max(0,min(b,caller['draw_begin_ns'])-a)/1e6,capture_window=(e["epoch"],e["generation"],e["display_index"]) in capture_ids,gc_overlaps=sum(max(a,g['start_ns'])<min(b,g['end_ns']) for g in r['gc_collection_samples'])))
out=dict(result='VERIFIED_RETAINED_SKY_SOURCE_WRAP_AND_GAP_EVIDENCE',source=str(p.resolve()),source_records=len(records),source_retention=retention,wraps=wraps,gaps=gaps,scope='Exact original source-pointer formula checked on retained source records only. Dropped early records explicitly prevent whole-run wrap coverage. Gap phase durations partition observed time, not exclusive cause.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(result=out["result"],source_records=len(records),wrap_count=len(wraps),dropped_source_records=retention["dropped_records"],gaps=gaps)))


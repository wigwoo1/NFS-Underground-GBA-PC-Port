import json,sys,statistics
from pathlib import Path
runs=[]
for filename in sys.argv[1:-1]:
 r=json.loads(Path(filename).read_text());rows=[];excluded=[]
 for p in r['world_preparation_stage_samples']:
  terminal=p['terminal'];t=terminal[5]
  if terminal[2]!='complete' or not t['sample_transfer_rows']:
   excluded.append([p['older'],p['newer'],terminal[2]]);continue
  start=p['parent_start_timing'];first=t['sample_transfer_rows'][0];assert first['index']==0
  stamps=[start['pack_begin_ns'],start['packed_ns'],start['sent_ns'],t['child_started_ns'],t['decoded_ns'],t['initialized_ns'],t['constructed_ns'],first['ready_ns']];assert stamps==sorted(stamps)
  names=['pack','send','child_queue','decode','initialize','construct','first_sample'];parts={k:(b-a)/1e6 for k,a,b in zip(names,stamps,stamps[1:])};total=(stamps[-1]-stamps[0])/1e6
  assert abs(sum(parts.values())-total)<1e-6
  rows.append(dict(pair=[p['older'],p['newer']],generation=p['generation'],total_first_sample_ms=total,parts_ms=parts,selected=t['scene_merge_stats'] is not None))
 assert rows
 def summarize(values):
  v=sorted(values);return dict(count=len(v),median=statistics.median(v),p95=v[int((len(v)-1)*.95)],maximum=v[-1])
 summary={k:summarize([x['parts_ms'][k] for x in rows]) for k in names};summary['total_first_sample']=summarize([x['total_first_sample_ms'] for x in rows])
 runs.append(dict(source=filename,processed=len(rows),excluded=excluded,summary_ms=summary,rows=rows))
out=dict(result='PASS_RECORDED_PREPARATION_FIRST_SAMPLE_PARTITIONS',runs=runs,scope='Every retained complete sample-bearing source job, exact ordered timestamps and additive first-sample partition. Exclusions explicit; no missing-job excuse or causal scheduler attribution. Sequential comparison, not randomized benchmark.')
Path(sys.argv[-1]).write_text(json.dumps(out,indent=2));print(json.dumps([{'source':x['source'],'processed':x['processed'],'excluded':len(x['excluded']),'summary_ms':x['summary_ms']} for x in runs]))

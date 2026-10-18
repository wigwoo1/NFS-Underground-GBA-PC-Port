import json,sys
from pathlib import Path
raw=Path(sys.argv[1]);manifest=Path(sys.argv[2]);r=json.loads(raw.read_text());m=json.loads(manifest.read_text());out=[]
for event in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 a,b=event['begin_ns'],event['end_ns'];matches=[]
 for row in m['rows']:
  for kind in ('capture','poll'):
   lo,hi=row[kind+'_begin_ns'],row[kind+'_end_ns'];assert lo<=hi
   overlap=max(0,min(b,hi)-max(a,lo))
   if overlap:matches.append(dict(kind=kind,identity=row['identity'],y=row['y'],overlap_ms=overlap/1e6))
 out.append(dict(identity=[event['epoch'],event['generation'],event['display_index']],interval_ms=(b-a)/1e6,capture_or_poll_overlaps=matches,nearest_capture_distance_ms=min(max(0,a-x['capture_end_ns'],x['capture_begin_ns']-b) for x in m['rows'])/1e6))
report=dict(result='COMPLETE_LONG_GAP_CAPTURE_OVERLAP_AUDIT',rows=out,scope='Exact recorded capture/poll interval intersections. Excludes uninstrumented hook/hostcopy work and does not prove scheduling cause.')
Path(sys.argv[3]).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

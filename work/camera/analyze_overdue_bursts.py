"""Measure late sample catch-up without changing presentation/game clocks."""
import json,sys,statistics
from pathlib import Path

def analyze(r):
 rows=[x for x in r['presentation_samples'] if x.get('native_committed_sample')]
 assert rows
 periods=[];bursts=[];current=[]
 for previous,row in zip(rows,rows[1:]):
  assert row['display_index']==previous['display_index']+1
  begin=previous['native_committed_sample'][6];end=row['native_committed_sample'][6]
  assert end>=begin
  paused=any(max(begin,p['begin_ns'])<min(end,p['end_ns']) for p in r.get('pause_events',[]))
  late=(end-row['presentation_deadline_ns'])/1e6
  if not paused and end-begin<1000000000/120 and late>1000/60:
   current.append(dict(display_index=row['display_index'],gap_ms=(end-begin)/1e6,late_ms=late,older=row['source_older'],newer=row['refresh']))
  else:
   if current:bursts.append(current);current=[]
  if not paused:periods.append((end-begin)/1e6)
 if current:bursts.append(current)
 return dict(result='MEASURED_OVERDUE_CATCHUP',presentation_count=len(rows),rapid_late_samples=sum(map(len,bursts)),burst_count=len(bursts),longest_bursts=sorted(bursts,key=len,reverse=True)[:10],active_median_gap_ms=statistics.median(periods) if periods else None,scope='Rapid commits defined as gap<8.333ms and deadline lateness>16.667ms, excluding recorded pause crossings. Consecutive indices verified. Commit completion is not physical scanout; late sample counts do not justify dropping game updates or certify a replacement policy.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='longest_bursts'},indent=2))

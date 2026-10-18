"""Whole native burst/deadline counters, bounded matched diagnostic only."""
import json,re,sys
from pathlib import Path
runs={}
for label,path in zip(('sync','immediate'),sys.argv[1:3]):
 log=Path(path).read_text();assert 'SMOKE_COMPLETE' in log and 'Traceback' not in log
 raw=Path(re.findall(r'[^\r\n]*owned-native-\d+\.json',log)[0].strip());d=json.loads(raw.read_text());a=d['bounded_diagnostic_stats']['whole_run_api_intervals'];s=a['native_commit_intervals'];l=a['native_commit_long_intervals'];assert l['dropped']==0 and l['total']==len(l['records'])
 assert 0<=s['under8']<=s['count'] and 0<=s['min_ms']<=s['max_ms'] and s['deadline_late_count']<=s['count']+s['excluded']+1
 assert s['deadline_late_total_ms']>=s['deadline_late_max_ms']>=0
 late=[max(0,x['transaction']['wait'][0]-x['transaction']['wait'][1])/1e6 for x in l['records']]
 assert max(late,default=0)<=s['deadline_late_max_ms']+1e-6
 runs[label]=dict(raw=str(raw),native=s,long_interval_late_count=sum(x>0 for x in late),long_interval_count=len(late))
out=dict(result='PASS_WHOLE_NATIVE_BURST_DEADLINE_PAIR',runs=runs,cadence_qualified=False,scope='Sequential10s equivalentsettings. Complete native adjacent interval scalar counters and long ledger; lateness at wait entry is not proof of exclusive cause, current clock speed change or physical scanout. Short runs do not establish sustained60 or policy benefit.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v['native'] for k,v in runs.items()}))

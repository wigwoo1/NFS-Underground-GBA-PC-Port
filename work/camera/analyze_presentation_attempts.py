import csv,json,statistics,sys
from pathlib import Path
p=Path(sys.argv[1]);read=lambda suffix:list(csv.DictReader(Path(str(p)+suffix).open()))
a=read('-attempts.csv');c=read('-context.csv');q=read('-producer.csv');ticks=read('-input.csv')
assert a and len(a)==len(c)
if Path(str(p)+'-clock-polls.csv').exists(): assert len(a)==sum(int(r['present']) for r in read('-clock-polls.csv'))
for x,y in zip(a,c):
 assert int(x['epoch'])==int(y['epoch']) and float(x['target'])==float(y['target']) and int(x['context_found'])==int(y['found'])
 assert int(x['outcome']) in (0,1,2) and int(x['end_ns'])>=int(x['begin_ns'])
assert len(q)==sum(int(x['outcome'])!=0 for x in a)
assert sum(int(x['outcome'])==2 for x in a)==sum(int(x['pushed']) for x in q)
intervals=sorted([(int(x['begin_ns']),int(x['end_ns'])) for x in a]+[(int(x['start_ns']),int(x['end_ns'])) for x in ticks])
assert all(x[1]<=y[0] for x,y in zip(intervals,intervals[1:])), 'Producer intervals overlap'
groups={}
for outcome,label in [(0,'unavailable'),(1,'queue_rejected'),(2,'queued')]:
 v=sorted((int(x['end_ns'])-int(x['begin_ns']))/1e6 for x in a if int(x['outcome'])==outcome)
 groups[label]={'count':len(v),'total_ms':sum(v),'median_ms':statistics.median(v) if v else None,'max_ms':max(v) if v else None}
out={'result':'ALL_PRESENTATION_ATTEMPTS_JOIN_EXACT','prefix':str(p),'attempts':len(a),'groups':groups,'scope':'All planned capture attempt wall intervals; logging/profiling overhead remains; excludes backlog-suppressed clock polls, no scanout or 60fps proof'}
Path(str(p)+'-attempt-analysis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))


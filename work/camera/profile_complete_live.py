from pathlib import Path
import json,csv,statistics
p=Path(__file__).resolve().parent;r=json.loads((p/'threaded-stable-complete-test.json').read_text());assert not r['complete_readback_requested'],'Intrusive readback run cannot profile normal draw cost'
prefix=r['prefix'];rows=list(csv.DictReader(open(prefix+'-worker.csv')));producer=list(csv.DictReader(open(prefix+'-producer.csv')))
def stats(values):
 values=sorted(values);return dict(count=len(values),median_ms=statistics.median(values),p95_ms=values[min(len(values)-1,int(len(values)*.95))],max_ms=max(values),over_16_667_ms=sum(x>1000/60 for x in values))
report=dict(prefix=prefix,scope='Single diagnostic four-second run; draw duration includes driver scheduling, not GPU timer measurement; discrete held motion',host_stats=r['host_stats'],draw_by_kind={k:stats([(int(x['draw_end_ns'])-int(x['start_ns']))/1e6 for x in rows if x['frame_kind']==k]) for k in sorted({x['frame_kind'] for x in rows})},producer_capture_to_push=stats([(int(x['push_begin_ns'])-int(x['begin_ns']))/1e6 for x in producer]),deadline_lateness=stats([max(0,int(x['commit_begin_ns'])-int(x['deadline_ns']))/1e6 for x in rows if x['committed']=='1']))
committed=[x for x in rows if x['committed']=='1'];rate=16777216/(280896*60)
slots=[round((float(x['target'])-int(x['source_base'])+8)/rate) for x in committed];assert all(b>a for a,b in zip(slots,slots[1:]))
report['presentation_slots']=dict(first=slots[0],last=slots[-1],committed=len(slots),missing_between=sum(b-a-1 for a,b in zip(slots,slots[1:])),max_slot_gap=max([b-a for a,b in zip(slots,slots[1:])] or [0]),scope='Internal gaps only; startup/end excluded; no physical scanout verification')
report['commit_intervals']=stats([(int(b['commit_begin_ns'])-int(a['commit_begin_ns']))/1e6 for a,b in zip(committed,committed[1:])])
(p/'complete-live-profile.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

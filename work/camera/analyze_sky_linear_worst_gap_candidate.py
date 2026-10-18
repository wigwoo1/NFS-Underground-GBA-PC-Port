"""Join complete native gaps with exact scene-preparation boundaries."""
from pathlib import Path
import json,sys
raw=Path(sys.argv[1]);r=json.loads(raw.read_text())
ledger=r["bounded_diagnostic_stats"]["whole_run_api_intervals"]["native_commit_long_intervals"]
slow=r["preparation_retention"]["slow_process_intervals"]
assert ledger["dropped"]==0 and slow["dropped"]==0
event=max(ledger["records"],key=lambda x:x["interval_ns"])
caller=event["caller_stages"]
begin=caller["preparation_take_begin_ns"];end=caller["preparation_take_end_ns"]
commit=event["transaction"]["commit"];older,newer=commit[2:4]
matches=[x for x in slow["records"] if (x["older"],x["newer"])==(older,newer)]
assert len(matches)==1
request=matches[0];assert request["child_gc_dropped"]==0
overlap=lambda a,b:max(0,min(end,b)-max(begin,a))/1e6
bound=request["child_boundaries"]
assert bound["started_ns"]<=bound["decoded_ns"]<=bound["initialized_ns"]<=bound["constructed_ns"]<=bound["sampled_ns"]<=bound["encoded_ns"]<=bound["sent_ns"]
phases=[]
for a,b in zip(("started_ns","decoded_ns","initialized_ns","constructed_ns","sampled_ns","encoded_ns"),("decoded_ns","initialized_ns","constructed_ns","sampled_ns","encoded_ns","sent_ns")):
 phases.append(dict(begin=a,end=b,whole_ms=(bound[b]-bound[a])/1e6,wait_overlap_ms=overlap(bound[a],bound[b])))
gc=[dict(generation=g["generation"],whole_ms=(g["end_ns"]-g["start_ns"])/1e6,wait_overlap_ms=overlap(g["start_ns"],g["end_ns"])) for g in request["child_gc_rows"]]
out=dict(result="PASS_EXACT_WORST_GAP_ATTRIBUTION",raw=str(raw.resolve()),identity=[event["epoch"],event["generation"],event["display_index"]],interval_ms=event["interval_ns"]/1e6,preparation_wait_ms=(end-begin)/1e6,sky_sample_ms=(caller["sky_end_ns"]-caller["sky_begin_ns"])/1e6,child_identity=[older,newer],child_phases=phases,child_gc=gc,scope="Exact elapsed interval association. Child phases may begin before caller wait; GC is nested, not additive or exclusive cause. Transfer elapsed includes scheduling. No CPU-time conversion or smooth gameplay claim.")
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

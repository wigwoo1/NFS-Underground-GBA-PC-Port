"""Complete saved request partitions, no conversion of cycles to CPU time."""
from pathlib import Path
import sys,json
r=json.loads(Path(sys.argv[1]).read_text())
retained=r["preparation_retention"]["slow_process_intervals"]
assert retained["dropped"]==0
rows=[x for x in retained["records"] if (x["older"],x["newer"])==(9126,9130)]
assert len(rows)==1
x=rows[0];assert not x["stage_records_truncated"] and not x["encode_samples_truncated"]
samples=x["sample_stages"];assert len(samples)==x["encode_sample_count"]==4
bound=x["child_boundaries"];cursor=bound["constructed_ns"];gaps=[];out=[]
for sample in samples:
 assert cursor<=sample["started_ns"]<=sample["completed_ns"]<=bound["sampled_ns"]
 gaps.append(dict(kind="before_sample",alpha=sample["alpha"],wall_ms=(sample["started_ns"]-cursor)/1e6))
 cursor=sample["completed_ns"]
 stages=sample["stages"];assert len(stages)==4
 for stage in stages:
  assert sample["started_ns"]<=stage["started_ns"]<=stage["completed_ns"]<=sample["completed_ns"]
 out.append(dict(alpha=sample["alpha"],wall_ms=sample["wall_ns"]/1e6,thread_cycles=sample["thread_cycles"],
  stages=[dict(name=s["name"],wall_ms=s["wall_ns"]/1e6,thread_cycles=s["thread_cycles"]) for s in stages],
  slowest_assembly=sample["slowest_assembly_stages"]))
gaps.append(dict(kind="after_last_sample",wall_ms=(bound["sampled_ns"]-cursor)/1e6))
total=sum(s["wall_ms"] for s in out)+sum(s["wall_ms"] for s in gaps)
assert abs(total-(bound["sampled_ns"]-bound["constructed_ns"])/1e6)<1e-7
mask=[next(s for s in row["stages"] if s["name"]=="source_face_mask") for row in out]
fast=min(mask,key=lambda s:s["wall_ms"]);slow=max(mask,key=lambda s:s["wall_ms"])
encoding=[dict(alpha=s[0],wall_ms=(s[2]-s[1])/1e6,thread_cycles=s[3],frame_bytes=s[4]) for s in x["encode_samples"]]
result=dict(result="PASS_COMPLETE_REQUEST_PARTITIONS",source=sys.argv[1],identity=[9126,9130],sample_phase_ms=total,samples=out,gaps=gaps,
 mask_elapsed_ratio=slow["wall_ms"]/fast["wall_ms"],mask_cycle_ratio=slow["thread_cycles"]/fast["thread_cycles"],encoding=encoding,
 scope="Same request elapsed/cycle comparison, not CPU-time conversion or exclusive scheduling/paging diagnosis. Assembly list retains only top3 stages. Fullsample partitions complete; unexplained gaps retained.")
Path(sys.argv[2]).write_text(json.dumps(result,indent=2))
print("PASS",round(total,4),"ms; mask elapsed ratio",round(result["mask_elapsed_ratio"],2),"cycles ratio",round(result["mask_cycle_ratio"],2))

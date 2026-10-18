"""Compare complete deterministic capture reports, excluding measured durations."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("reports",nargs="+",type=Path)
p.add_argument("--output",type=Path,required=True)
args=p.parse_args()
assert len(args.reports)>=2,"Supply a reference and at least one candidate report"
rows=[json.loads(path.read_text()) for path in args.reports]
reference=rows[0]
assert reference["frames"]>0
assert len(reference["original_frame_hashes"])==reference["frames"]
assert reference["packets"] and reference["backgrounds"] and reference["hud_text_samples"]
assert any(row[2]>0 for row in reference["backgrounds"]),"No covered background pixels were checked"
fields=["frames","packets","original_frame_hashes","backgrounds","hud_text_samples"]
for path,row in zip(args.reports[1:],rows[1:]):
 for name in fields:
  assert reference[name]==row[name],f"{path}: different {name}"
result=dict(result="PASS",frames=reference["frames"],reports=[str(path) for path in args.reports],scene_packets=len(reference["packets"]),background_snapshots=len(reference["backgrounds"]),hud_text_samples=len(reference["hud_text_samples"]),exact_fields=fields,scope="Deterministic checkpoint capture equivalence; not full-course or display cadence verification")
args.output.write_text(json.dumps(result,indent=2))
print(json.dumps(result))

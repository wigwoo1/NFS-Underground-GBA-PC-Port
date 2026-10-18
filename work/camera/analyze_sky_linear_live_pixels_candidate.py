import json,sys
from pathlib import Path
import numpy as np
manifest=Path(sys.argv[1]);r=json.loads(manifest.read_text());rows=r["rows"];assert len(rows)==16
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
y=np.floor((np.arange(594,1458,27,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
checks=[];previous=None;motions=[]
for row in rows:
 data=np.load(row["file"]);actual=data["actual"];lo=data["lower"][y[:,None],x[None,:]];hi=data["upper"][y[:,None],x[None,:]]
 assert actual.shape==(32,3240,4) and 0<=row["phase"]<=1
 expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(row["phase"])).astype(np.uint8)
 opaque=(lo[:,:,3]>127)&(hi[:,:,3]>127)
 match=np.all(np.abs(actual.astype(np.int16)-expected.astype(np.int16))<=1,axis=2)&opaque
 assert row["native_result"]==1 and row["commit"][:2]==row["identity"][:2] and row["commit"][4]==row["identity"][2]
 checks.append(dict(identity=row["identity"],phase=row["phase"],matching_pixels=int(match.sum()),pixels=match.size))
 if previous:
  prior,old_actual,old_expected,old_match=previous
  if row["identity"][:2]==prior["identity"][:2] and row["identity"][2]==prior["identity"][2]+1:
   jointly_visible=match&old_match
   expected_changes=np.any(expected!=old_expected,axis=2)&jointly_visible
   actual_changes=np.any(actual!=old_actual,axis=2)&jointly_visible
   motions.append(dict(from_index=prior["identity"][2],to_index=row["identity"][2],jointly_matching_pixels=int(jointly_visible.sum()),expected_changed_pixels=int(expected_changes.sum()),actual_changed_pixels=int(actual_changes.sum()),expected_changes_visible=int((expected_changes&actual_changes).sum())))
 previous=row,actual,expected,match
out=dict(result="DIAGNOSTIC_CAPTURE_ANALYZED",checks=checks,motions=motions,scope="16 synchronous owner-thread GPU captures tied to successful native commits. Matches independent linear source-color oracle in visible sky pixels; unmatched occlusions retained, not excused as fidelity proof. Readback perturbs timing; no physical scanout or full-scene60fps certification.")
out["visibility_gate_passed"]=min(x["matching_pixels"] for x in checks)>1000
out["motion_gate_passed"]=any(x["expected_changed_pixels"]>1000 and x["expected_changes_visible"]>1000 for x in motions)
out["result"]="PASS_BOUNDED_LIVE_SKY_PIXEL_MOTION" if out["visibility_gate_passed"] and out["motion_gate_passed"] else "FAIL_LIVE_SKY_PIXEL_GATE"
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out["result"],"matches",min(x["matching_pixels"] for x in checks),"moving transitions",sum(x["expected_changed_pixels"]>0 for x in motions))
if not(out["visibility_gate_passed"] and out["motion_gate_passed"]):sys.exit(1)

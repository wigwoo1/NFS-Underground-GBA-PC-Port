"""Validate earlier source-only poses against actual later native scene packets."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("capture",type=Path)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args();j=json.loads(a.capture.read_text())
rows=j["pose_boundaries"];timing=j["scene_timing"];early=j["early_poses"]
assert rows and not j["pose_boundary_missing"] and len(rows)==len(timing)==len(j["packets"])
entry_models=packet_models=early_closed=0;source_lead=[];geometry_lead=[];available_lead=[]
for row,t in zip(rows,timing):
 m=row["meta"];assert m[:4]==t[:4] and m[10]==1 and m[11]==31
 assert m[12]==m[13]==m[14] and m[15]==0,"Source camera/object pose changed before a model entry"
 assert row["models"]==row["packet_camera_matches"]==row["known_packet_objects"]==row["packet_position_matches"]
 assert row["root_sky_angle_matches"] and row["root_sky_center_matches"]
 assert m[4]<t[5]<=t[6]<=t[4],"Source snapshot did not precede geometry"
 entry_models+=m[12];packet_models+=row["models"]
 source_lead.append((t[4]-m[4])/280896)
 geometry_lead.append((t[5]-m[4])/280896)
 source=early.get(str(m[1]))
 assert source,"Source snapshot was not observed before completion"
 raw=bytes.fromhex(source["raw_hex"]);closed=bytes.fromhex(row["raw_hex"])
 assert raw[128:]==closed[128:]
 lead=m[3]-source["first_available_refresh"]
 assert lead>0,"Source input not readable before original flip"
 available_lead.append(lead);early_closed+=1
def summary(v):return dict(min=min(v),median=statistics.median(v),max=max(v))
result=dict(result="PASS",original_frames=j["frames"],closed_scenes=len(rows),
 entry_pose_matches=entry_models,finished_model_camera_and_position_matches=packet_models,
 coherent_sky_scenes=len(rows),early_sources_matched_to_finished_scenes=early_closed,
 early_immutable_reads=j["early_pose_reads"],source_to_original_flip_frames=summary(source_lead),
 source_before_first_geometry_frames=summary(geometry_lead),
 host_available_before_flip_refreshes=summary(available_lead),
 source_only_not_complete_geometry=True,
 scope="Actual source camera/known-racer pose/sky coherence and early input availability; not a rendered interpolation fix, all-object snapshot, full-course validation or 60fps gameplay.")
a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

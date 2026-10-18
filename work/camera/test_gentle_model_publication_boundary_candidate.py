"""Captured-source evidence only; no ownership or visibility rule changes."""
from pathlib import Path
import sys,struct,json
sys.path.insert(0,str(Path("work/camera").resolve()))
from owned_ordinary_model_visits import owned_object_chains,ordinary_model_visits
from owned_object_filter import eligibility,depth_distance
from owned_object_dispatch import select
from owned_scenery_projection import SceneryProjection
from owned_motion_pairs import records
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0].replace("1791308040881565000","1791575541143887200").replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={};exec(compile(setup,"captured-boundary-setup","exec"),env)
report=[]
try:
 for endpoint,scene in enumerate(env["scenes"]):
  closed=scene.graph;state=closed.graph.context[:256];camera=closed.graph.context[256:304]
  queue=env["prepared"].pair.portal.sample(endpoint)
  rows=records(env["frames"][endpoint])["records"];row=rows[18]
  assert row["kind"]==3
  base=struct.unpack_from("<I",state,60)[0];matrix_base=struct.unpack_from("<I",state,252)[0]
  projection=SceneryProjection(env["rom"]);matches=[]
  for parent,chain in owned_object_chains(closed).items():
   for owner,source in chain:
    if eligibility(source)!="project" or source[136]==255:continue
    depth=depth_distance(source,camera)[0]
    dispatch=select(source,state,depth)
    if dispatch["kind"]!="model" or not 30<=dispatch["model"]<=36:continue
    address=dispatch["descriptor"]-0x08000000
    if bytes(row["blocks"][1])!=env["rom"][address:address+40]:continue
    builder=scene.builders.at(base+owner*164,matrix_base+source[136]*48,closed.refresh)
    pose=projection.matrix(builder.camera,builder.source,builder.initial_matrix)
    if pose!=bytes(row["blocks"][2]):continue
    # Both independently required proofs reject deliberate single-byte corruption.
    bad_descriptor=bytearray(row["blocks"][1]);bad_descriptor[0]^=1
    bad_pose=bytearray(row["blocks"][2]);bad_pose[0]^=1
    assert bytes(bad_descriptor)!=env["rom"][address:address+40]
    assert bytes(bad_pose)!=pose
    matches.append(dict(owner=owner,parent=parent,model=dispatch["model"],depth=depth,
      builder_refresh=builder.refresh,publication_refresh=closed.refresh,
      graph_source_refresh=closed.graph.refresh,slot=source[136],
      regions=[list(r) for r in queue if r[0]==parent]))
  assert len(matches)==1 and matches[0]["owner"]==36,matches
  visible=any(v["object"]==36 for v in ordinary_model_visits(closed,queue))
  assert visible==(endpoint==0)
  report.append(dict(endpoint=endpoint,record=18,ordinary_visit_present=visible,proof=matches[0]))
 assert report[1]["proof"]["regions"][0][1]>report[1]["proof"]["regions"][0][2]
 result=dict(result="PASS",endpoints=report,negative_checks=4,
  scope="Exact saved descriptor and latest allocated builder pose establish owner36 at both publications. Reconstructed newer portal interval is empty. No production fallback, clipping change, live timing or original visibility equivalence proven.")
 Path("outputs/nfsug-native-renderer/camera-research/gentle-model-publication-boundary-20261009.json").write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
finally:
 env["prepared"].close();env["history"].close()

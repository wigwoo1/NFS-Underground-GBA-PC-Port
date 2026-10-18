"""Captured active child endpoint selection, inherited bounds and source closure."""
import audit_active_road_child_actions as fixture
from owned_endpoint_road_selection import endpoint_road_span_candidates
from owned_complete_road_candidates import road_candidates
from owned_closed_scene_memory import ClosedSceneMemory
from owned_endpoint_road_planner import EndpointRoadPlanner
import json
from pathlib import Path
checks=[]
planner=EndpointRoadPlanner(fixture.rom,fixture.table)
try:
 for endpoint,scene in enumerate(fixture.scenes):
  memory=ClosedSceneMemory(scene,fixture.rom)
  selected=endpoint_road_span_candidates(scene,memory,road_candidates(scene,memory),fixture.table,include_empty=True)
  child=[x for x in selected if x['descriptor']==228];assert len(child)==1
  parent=[x for x in selected if x['descriptor']==22];assert len(parent)==1
  assert child[0]['bounds']==parent[0]['bounds'] and child[0]['ordinal']==parent[0]['ordinal']
  assert child[0]['static_depth']==1 and parent[0]['static_depth']==0
  assert child[0]['input_count']==4 and parent[0]['input_count']==10
  assert selected.index(parent[0])<selected.index(child[0])
  actual,details=planner.plan(scene)
  assert any(x['descriptor']==228 for x in details)
  checks.append(dict(endpoint=endpoint,child_bounds=child[0]['bounds'],child_spans=child[0]['spans'],child_runs=[x for x in details if x['descriptor']==228],missing_reads=memory.missing))
 assert all(not x['missing_reads'] for x in checks)
 result=dict(result='PASS',checks=checks,scope='Original endpoint road traversal and scratch progression only; fractional clipping/full-scene composition unverified')
 Path('work/camera/endpoint-static-road-traversal-tests.json').write_text(json.dumps(result,indent=2));print(result)
finally:planner.close()

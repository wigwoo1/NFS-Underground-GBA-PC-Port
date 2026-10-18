"""Compare captured original scene association regions with recovered endpoint queues."""
import json,sys,struct
from pathlib import Path
from owned_scene_bundle import chunks
from owned_wall_region_candidates import regions
# Reuse only the retained-operand data adapter, without executing its CLI.
namespace={};source=Path('work/camera/analyze_live_portal_operands_candidate.py').read_text().split('path=Path(sys.argv[1])',1)[0];exec(compile(source,'portal-data-adapter','exec'),namespace)
PortalGraph=namespace['PortalGraph']
path=Path(sys.argv[1]);data=json.loads(path.read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes())
checks=[];mismatches=[];total=0
for digest,row in data['graphs'].items():
 graph=PortalGraph(row);assert digest==graph.digest()
 queue=regions(graph,table);original=[];last_ordinal=len(queue)
 for header,raw in chunks(bytes.fromhex(row['original_associations']),'associations'):
  assert header[0]==0x3241534e and raw[352:400]==graph.context[256:304]
  region=struct.unpack_from('<8H',raw,32)[:7];serial=header[7]
  matching=[i for i in range(last_ordinal-1,-1,-1) if tuple(queue[i])==tuple(region)]
  ordinal=matching[0] if matching else None
  original.append(dict(association_serial=serial,matched_queue_ordinal=ordinal,region=list(region)))
  total+=1
  if ordinal is None:mismatches.append(dict(graph=digest,source_refresh=graph.refresh,scene_refresh=row['scene_refresh'],association_serial=serial,original=list(region),remaining_queue=[list(r) for r in queue[:last_ordinal]]))
  else:last_ordinal=ordinal
 assert len(original)==len(queue) and {r['matched_queue_ordinal'] for r in original}==set(range(len(queue))), ('Incomplete original queue association coverage',digest)
 checks.append(dict(graph=digest,source_refresh=graph.refresh,scene_refresh=row['scene_refresh'],recovered_regions=len(queue),original_associations=original))
assert total>0
out=dict(result='PASS_CAPTURED_ORIGINAL_ENDPOINT_ASSOCIATION_REGIONS' if not mismatches else 'FAIL_CAPTURED_ORIGINAL_ENDPOINT_ASSOCIATION_REGIONS',graphs=len(checks),original_regions=total,complete_captured_endpoint_queue_coverage=True,mismatches=mismatches,checks=checks,scope='Original captured association region bytes and reverse dispatch order compared to recovered endpoint traversal; association serial is not a queue ordinal. All captured queue ordinals covered exactly once in these captured graphs. Does not establish coverage outside the captured interval, fractional topology or full-scene60 proof.')
path.with_name(path.stem+'-original-associations-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('checks','mismatches')});print('mismatches',len(mismatches));assert not mismatches,mismatches[:3]

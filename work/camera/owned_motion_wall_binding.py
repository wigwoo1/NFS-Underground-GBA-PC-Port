"""Bind native wall records to owned graph edges, never projected screen geometry."""
import struct
from collections import defaultdict
from owned_motion_pairs import records
from owned_motion_wall_regions import wall_region_candidates

def bind_wall_records(frame,portal_pair,endpoint,supplements=None):
 if endpoint not in (0,1):raise ValueError('Expected discrete binding endpoint')
 scene=records(frame)
 if supplements is not None:
  graph=portal_pair.newer if endpoint==1 else portal_pair.older
  if (supplements.epoch,supplements.refresh,supplements.source_refresh)!=(scene['epoch'],scene['refresh'],graph.refresh):raise ValueError('Stale supplemental binding identity')
 candidates=wall_region_candidates(portal_pair,endpoint)
 by_source=defaultdict(list)
 for c in candidates:by_source[(c.wall.vertices,c.wall.offsets)].append(c)
 supplemental_by_source=defaultdict(list)
 if supplements is not None:
  from types import SimpleNamespace
  from owned_graph_wall_sources import supplemental_wall_sources
  from owned_scene_bundle import chunks
  proxy=SimpleNamespace(supplements=supplements.geometry,textures=supplements.textures,validate=lambda:None)
  walls=supplemental_wall_sources(proxy)
  for call,(h,raw) in enumerate(chunks(supplements.geometry,'supplements')):
   vertex_set={raw[976+i*140:1044+i*140] for i in range(h[4])}
   bounds=tuple(float(x) for x in struct.unpack_from('<4H',raw,194))
   for wall in walls:
    if wall.descriptor==h[3] and wall.vertices[:68] in vertex_set:
     supplemental_by_source[(wall.vertices,wall.offsets,bounds)].append((call,wall.descriptor,wall.edge))
 result=[]
 for index,row in enumerate(scene['records']):
  if row['kind']!=2:continue
  source=(bytes(row['blocks'][0]),bytes(row['blocks'][1]))
  options=by_source.get(source,[])
  bounds=tuple(float(x) for x in struct.unpack('<4H',row['blocks'][5]))
  # Bounds disambiguate multiple original portal visits of the SAME raw edge.
  matches=[c for c in options if c.bounds==bounds]
  if len(matches)>1:raise ValueError('Ambiguous owned region visit')
  supplemental=supplemental_by_source.get((*source,bounds),[]) if not matches else []
  supplemental=list(dict.fromkeys(supplemental))
  if len(supplemental)>1:raise ValueError('Ambiguous supplemental source visit')
  result.append(dict(record=index,source=(matches[0].descriptor,matches[0].edge) if matches else None,supplemental=supplemental[0] if supplemental else None,endpoint_bounds=bounds,status='owned_graph_edge' if matches else 'owned_supplemental_edge' if supplemental else 'unresolved_source_visit'))
 return tuple(result)

def sampled_bound_overrides(frame,portal_pair,bindings,alpha):
 rows=records(frame)['records'];out=[0.0]*(4*len(rows));sampled=defaultdict(list)
 for c in wall_region_candidates(portal_pair,alpha):sampled[(c.descriptor,c.edge)].append(c)
 unresolved=[];disappeared=[];supplemental_held=[]
 for binding in bindings:
  index=binding['record'];bounds=binding['endpoint_bounds'];source=binding['source']
  if source is None:
   if binding.get('supplemental') is not None:supplemental_held.append(index)
   else:unresolved.append(index)
  else:
   options=sampled.get(source,[])
   if not options:disappeared.append(index)
   elif len(options)!=1:raise ValueError('Ambiguous sampled region visit')
   else:bounds=options[0].bounds
  out[index*4:index*4+4]=bounds
 return tuple(out),dict(unresolved_records=unresolved,held_supplemental_records=supplemental_held,disappeared_records=disappeared,scope='Existing wall bound diagnostic; new/missing surfaces are not integrated and cannot be called full visibility.')

"""Source-owned candidate poses; allocation remains separate from visibility."""
from dataclasses import dataclass
import struct
from owned_ordinary_model_visits import ordinary_model_visits
from owned_scenery_projection import SceneryProjection
from owned_motion_pairs import records

@dataclass(frozen=True)
class SceneryCandidate:
 object_index:int
 model:int
 descriptor:int
 allocated:bool
 source:bytes
 matrix:bytes
 builder_refresh:int|None

 def __post_init__(self):
  object.__setattr__(self,'source',bytes(self.source));object.__setattr__(self,'matrix',bytes(self.matrix))

def scenery_candidates(scene,queue,frame,rom):
 scene.match(frame);projection=SceneryProjection(rom);state=scene.graph.graph.context[:256]
 base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0]
 rows=[r for r in records(frame)['records'] if r['kind']==3];out=[]
 for visit in ordinary_model_visits(scene.graph,queue,True):
  model=visit['dispatch']['model']
  if not 30<=model<=36:continue
  source=visit['source'];descriptor=visit['dispatch']['descriptor'];builder_refresh=None
  if visit['allocated']:
   if scene.builders is None:raise ValueError('Allocated scenery lacks builder closure')
   builder=scene.builders.at(base+visit['object']*164,matrix_base+source[136]*48,scene.graph.refresh)
   if struct.unpack_from('<h',builder.source,54)[0]!=model:raise ValueError('Scenery builder identity changed')
   matrix=projection.matrix(builder.camera,builder.source,builder.initial_matrix);builder_refresh=builder.refresh
   offset=descriptor-0x08000000
   if not 0<=offset<=len(rom)-40:raise ValueError('Scenery descriptor outside owned ROM')
   matches=[r for r in rows if bytes(r['blocks'][1])==rom[offset:offset+40]]
   if len(matches)!=1 or bytes(matches[0]['blocks'][2])!=matrix:raise ValueError('Scenery builder/consumed matrix mismatch')
  else:
   # Candidate geometry only: a hypothetical source builder does not activate a slot.
   matrix=projection.matrix(scene.graph.graph.context[256:304],source)
  out.append(SceneryCandidate(visit['object'],model,descriptor,visit['allocated'],source,matrix,builder_refresh))
 return tuple(out)

"""Offline replay of retained live portal operands; not original ROM equivalence."""
import sys,json,hashlib,struct,math
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_motion_visibility import sampled_regions
class PortalGraph:
 def __init__(self,row):
  self.refresh=row['refresh'];self.root=row['root']
  for name in ('context','geometry','offsets','viewport_data'):setattr(self,name,bytes.fromhex(row[name]))
  assert len(self.context)==896 and len(self.viewport_data) in (0,16)
  self.packet=GraphPacket(self.refresh,self.root,self.context,self.geometry,self.offsets,b'',viewport_data=self.viewport_data)
  self.packet.graph();self.descriptor_links=self.packet.descriptor_links
 def graph(self):return self.packet.graph()
 def validate(self):return self.graph()[0]
 def digest(self):
  blocks=(self.context,self.geometry,self.offsets,self.viewport_data)
  return hashlib.sha256(struct.pack('<4I',*map(len,blocks))+b''.join(blocks)).hexdigest()
path=Path(sys.argv[1]);data=json.loads(path.read_text());assert data['dropped']==0 and data['samples']
graphs={key:PortalGraph(row) for key,row in data['graphs'].items()};assert 0<len(graphs)<=data.get('graph_limit',32)
for key,graph in graphs.items():assert key==graph.digest()
reciprocal=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes())
checks=[]
for sample in data['samples']:
 a,b=[graphs[key] for key in sample['graph_ids']];assert a.refresh<=sample['older'] and b.refresh>=a.refresh # Original graph source refresh may precede its owning scene boundary.
 alpha=sample['alpha'];camera=sample['sampled_camera'];endpoints=sample['endpoint_cameras']
 assert len(camera)==(0 if alpha in (0,1) else 12) and all(math.isfinite(x) for x in camera)
 replay=sampled_regions(a,b,reciprocal,camera,alpha,endpoints,linked_viewports=sample['linked_viewports'])
 assert [list(region) for region in replay]==sample['portal_regions'],sample['sample_id']
 checks.append(dict(sample_id=sample['sample_id'],older=a.refresh,newer=b.refresh,alpha=alpha,regions=len(replay)))
out=dict(result='PASS_RETAINED_LIVE_PORTAL_OPERAND_REPLAY',graphs=len(graphs),samples=len(checks),checks=checks,scope='Hash-bound raw context/geometry/offsets/viewport and sampled/endpoint cameras replay exact captured portal queues. Reuses recovered traversal implementation; does not independently establish original ROM equivalence, fractional topology correctness or full-scene60fps.')
path.with_name(path.stem+'-portal-operands-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})

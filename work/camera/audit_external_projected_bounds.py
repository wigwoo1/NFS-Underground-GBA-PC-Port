"""Projected vertex envelope diagnostic; not polygon visibility equivalence."""
import runpy,struct,json,sys
from pathlib import Path
from owned_external_source_motion import PreparedExternalSourceMotion
from owned_model_sources import OwnedModelSources
v=runpy.run_path('work/camera/test_external_record_candidate.py');scenes=v['scenes'];captures=v['captures']
sources=[OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),s) for c,s in zip(captures,scenes)]
motion=PreparedExternalSourceMotion(scenes,sources,1);blocks=v['blocks'][0];vertices=list(struct.iter_unpack('<3h',blocks[4]));scale=struct.unpack_from('<I',blocks[0],64)[0];cx,cy=struct.unpack_from('<2h',blocks[3],8);evidence=[]
for i in range(101):
 alpha=i/100;m=motion.matrix(alpha);points=[tuple(m[9+k]+sum(local[j]*m[j*3+k] for j in range(3)) for k in range(3)) for local in vertices]
 assert all(p[2]>=64 for p in points),'Near crossing requires polygon clipping audit'
 projected=[(cx+scale*p[0]/p[2],cy+scale*p[1]/p[2]) for p in points]
 envelope=(min(p[0] for p in projected),max(p[0] for p in projected),min(p[1] for p in projected),max(p[1] for p in projected))
 region=next(q for q in v['portal'].sample(alpha) if q[0]==23 and not q[5]&0x88)
 rejected=envelope[1]<region[1] or envelope[0]>=region[2] or envelope[3]<region[3] or envelope[2]>=region[4]
 evidence.append(dict(alpha=alpha,envelope=envelope,portal=list(region[1:5]),envelope_rejected=rejected))
Path(sys.argv[1]).with_suffix('.external-projected-bounds.json').write_text(json.dumps(evidence,indent=2))
print('Vertex envelope rejects',sum(x['envelope_rejected'] for x in evidence),'of101 samples')
print(evidence[0],evidence[-1])

"""Source-only affine UV consistency; no screen matching or fitted renderer."""
from pathlib import Path
import json,itertools,math,hashlib
p=Path('work/camera');source=p/'stable-road-geometric-inputs.json';r=json.loads(source.read_text());checks=[]
def det(m):return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])
def solve(m,b):
 d=det(m);assert abs(d)>1e-10
 return [det([[b[i] if j==k else m[i][j] for j in range(3)] for i in range(3)])/d for k in range(3)]
for road in r['roads']:
 vertices=road['vertices'];uv=road['uv'];assert max(v[1] for v in vertices)==min(v[1] for v in vertices)
 anchors=next(ids for ids in itertools.combinations(range(len(vertices)),3) if abs(det([[vertices[i][0],vertices[i][2],1] for i in ids]))>1e-10);m=[[vertices[i][0],vertices[i][2],1] for i in anchors];coeff=[solve(m,[uv[i][axis] for i in anchors]) for axis in (0,1)];errors=[]
 for i,v in enumerate(vertices):
  expected=[c[0]*v[0]+c[1]*v[2]+c[2] for c in coeff];diff=[(uv[i][axis]-expected[axis])*(road['width'] if axis==0 else road['height']) for axis in (0,1)];errors.append(dict(vertex=i,source_texel_residual=diff))
 checks.append(dict(surface=road['surface'],source_vertices=len(vertices),anchors=list(anchors),coefficients=coeff,max_source_texel_residual=max(abs(x) for row in errors for x in row['source_texel_residual']),residuals=errors))
report=dict(result='MEASURED',checks=checks,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Affine UV plane determined by first noncollinear source-world corners, remaining source corners checked. Diagnostic only; no screen coordinates or original polygon matching, no replacement UV coefficients used by renderer. Nonzero residuals imply triangulation-independent affine mapping cannot exactly represent all source corner UVs.')
(p/'stable-road-source-uv-planarity.json').write_text(json.dumps(report,indent=2));print([{k:v for k,v in c.items() if k not in ('residuals','coefficients')} for c in checks])

import ctypes as C,json,struct
from pathlib import Path
from owned_motion_pairs import records
from owned_source_face_determinant_candidate import SourceFaceDeterminants
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str((p/'owned-sky-source-face-candidate.dll').resolve()));table=(C.c_uint32*32768)(*struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]));d.nfs_model_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_int,C.c_int,C.c_void_p,C.c_void_p];d.nfs_model_polygon_classify.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
def classification(points,indices,rect):
 raw=struct.pack('<'+'h'*len(points)*2,*(v for pair in points for v in pair));ids=(C.c_uint16*len(indices))(*indices);bounds=(C.c_int32*4)(*rect);out=C.c_int();assert d.nfs_model_polygon_classify(raw,len(points),ids,len(indices),bounds,C.byref(out))==1;return out.value
checks=0;rejected=0;crossing_disagreements=0
for frame in report['wall_diagnostic_frames']:
 for row in records(Path(frame['regenerated']).read_bytes())['records']:
  if row['kind']!=3:continue
  b=row['blocks'];n=len(b[4])//6;out=C.create_string_buffer(n*4);scale=struct.unpack_from('<I',b[0],64)[0];center=struct.unpack_from('<2h',b[3],8);assert d.nfs_model_project(bytes(b[2]),bytes(b[4]),n,scale,*center,table,out)==1;points=tuple(struct.iter_unpack('<2h',out.raw));rect=struct.unpack('<4i',b[9]);at=0
  for count in b[5]:
   ids=struct.unpack_from('<'+str(count)+'H',b[6],at*2);at+=count;cl=classification(points,ids,rect);checks+=1;rejected+=cl==4
   xs=[points[i][0] for i in ids];ys=[points[i][1] for i in ids];overlap=not(max(xs)<rect[0] or min(xs)>=rect[2] or max(ys)<rect[1] or min(ys)>=rect[3]);crossing_disagreements+=overlap!=(cl!=4)
synthetic=[]
for points,rect in ((((0,0),(10,0),(10,10),(0,10)),(4,4,6,6)),(((0,0),(1,0),(0,1)),(0,0,1,1)),(((1,0),(1,1),(1,2)),(0,0,1,3))):
 cl=classification(points,tuple(range(len(points))),rect);synthetic.append(dict(points=points,rect=rect,classification=cl))
assert [x['classification'] for x in synthetic]==[4,3,4]
local=struct.pack('<9h',0,0,0,1,0,0,0,1,0);depths=[]
for z in (-1,0,1,63,64,24576,24577):
 matrix=(16384,0,0,0,16384,0,0,0,16384,0,0,z);out=C.create_string_buffer(12);original=d.nfs_model_project(struct.pack('<12i',*matrix),local,3,128,120,87,table,out)
 candidate=SourceFaceDeterminants.__new__(SourceFaceDeterminants);candidate.vertices=((0,0,0),(1,0,0),(0,1,0));candidate.faces=((0,1,2),);m=tuple(v/16384 if i<9 else float(v) for i,v in enumerate(matrix))
 try:candidate.ideal(m,128,(120,87));supported=True
 except ValueError:supported=False
 depths.append(dict(depth=z,original_accepts=bool(original),candidate_supports=supported))
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-rectangle-depth-contract-20261007');root.mkdir(exist_ok=True);result=dict(result='MEASURED_ORIGINAL_BOUNDARY_CONTRACT',captured_faces=checks,original_rectangle_rejected=rejected,conservative_overlap_disagreements=crossing_disagreements,synthetic_rectangles=synthetic,depth_cases=depths,scope='Original integer rectangle/depth source contracts; candidate depth coverage limitations explicit. Not fractional rectangle implementation or GPU clipping proof.');(root/'tests.json').write_text(json.dumps(result,indent=2));(root/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))

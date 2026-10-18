import ctypes as C,struct,json,math,random
from pathlib import Path
from owned_model_projection_cells_candidate import project_camera_cells
p=Path('work/camera');table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]);table_c=(C.c_uint32*len(table))(*table);d=C.CDLL(str((p/'owned-sky-source-face-candidate.dll').resolve()));d.nfs_model_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_int,C.c_int,C.c_void_p,C.c_void_p];random.seed(107);checks=0;maximum=0
for depth in (0,1,2,31,63,64,65,127,1024,24575,24576):
 for _ in range(64):
  x,y=random.randint(-32000,32000),random.randint(-32000,32000);scale=random.choice((1,64,128,256,10000));center=(random.randint(-100,100),random.randint(-100,100));m=(16384,0,0,0,16384,0,0,0,16384,x,y,depth);out=C.create_string_buffer(4)
  assert d.nfs_model_project(struct.pack('<12i',*m),bytes(6),1,scale,*center,table_c,out)==1;expected=struct.unpack('<2h',out.raw);actual=project_camera_cells((x,y,depth),scale,center,table);error=max(abs(a-b) for a,b in zip(actual,expected));maximum=max(maximum,error);assert error==0;checks+=1
interior_checks=0
for depth in (0,.25,.5,.75,1,31.5,63.5,63.999999,64,64.000001,24575.5,24576):
 actual=project_camera_cells((12.25,-7.75,depth),128,(120,87),table);assert all(math.isfinite(v) for v in actual);interior_checks+=1
near=project_camera_cells((12.25,-7.75,63.999999999),128,(120,87),table);far=project_camera_cells((12.25,-7.75,64.000000001),128,(120,87),table);seam=max(abs(a-b) for a,b in zip(near,far));assert seam<1e-6
for point in ((0,0,-1),(0,0,24577),(0,0,float('nan'))):
 try:project_camera_cells(point,128,(120,87),table)
 except ValueError:pass
 else:raise AssertionError('Invalid depth accepted')
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-camera-cell-projection-20261007');root.mkdir(exist_ok=True);result=dict(result='PASS_ORIGINAL_CAMERA_CELL_PROJECTION',integer_checks=checks,max_error=maximum,finite_fractional_depth_checks=interior_checks,depth64_seam_error=seam,scope='Recovered original integer camera cells including zero/near depth, finite trilinear extension and bounded seam. Signed16 wrap is preserved at cells; fractional deformation/near-clipped face visibility/GPU/live motion not yet verified.');(root/'tests.json').write_text(json.dumps(result,indent=2));(root/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))

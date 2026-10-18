from pathlib import Path
import hashlib,json
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-gpu-tests'
original=here/'test_sky_gpu.py';text=original.read_text().replace("NFSUG-pc-sky-gpu-tests","NFSUG-pc-recipe-gpu-tests").replace("source-sky-gpu.dll","recipe-gpu.dll").replace("sky-gpu-build-report.json","recipe-gpu-build-report.json").replace("receipt['extension_sha256']", "receipt['source_sha256']")
anchor="assert draw_scene(g,scene,3840,2160,3240,2160,second,len(second)) and second.raw==first.raw"
assert text.count(anchor)==1
injection='''# Recipe submission between complete-scene draws checks shared shader/upload state.
 class RecipeBlock(C.Structure):_fields_=[('data',P),('bytes',S)]
 values=[b'\\0']*15;matbytes=bytearray(48);matbytes[36:40]=bytes([2,0,4,0]);values[4]=bytes(matbytes);values[8]=bytes([1])*16
 buffers=[C.create_string_buffer(v) for v in values];blocks=(RecipeBlock*15)(*[RecipeBlock(C.cast(v,P),len(values[j])) for j,v in enumerate(buffers)])
 rm=fn(d,'nf_pc_recipe_material_decode',[U,P,U,S],P)(2,blocks,15,65536);assert rm
 coords=(C.c_double*24)(20,20,128,.1,.1,1,220,20,128,.8,.1,1,220,140,128,.8,.8,1,20,140,128,.1,.8,1)
 rmesh=fn(d,'nf_pc_recipe_mesh_ring',[P,U,S],P)(coords,4,65536);assert rmesh
 # The intervening sky check resized the target to240x160.
 assert fn(d,'nf_pc_scene_gpu_render_recipe',[P,P,P,P,S,U,U,P])(g,rmesh,rm,pal.tobytes(),163840,240,160,(U*4)(0,240,0,160))
 fn(d,'nf_pc_recipe_mesh_free',[P],None)(rmesh);fn(d,'nf_pc_recipe_material_free',[P],None)(rm)
 '''
text=text.replace(anchor,injection+anchor)
exec(compile(text,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
r=dict(result='PASS_EXISTING_SKY_AND_FULL_SCENE_AFTER_RECIPE_SUBMISSION',wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),original_test_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),executed_test_sha256=hashlib.sha256(text.encode()).hexdigest(),recipe_submission_between_endpoint_draws=True)
(out/'recipe-regression-wrapper-report.json').write_text(json.dumps(r,indent=2));print(r['result'])

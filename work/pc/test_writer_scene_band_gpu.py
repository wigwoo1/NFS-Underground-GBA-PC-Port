from pathlib import Path
import json,hashlib
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-band-tests'
original=here/'test_writer_scene_gpu.py';text=original.read_text().replace('NFSUG-pc-writer-scene-tests','NFSUG-pc-writer-band-tests').replace('nf_pc_scene_gpu_render_scene_writer','nf_pc_scene_gpu_render_scene_writer_banded').replace('-real-palette-writer-textures-4k.png','-banded-real-palette-writer-textures-4k.png')
# Inner original test is loaded dynamically; inject exact destination-band oracle.
anchor='env[\'bound_draw\']=bound_draw';assert text.count(anchor)==1
# At this point variable text inside the executed wrapper is its transformed GPU test.
replacement="""env['bound_draw']=bound_draw
inner_anchor=\"       assert geo['read'](gpu,pixels,len(pixels));actual=\"
assert text.count(inner_anchor)==1
text=text.replace(inner_anchor,\"       display_rows=(((ah-np.arange(ah,dtype=np.int64))*2-1)*80)//ah;outside=(display_rows<selection[1])|(display_rows>=selection[2]);expected[np.nonzero(outside)[0],:aw]=0\\n\"+inner_anchor)
text=text.replace(\"diff=np.any(actual!=expected,axis=2);\",\"assert not actual[np.nonzero(outside)[0],:aw].any();diff=np.any(actual!=expected,axis=2);\")
"""
text=text.replace(anchor,replacement)
exec(compile(text,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
r=dict(result='PASS_REAL_SCENE_WRITER_DESTINATION_BANDS',source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),executed_sha256=hashlib.sha256(text.encode()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),gpu_dll_sha256=hashlib.sha256((out/'recipe-gpu.dll').read_bytes()).hexdigest(),outside_owner_band_pixels_strictly_empty=True,full_scene_60fps=False)
(out/'writer-scene-band-wrapper-report.json').write_text(json.dumps(r,indent=2));print(r['result'])

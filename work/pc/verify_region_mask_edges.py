from pathlib import Path
import json,hashlib
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-region-mask-edges-tests';rows=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['test_region_mask_gpu.py','test_region_mask_guards.py','test_region_mask_near_gpu.py','test_region_mask_regression.py']:
 path=here/name;source=path.read_text();text=source.replace('NFSUG-pc-region-mask-tests','NFSUG-pc-region-mask-edges-tests')
 if name=='test_region_mask_near_gpu.py':
  old="boot=original.read_text().split('try:\\n for name,h in cr[')[0]";new=old+".replace('NFSUG-pc-region-mask-tests','NFSUG-pc-region-mask-edges-tests')";assert text.count(old)==1;text=text.replace(old,new)
 executed=out/('executed-'+name);executed.write_text(text)
 print('RUN',name,flush=True);exec(compile(text,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
 rows.append(dict(test=name,original_sha256=sha(path),executed_sha256=sha(executed)));(out/'edge-regression-dispatch-report.json').write_text(json.dumps(dict(result='RUNNING_DIRECT_EDGE_REGRESSIONS',tests=rows,script_sha256=sha(Path(__file__))),indent=2))
r=dict(result='PASS_DIRECT_PROJECTIVE_EDGE_ALL_REGRESSIONS',tests=rows,script_sha256=sha(Path(__file__)),gpu_dll_sha256=sha(out/'recipe-gpu.dll'),cpu_dll_sha256=sha(out/'recipe-regions.dll'),full_scene_60fps=False);(out/'edge-regression-dispatch-report.json').write_text(json.dumps(r,indent=2));print(r['result'])

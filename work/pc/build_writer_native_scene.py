from pathlib import Path
import json,hashlib,os,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-writer-shared-tests';out=base/'NFSUG-pc-writer-native-scene-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((prior/'recipe-gpu-build-report.json').read_text())
for group in ['source_sha256','staged_sha256']:
 for p,h in b[group].items():assert sha(p)==h,p
assert sha(prior/'recipe-gpu.dll')==b['dll_sha256']
for name in ['recipe-regions.dll','region-build-report.json','sky_composition.inc','writer_band_generated.inc','writer_shared_generated.c','writer_shared_address_map.c','scene_gpu_writer_shared.c']:shutil.copyfile(prior/name,out/name)
partition=out/'recipe_regions_partition.c';text=(here/'recipe_regions.c').read_text().split('int nf_pc_recipe_regions_ring(')[0];partition.write_text(text)
args=[a.replace(str(prior),str(out)) for a in b['command']];args=[str(here/'writer_native_store.c') if Path(a).name=='writer_shared_store.c' else a for a in args];args[1:1]=[str(here/'writer_native_scene.c'),str(partition)];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
b.update(result='BUILT_NATIVE_OWNED_WRITER_SCENE_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)),previous_gpu_sha256=sha(prior/'recipe-gpu.dll'),previous_receipt_sha256=sha(prior/'recipe-gpu-build-report.json'))
for n in ['writer_native_scene.h','writer_native_scene.c','writer_native_store.c','recipe_regions.c','recipe_regions.h']:b['source_sha256'][str(here/n)]=sha(here/n)
b['staged_sha256']={str(out/Path(p).name):sha(out/Path(p).name) for p in b['staged_sha256']};b['staged_sha256'][str(partition)]=sha(partition);(out/'recipe-gpu-build-report.json').write_text(json.dumps(b,indent=2));print('STRICT_NATIVE_WRITER_SCENE_BUILD_PASS',b['dll_sha256'])

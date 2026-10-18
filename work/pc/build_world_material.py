from pathlib import Path
import subprocess,sys,os,json,hashlib,uuid,ctypes as C
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-material-tests';out.mkdir(exist_ok=True);jdk=base/'android-tools/jdk-21.0.12.1+1/bin';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prerequisite=base/'NFSUG-pc-world-mesh-tests/world-mesh-build-report.json';prior=json.loads(prerequisite.read_text());native=['source_frame.c','source_frame.h','source_world.c','source_world.h','source_road.c','source_road.h','world_mesh.c','world_mesh.h']
for n in native:assert sha(source/n)==prior['source_sha256'][n],('Prerequisite changed',n)
for n,digest in prior['input_sha256'].items():assert sha(base/'NFSUG-pc-world-mesh-tests/inputs'/n)==digest
native+=['world_material.c','world_material.h'];cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(source/n) for n in native if n.endswith('.c')]+['-o',str(out/'world-material.dll'),'-lm'];subprocess.run(cmd,check=True,env=env)
subprocess.run([sys.executable,str(source/'make_world_material_inputs.py')],check=True,env=env)
java=root/'work/android/java/org/codex/nfsugpreview';classes=out/('classes-'+uuid.uuid4().hex[:8]);subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcWorldMaterialReferenceExport.java')],check=True,env=env)
subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.PcWorldMaterialReferenceExport',str(out/'inputs'),str(out/'references')],check=True,env=env)
subprocess.run([sys.executable,str(source/'test_world_material.py')],check=True,env=env);r=json.loads((out/'world-material-report.json').read_text())
assert r['worlds']==38 and r['actual_surfaces']==388 and r['accepted']==406 and r['unsupported_rejected']==3 and r['invalid_alpha_rejected']==2 and r['upload_variants']==631 and r['compared_upload_bytes']==22922872 and r['compared_shade_columns']==331870 and len(r['modes'])==11
assert r['all_variants_curves_columns_byte_identical_to_java'] and r['one_expanded_buffer_reused'] and r['world_release_lifetime_verified']
for n,digest in r['source_sha256'].items():assert sha(source/n)==digest
assert r['test_sha256']==sha(source/'test_world_material.py') and r['dll_sha256']==sha(out/'world-material.dll')
java_sources={}
for file in classes.rglob('*.class'):
 name=file.name.split('$')[0].split('.')[0]+'.java';path=source/name if name=='PcWorldMaterialReferenceExport.java' else java/name;java_sources[str(path)]=sha(path)
exports=['nf_pc_world_material','nf_pc_world_material_free','nf_pc_world_material_info','nf_pc_world_material_image','nf_pc_world_material_curve','nf_pc_world_material_columns']
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'world-material.dll'))
for n in exports:assert getattr(dll,n)
names=native+['PcWorldMaterialReferenceExport.java','make_world_material_inputs.py','test_world_material.py','build_world_material.py']
b=dict(result='PASS_PC_WORLD_MATERIAL_INTEGRATION',command=cmd,source_sha256={n:sha(source/n) for n in names},java_oracle_sources=java_sources,input_sha256={p.name:sha(p) for p in (out/'inputs').glob('*.nsp')},reference_sha256={p.name:sha(p) for p in (out/'references').glob('*.material')},prerequisite_receipt_sha256=sha(prerequisite),dll_sha256=sha(out/'world-material.dll'),exports=exports,actual_surfaces=388,accepted_materials=406,unsupported_rejected=3,invalid_alpha_rejected=2,upload_variants=631,compared_upload_bytes=22922872,compared_shade_columns=331870,one_expanded_buffer_reused=True,world_release_lifetime_verified=True,native_shade_curve_matches_established_reader=True,original_gba_quantized_columns_claimed=False,gpu_world_drawing=False,full_scene=False,playable_native_release=False,full_scene_60fps=False,report_sha256=sha(out/'world-material-report.json'))
(out/'world-material-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','source_sha256','java_oracle_sources','input_sha256','reference_sha256']},indent=2))

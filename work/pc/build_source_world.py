from pathlib import Path
import subprocess,sys,os,json,hashlib,uuid,ctypes as C
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-tests';out.mkdir(exist_ok=True);jdk=base/'android-tools/jdk-21.0.12.1+1/bin';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(source/'verify_source_frame.py')],check=True,env=env)
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared',str(source/'source_frame.c'),str(source/'source_world.c'),'-o',str(out/'source-world.dll'),'-lm'];subprocess.run(cmd,check=True,env=env)
subprocess.run([sys.executable,str(source/'make_world_synthetic.py')],check=True,env=env)
java=root/'work/android/java/org/codex/nfsugpreview';classes=out/('classes-'+uuid.uuid4().hex[:8]);subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcWorldReferenceExport.java')],check=True,env=env)
subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.PcWorldReferenceExport',str(base/'NFSUG-background-owner-api-fixtures'),str(out/'references'),str(out/'synthetic')],check=True,env=env)
java_sources={}
for file in classes.rglob('*.class'):
 name=file.name.split('$')[0].split('.')[0]+'.java';path=source/name if name=='PcWorldReferenceExport.java' else java/name;java_sources[str(path)]=sha(path)
subprocess.run([sys.executable,str(source/'test_source_world_live.py')],check=True,env=env)
a=json.loads((out/'world-report.json').read_text());b=json.loads((out/'world-live-report.json').read_text())
assert a['surfaces']==399 and a['owners']==28 and a['commands']==439 and a['malformed_rejected']==39 and len(a['modes'])==11
assert b['surfaces']==388 and b['owners']==17 and b['original_prefix_frames']==296 and b['world_survives_frame_release_and_core_close'] and b['decoder_never_steps_logic']
for n,h in a['source_sha256'].items():assert sha(source/n)==h
assert a['test_sha256']==sha(source/'test_source_world.py') and b['test_sha256']==sha(source/'test_source_world_live.py')
assert a['dll_sha256']==b['dll_sha256']==sha(out/'source-world.dll')
exports=['nf_pc_world_decode','nf_pc_source_world','nf_pc_world_free','nf_pc_world_info','nf_pc_world_surface_info','nf_pc_world_surface_buffer','nf_pc_world_buffer','nf_pc_world_command']
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-world.dll'))
for name in exports:assert getattr(dll,name)
names=['source_frame.c','source_frame.h','source_world.c','source_world.h','test_source_world.py','test_source_world_live.py','make_world_synthetic.py','PcWorldReferenceExport.java','build_source_world.py']
r=dict(result='PASS_PC_SOURCE_WORLD_INTEGRATION',command=cmd,source_sha256={n:sha(source/n) for n in names},java_oracle_sources=java_sources,source_reference_inputs={str(p):sha(p) for p in (base/'NFSUG-background-owner-api-fixtures').glob('source-race-background-*.nrb')},synthetic_model_input_sha256=sha(base/'NFSUG-pc-model-tests/references/synthetic-near.model'),reference_sha256={p.name:sha(p) for p in (out/'references').iterdir() if p.is_file()},dll_sha256=sha(out/'source-world.dll'),core_sha256=b['core_sha256'],exports=exports,actual_surfaces=388,synthetic_material_modes=11,component_buffer_bytes=a['compared_buffer_bytes'],malformed_rejected=39,original_prefix_frames=296,projection_implemented=False,gpu_world_drawing=False,full_scene=False,playable_native_release=False,full_scene_60fps=False,reports_sha256={n:sha(out/n) for n in ['world-report.json','world-live-report.json']})
(out/'world-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['command','source_sha256','java_oracle_sources','source_reference_inputs','reference_sha256']},indent=2))

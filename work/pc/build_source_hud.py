from pathlib import Path
import os,sys,subprocess,json,hashlib,uuid,ctypes as C
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-hud-tests';out.mkdir(exist_ok=True);env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');jdk=base/'android-tools/jdk-21.0.12.1+1/bin';java=root/'work/android/java/org/codex/nfsugpreview'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=base/'NFSUG-android-hud-candidates-local/hud-candidates-host-report.json';receipt=json.loads(prior.read_text())
for name,digest in receipt['reference_sha256'].items():assert sha(root/'work/camera'/name)==digest
for name,digest in receipt['source_sha256'].items():assert sha(root/'work/android'/name.replace('\\','/'))==digest
assert sha(base/'NFSUG-android-hud-candidates-local/hud-candidates-cases.bin')==receipt['fixture_sha256']
subprocess.run([sys.executable,str(source/'verify_source_frame.py')],check=True,env=env)
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared',str(source/'source_frame.c'),str(source/'source_hud.c'),str(root/'work/camera/obj_tile.c'),'-o',str(out/'source-hud.dll')];subprocess.run(cmd,check=True,env=env)
classes=out/('classes-'+uuid.uuid4().hex[:8]);subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcHudReferenceExport.java'),str(root/'work/android/tests/org/codex/nfsugpreview/HudCandidatesTest.java')],check=True,env=env)
subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.HudCandidatesTest',str(base/'NFSUG-android-hud-candidates-local/hud-candidates-cases.bin')],check=True,env=env)
subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.PcHudReferenceExport',str(base/'NFSUG-background-owner-api-fixtures'),str(base/'NFSUG-android-hud-frame-local'),str(out/'references'),str(base/'NFSUG-android-hud-effect-local/synthetic.nab')],check=True,env=env)
subprocess.run([sys.executable,str(source/'test_source_hud.py')],check=True,env=env)
r=json.loads((out/'hud-report.json').read_text());assert r['frames']==12 and r['rows']==1920 and r['candidate_cases']==1881 and r['original_prefix_frames']==296 and r['all_planes_parameters_exact'] and r['owned_after_core_close'] and r['dll_sha256']==sha(out/'source-hud.dll')
java_sources={}
for file in classes.rglob('*.class'):
 name=file.name.split('$')[0].split('.')[0]+'.java';p=source/name if name=='PcHudReferenceExport.java' else root/'work/android/tests/org/codex/nfsugpreview'/name if name=='HudCandidatesTest.java' else java/name;java_sources[str(p)]=sha(p)
exports=['nf_pc_hud_row','nf_pc_hud_decode_layers','nf_pc_source_hud','nf_pc_hud_free','nf_pc_hud_info','nf_pc_hud_buffer']
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-hud.dll'))
for name in exports:assert getattr(dll,name)
b=dict(result='PASS_PC_SOURCE_HUD',command=cmd,source_sha256={n:sha(source/n) for n in ['source_frame.c','source_frame.h','source_hud.c','source_hud.h','PcHudReferenceExport.java','test_source_hud.py','build_source_hud.py']},reused_camera_source_sha256={n:sha(root/'work/camera'/n) for n in ['obj_tile.c','obj_tile.h']},java_oracle_sources=java_sources,reference_sha256={p.name:sha(p) for p in (out/'references').glob('*') if p.is_file()},fixture_sha256={str(p):sha(p) for p in [base/'NFSUG-android-hud-candidates-local/hud-candidates-cases.bin',base/'NFSUG-android-hud-effect-local/synthetic.nab']+[p for pattern in ['source-race-background-*.nrb'] for p in (base/'NFSUG-background-owner-api-fixtures').glob(pattern)]+[base/f'NFSUG-android-hud-frame-local/{name}.nab' for name in ['whole','split']]},prior_candidate_receipt_sha256=sha(prior),dll_sha256=sha(out/'source-hud.dll'),core_sha256=r['core_sha256'],report_sha256=sha(out/'hud-report.json'),exports=exports,frames=12,rows=1920,candidate_cases=1881,original_prefix_frames=296,gpu_submitted=False,playable_native_release=False,full_scene_60fps=False)
(out/'hud-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','source_sha256','reused_camera_source_sha256','java_oracle_sources','reference_sha256','fixture_sha256']},indent=2))

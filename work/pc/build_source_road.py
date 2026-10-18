from pathlib import Path
import subprocess,sys,os,json,hashlib,uuid,ctypes as C
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-road-math-tests';out.mkdir(exist_ok=True);jdk=base/'android-tools/jdk-21.0.12.1+1/bin';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
commands=[]
for name,options in [('source-road.dll',['-O2']),('source-road-trap.dll',['-O1','-ftrapv'])]:
 cmd=['C:/msys64/mingw64/bin/gcc.exe',*options,'-Wall','-Wextra','-Werror','-ffp-contract=off','-shared',str(source/'source_road.c'),'-o',str(out/name),'-lm'];subprocess.run(cmd,check=True,env=env);commands.append(cmd)
java=root/'work/android/java/org/codex/nfsugpreview';classes=out/('classes-'+uuid.uuid4().hex[:8]);subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcRoadMathReferenceExport.java')],check=True,env=env)
subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.PcRoadMathReferenceExport',str(base/'NFSUG-background-owner-api-fixtures'),str(out/'references')],check=True,env=env)
for name in ['source-road.dll','source-road-trap.dll']:subprocess.run([sys.executable,str(source/'test_source_road.py'),name],check=True,env=env)
a=json.loads((out/'road-math-report.json').read_text());b=json.loads((out/'road-math-trap-report.json').read_text())
for r,name in [(a,'source-road.dll'),(b,'source-road-trap.dll')]:
 assert r['cases']==1187 and r['compared_double_values']==5840 and r['captured_road_rings']==86 and r['invalid_cases_rejected']==15 and r['all_outputs_byte_identical_to_java']
 assert r['test_sha256']==sha(source/'test_source_road.py') and r['dll_sha256']==sha(out/name)
 for n,digest in r['source_sha256'].items():assert sha(source/n)==digest
java_sources={}
for file in classes.rglob('*.class'):
 name=file.name.split('$')[0].split('.')[0]+'.java';path=source/name if name=='PcRoadMathReferenceExport.java' else java/name;java_sources[str(path)]=sha(path)
exports=['nf_pc_road_camera','nf_pc_road_vertex','nf_pc_road_near','nf_pc_road_clip','nf_pc_road_project_point','nf_pc_road_project_near','nf_pc_road_project_ring']
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-road.dll'))
for name in exports:assert getattr(dll,name)
r=dict(result='PASS_PC_SOURCE_ROAD_MATH_INTEGRATION',commands=commands,source_sha256={n:sha(source/n) for n in ['source_road.c','source_road.h','PcRoadMathReferenceExport.java','test_source_road.py','build_source_road.py']},java_oracle_sources=java_sources,source_reference_inputs={str(p):sha(p) for p in (base/'NFSUG-background-owner-api-fixtures').glob('source-race-background-*.nrb')},reference_sha256={p.name:sha(p) for p in (out/'references').iterdir() if p.is_file()},dll_sha256={n:sha(out/n) for n in ['source-road.dll','source-road-trap.dll']},exports=exports,cases_per_build=1187,compared_double_values_per_build=5840,captured_road_rings=86,invalid_cases_per_build=15,signed_overflow_trap_build_passed=True,ubsan_verified=False,ubsan_limitation='Installed Windows GCC has no libubsan; no sanitizer result claimed.',full_world_mesh=False,gpu_world_drawing=False,full_scene=False,playable_native_release=False,full_scene_60fps=False,reports_sha256={n:sha(out/n) for n in ['road-math-report.json','road-math-trap-report.json']})
(out/'road-math-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['commands','source_sha256','java_oracle_sources','source_reference_inputs','reference_sha256']},indent=2))

from pathlib import Path
import hashlib,json,os,shutil,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');parent=base/'NFSUG-Android-Context-Refresh-20261017/native';out=base/'NFSUG-Host3519-Diagnostic-20261017';out.mkdir(exist_ok=True);src=out/'source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copytree(parent/'source',src,dirs_exist_ok=True);header=src/'camera/live_scene.h';text=header.read_text();original=text
names=['nf_native_scene_rejection_detail','nf_native_scene_first_bad','nf_native_model_rejection_detail','nf_native_scene_model_rejection_visits']
for name in names:
 needle='API void '+name+'(';assert text.count(needle)==1;text=text.replace(needle,'__declspec(dllexport) void '+name+'(')
assert all(text.count('__declspec(dllexport) void '+name+'(')==1 for name in names);header.write_text(text)
restored=text
for name in names:restored=restored.replace('__declspec(dllexport) void '+name+'(','API void '+name+'(')
assert restored==original
provenance=json.loads((parent/'source-provenance.json').read_text());cpu=provenance['cpu_sources'];package=root/'work/v2/package/NFSUG-Native-Renderer-source'
lib=out/'capture-diagnostic-host.dll'
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-shared','-ffunction-sections','-fdata-sections','-DBUILD_STATIC','-DM_CORE_GBA','-DUSE_DEBUGGERS','-DNF_VISIBILITY_CAPTURE','-DNF_VISIBILITY_QUEUE_CAPACITY=64','-DNF_ROAD_ATTRIBUTE_CORRECTION','-DNF_PACKET_NO_FILES','-D_GNU_SOURCE','-I'+str(src),'-I'+str(src/'camera'),'-I'+str(package/'deps/mgba-0.10.5/include'),'-I'+str(package/'build/mgba-nfsug/include'),str(src/'nfsug_android_core.c'),str(src/'observer.c'),str(src/'native_span.c')]+[str(src/'camera'/name) for name in cpu]+[str(package/'build/mgba-nfsug/libmgba.a'),'-lws2_32','-lshlwapi','-lole32','-luuid','-lm','-Wl,--gc-sections','-o',str(lib)]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'compile.log').open('w') as log:subprocess.run(cmd,check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
report=dict(result='BUILT_HOST_EXISTING_REJECTION_METADATA_EXPORTS',diagnostic_only=True,logic_changed=False,parent_host_sha256=sha(parent/'capture-host.dll'),parent_provenance_sha256=sha(parent/'source-provenance.json'),original_header_sha256=sha(parent/'source/camera/live_scene.h'),staged_header_sha256=sha(header),library_sha256=sha(lib),exported_existing_functions=names,compile_command=cmd,factory_sha256=sha(Path(__file__)))
(out/'build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['library_sha256'])

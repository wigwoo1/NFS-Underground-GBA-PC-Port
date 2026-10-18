"""Isolated PC serialization experiment; baseline core/Android staging untouched."""
from pathlib import Path
import os,sys,subprocess,shutil,json,hashlib,re
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-android-background-jni-native-local';out=base/'NFSUG-pc-owned-assembly-core-tests';out.mkdir(exist_ok=True);source=out/'source';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(here/'verify_source_frame.py')],check=True,env=env)
assert sha(baseline/'capture-host.dll')=='137fbe3532ed7a89979315a69693de1636b80ca7de14b2c97ad8694633f40b06'
shutil.copytree(baseline/'source',source,dirs_exist_ok=True);path=source/'observer.c';text=path.read_text(encoding='utf-8');original=text
def replace_function(name,helper,prepare,finish):
 global text
 signature=f'size_t {name}(uint64_t epoch,unsigned refresh,void*out,size_t capacity)';start=text.index(signature);end=text.index('\n}',start)+2;old=text[start:end];new=old.replace(signature,f'static size_t {helper}(uint64_t epoch,unsigned refresh,uint8_t**owned)',1);new=new.replace('{\n','{\n *owned=NULL;\n',1)
 for before,after in prepare:
  assert new.count(before)==1,(name,before);new=new.replace(before,after,1)
 before,after=finish;assert new.count(before)==1,(name,before);new=new.replace(before,after,1);assert not re.search(r'\b(out|capacity)\b',new),(name,'Unconverted caller output')
 wrapper=f'''\n{signature}{{
 uint8_t*packet=NULL;size_t bytes={helper}(epoch,refresh,&packet);if(!bytes)return 0;
 if(out&&capacity<bytes){{free(packet);return 0;}}if(out)memcpy(out,packet,bytes);free(packet);return bytes;
}}'''
 text=text[:start]+new+wrapper+text[end:]
replace_function('nf_android_observer_bundle','android_bundle_owned',[
 ('if(!out)return total;if(capacity<total)return 0;','')],
 ('if(ok)memcpy(out,copy,total);free(copy);return ok?total:0;','if(!ok){free(copy);return 0;}*owned=copy;return total;'))
replace_function('nf_android_observer_sky_scene','android_sky_scene_owned',[
 ('size_t scene_bytes=nf_android_observer_bundle(epoch,refresh,NULL,0);if(!scene_bytes)return 0;\n uint8_t*scene=malloc(scene_bytes);if(!scene)return 0;if(nf_android_observer_bundle(epoch,refresh,scene,scene_bytes)!=scene_bytes){free(scene);return 0;}','uint8_t*scene=NULL;size_t scene_bytes=android_bundle_owned(epoch,refresh,&scene);if(!scene_bytes)return 0;'),
 ('if(out&&capacity<bytes){free(scene);return 0;}','')],
 ('if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);if(out)memcpy(out,copy,bytes);}else ok=0;free(copy);free(scene);return ok?bytes:0;','if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);*owned=copy;}else{free(copy);ok=0;}free(scene);return ok?bytes:0;'))
replace_function('nf_android_observer_background_scene','android_background_scene_owned',[
 ('size_t sn=nf_android_observer_sky_scene(epoch,refresh,NULL,0);if(!sn||sn>64u*1024u*1024u-128-2*76880)return 0;\n uint8_t*sky=malloc(sn);if(!sky)return 0;if(nf_android_observer_sky_scene(epoch,refresh,sky,sn)!=sn){free(sky);return 0;}','uint8_t*sky=NULL;size_t sn=android_sky_scene_owned(epoch,refresh,&sky);if(!sn)return 0;if(sn>64u*1024u*1024u-128-2*76880){free(sky);return 0;}'),
 ('if(count<1||count>2||(out&&capacity<bytes))','if(count<1||count>2)')],
 ('if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);if(out)memcpy(out,copy,bytes);}else ok=0;free(copy);free(sky);return ok?bytes:0;','if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);*owned=copy;}else{free(copy);ok=0;}free(sky);return ok?bytes:0;'))
path.write_text(text,encoding='utf-8');provenance=json.loads((baseline/'source-provenance.json').read_text());package=root/'work/v2/package/NFSUG-Native-Renderer-source'
args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-shared','-ffunction-sections','-fdata-sections','-DBUILD_STATIC','-DM_CORE_GBA','-DUSE_DEBUGGERS','-DNF_VISIBILITY_CAPTURE','-DNF_VISIBILITY_QUEUE_CAPACITY=64','-DNF_ROAD_ATTRIBUTE_CORRECTION','-DNF_PACKET_NO_FILES','-D_GNU_SOURCE','-I'+str(source),'-I'+str(source/'camera'),'-I'+str(package/'deps/mgba-0.10.5/include'),'-I'+str(package/'build/mgba-nfsug/include'),str(source/'nfsug_android_core.c'),str(path),str(source/'native_span.c')]+[str(source/'camera'/n) for n in provenance['cpu_sources']]+[str(package/'build/mgba-nfsug/libmgba.a'),'-lws2_32','-lshlwapi','-lole32','-luuid','-lm','-Wl,--gc-sections','-o',str(out/'capture-host.dll')]
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
assert (baseline/'source/observer.c').read_text(encoding='utf-8')==original
inputs={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()};assert all(sha(source/name)==sha(baseline/'source'/name) for name in inputs if name!='observer.c')
b=dict(result='BUILT_OWNED_ASSEMBLY_CORE_TESTS_PENDING',command=args,baseline_core_sha256=sha(baseline/'capture-host.dll'),baseline_observer_sha256=sha(baseline/'source/observer.c'),observer_sha256=sha(path),staged_input_sha256=inputs,mgba_static_library_sha256=sha(package/'build/mgba-nfsug/libmgba.a'),script_sha256=sha(Path(__file__)),core_sha256=sha(out/'capture-host.dll'),changed_functions=['nf_android_observer_bundle','nf_android_observer_sky_scene','nf_android_observer_background_scene'],game_logic_changed=False,android_packages_changed=False)
(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','staged_input_sha256']},indent=2))

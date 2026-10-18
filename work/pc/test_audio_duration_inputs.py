from pathlib import Path
import ctypes as C,hashlib,json,os,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');source=root/'work/pc';base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-audio-duration-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
current=(source/'live_host.c').read_text();before=root/'outputs/nfsug-native-renderer/camera-research/pc-audio-duration-20261017/before/live_host.c';old=before.read_text()
def function(text,signature):
 a=text.index(signature);start=text.index('{',a);depth=0
 for i in range(start,len(text)):
  if text[i]=='{':depth+=1
  elif text[i]=='}':
   depth-=1
   if not depth:return text[a:i+1]
 raise AssertionError(signature)
marker=' int16_t pcm[8192]';a=function(current,'static void audio_drain(');b=function(old,'static void audio_drain(')
assert a[a.index(marker):a.index('\n /*',a.index(marker))]==b[b.index(marker):b.index('\n /*',b.index(marker))]
assert function(current,'static void audio_reset(')==function(old,'static void audio_reset(').replace('static void audio_reset(void){','static void audio_reset(void){nf_audio_clock_reset(&audio_clock);')
component=out/'report.json';proof=json.loads(component.read_text());assert proof['source_sha256']==sha(source/'live_host.c') and proof['rows']['candidate']['measured']['empty_events']==0
assert 'PASS_AUDIO_CLOCK_DURATION_RESET_INVALID_NONMONOTONIC_WRAP' in (out/'clock-run.log').read_text()
scripted=function(current,'static unsigned scripted_input(');assert scripted==function(old,'static unsigned scripted_input(')
code='#include <stdint.h>\n'+scripted+'\n__declspec(dllexport) unsigned keys(uint64_t segment,int mode){return scripted_input(segment,mode);}\n'
path=out/'duration-input-test.c';path.write_text(code);dll=out/'duration-input-test.dll';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared',str(path),'-o',str(dll)],env=env,check=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):lib=C.CDLL(str(dll))
lib.keys.argtypes=[C.c_uint64,C.c_int];lib.keys.restype=C.c_uint
oracle=base/'NFSUG-pc-diverse-route-tests/diverse-route-report.json';ledger=json.loads(oracle.read_text());assert len(ledger['input_keys'])==6000
assert [lib.keys(i,2) for i in range(6000)]==ledger['input_keys']
assert [lib.keys(i,1) for i in range(6000)]==[1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0) for i in range(6000)]
result=dict(result='PASS_AUDIO_DURATION_INPUT_LEDGER_AND_PCM_PULL',diverse_steps=6000,simple_steps=6000,pcm_pull_and_ring_insertion_unchanged=True,reset_change_only_duration_clock=True,source_sha256=sha(source/'live_host.c'),component_sha256=sha(component),route_ledger_sha256=sha(oracle),script_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'duration-input-ledger-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

"""Verify actual scripted-input function against the established route ledger."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-traffic-live-host-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=out);out=parser.parse_args().output_dir;out.mkdir(exist_ok=True)
s=(source/'live_host.c').read_text();old=(base/'NFSUG-pc-traffic-live-host-tests/before/live_host.c').read_text()
def function(text,signature):
 a=text.index(signature);start=text.index('{',a);depth=0
 for i in range(start,len(text)):
  if text[i]=='{':depth+=1
  if text[i]=='}':
   depth-=1
   if not depth:return text[a:i+1]
 raise AssertionError(signature)
# PCM generation/ring insertion stays byte-for-byte equal to the prior host.
# Submission changes require the actual-function, consuming-device regression.
signature='static void audio_drain(';current=function(s,signature);previous=function(old,signature)
marker=' int16_t pcm[8192]';pull_end='\n /*'
assert current[current.index(marker):current.index(pull_end,current.index(marker))]==previous[previous.index(marker):previous.index('\n if(audio_device)for',previous.index(marker))]
component=base/'NFSUG-pc-audio-partial-live-tests/partial-audio-component-report.json'
proof=json.loads(component.read_text());assert proof['result']=='VERIFIED_ACTUAL_PARTIAL_AUDIO_BLOCKS_CONTROLLED_ONLY' and proof['source_sha256']==sha(source/'live_host.c') and proof['script_sha256']==sha(source/'test_audio_partial_blocks.py')
signature='static void audio_reset(';assert function(s,signature)==function(old,signature).replace('audio_queue_started=audio_queue_empty_active=0;}','audio_queue_started=audio_queue_empty_active=0;audio_queue_last_valid=audio_queue_last_queued=audio_queue_last_pending=0;audio_queue_last_time=0;audio_queue_last_pcm=0;}')
code='#include <stdint.h>\n'+function(s,'static unsigned scripted_input(')+'\n__declspec(dllexport) unsigned keys(uint64_t segment,int mode){return scripted_input(segment,mode);}\n'
(out/'input-test.c').write_text(code);dll=out/'input-test.dll';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared',str(out/'input-test.c'),'-o',str(dll)],env=env,check=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(dll))
d.keys.argtypes=[C.c_uint64,C.c_int];d.keys.restype=C.c_uint
oracle=base/'NFSUG-pc-diverse-route-tests/diverse-route-report.json';r=json.loads(oracle.read_text());expected=r['input_keys'];assert len(expected)==6000
assert [d.keys(i,2) for i in range(6000)]==expected
assert [d.keys(i,1) for i in range(6000)]==[1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0) for i in range(6000)]
result=dict(result='PASS_ACTUAL_HOST_SCRIPTED_INPUT_LEDGER',diverse_steps=6000,simple_steps=6000,audio_pcm_pull_and_ring_preserved=True,audio_submission_controlled_test_sha256=sha(component),audio_start_prefill_frames=4096,source_sha256=sha(source/'live_host.c'),script_sha256=sha(Path(__file__)),route_ledger_sha256=sha(oracle),test_c_sha256=sha(out/'input-test.c'),full_scene_60fps=False)
(out/'input-ledger-test-report.json').write_text(json.dumps(result,indent=2));print(result['result'])

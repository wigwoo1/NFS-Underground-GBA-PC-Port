"""Isolated read-only playback-position host; maintained host and offered builds unchanged."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-position-probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(source/'build_traffic_refresh2_live_host.py'),'--output-dir',str(out)],check=True)
path=out/'live-build-report.json';b=json.loads(path.read_text());(out/'baseline-live-build-report.json').write_text(json.dumps(b,indent=2));s=(source/'live_host.c').read_text()
def replace(a,c):
 global s
 assert s.count(a)==1,a;s=s.replace(a,c,1)
replace('static void audio_reset(void){','static void nf_ap_reset(void);\nstatic void audio_reset(void){')
replace('audio_queue_last_time=0;audio_queue_last_pcm=0;}','audio_queue_last_time=0;audio_queue_last_pcm=0;nf_ap_reset();}')
replace('static void invalidate(void){','#include "audio_position_probe.h"\nstatic void invalidate(void){')
replace('static void audio_drain(FILE*dump){','static void audio_drain(FILE*dump){nf_ap_sample(0);')
replace('else {audio_queue_started=1;audio_queue_empty_active=0;}}','else {nf_ap_submit(2048);audio_queue_started=1;audio_queue_empty_active=0;}}\n nf_ap_sample(1);')
replace('frames++;segment++;next+=280896.0/16777216.0;double audio_start','frames++;segment++;next+=280896.0/16777216.0;nf_ap_context(frames,next-280896.0/16777216.0);double audio_start')
replace('timeEndPeriod(1);','nf_ap_finish();timeEndPeriod(1);')
staged=out/'live_host_position_probe.c';staged.write_text(s);cmd=[str(staged) if x==str(source/'live_host.c') else x for x in b['command']];assert str(staged) in cmd;cmd.insert(1,'-I'+str(source));env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'probe-build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b.update(core_kind='diagnostic-refresh2-audio-position',diagnostic_only=True,position_probe_enabled_by_environment='NF_AUDIO_POSITION_CSV',exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),diagnostic_staged_source_sha256=sha(staged),diagnostic_command=cmd,diagnostic_builder_sha256=sha(Path(__file__)))
b['source_sha256']['audio_position_probe.h']=sha(source/'audio_position_probe.h');path.write_text(json.dumps(b,indent=2));print('BUILT_AUDIO_POSITION_PROBE_TESTS_PENDING',b['exe_sha256'])

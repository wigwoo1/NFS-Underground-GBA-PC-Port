"""Staged diagnostic host only: observe real driver reserve before/after drain."""
from pathlib import Path
import hashlib,json,os,subprocess,time
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');src=root/'work/pc';base=Path('C:/NFSUG-Workspace');parent=base/'NFSUG-pc-present-deadline-tests';out=base/'NFSUG-pc-audio-reserve-trace-tests';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((parent/'live-build-report.json').read_text())
for name,digest in b['source_sha256'].items():assert sha(src/name)==digest,name
text=(src/'live_host.c').read_text()
helper=r'''
/* DIAGNOSTIC ONLY: extra read-only driver queries, never feeds refill policy. */
static void trace_audio_reserve(unsigned phase){
 static FILE*log;static int initialized;static unsigned id;
 if(!initialized){initialized=1;const char*path=getenv("NF_AUDIO_RESERVE_TRACE");if(path)log=fopen(path,"w");if(log)fputs("drain,phase,time,produced,submitted,ring,started,queued,header_frames,result,type,played\n",log);}
 if(!log)return;
 if(!phase)id++;
 MMTIME p;memset(&p,0,sizeof(p));p.wType=TIME_SAMPLES;
 MMRESULT result=audio_device?waveOutGetPosition(audio_device,&p,sizeof(p)):MMSYSERR_ERROR;
 unsigned queued=0,header_frames=0;for(unsigned i=0;i<8;i++)if(wave[i].dwFlags&WHDR_INQUEUE){queued++;header_frames+=wave[i].dwBufferLength/4;}
 fprintf(log,"%u,%u,%.9f,%llu,%llu,%u,%u,%u,%u,%u,%u,%lu\n",id,phase,now(),(unsigned long long)audio_frames,(unsigned long long)audio_clock.submitted,audio_count,audio_queue_started,queued,header_frames,(unsigned)result,(unsigned)p.wType,(unsigned long)p.u.sample);
}
'''
marker='enum {M_CORE';assert text.count(marker)==1;text=text.replace(marker,helper+'\n'+marker)
marker='static void audio_drain(FILE*dump){';assert text.count(marker)==1;text=text.replace(marker,marker+'\n trace_audio_reserve(0);')
a=text.index(marker);start=text.index('{',a);depth=0
for end in range(start,len(text)):
 if text[end]=='{':depth+=1
 elif text[end]=='}':
  depth-=1
  if not depth:break
text=text[:end]+' trace_audio_reserve(1);\n'+text[end:]
staged=out/'diagnostic-reserve-host.c';staged.write_text(text,encoding='utf-8')
cmd=list(b['command']);cmd=[str(staged) if Path(s).name=='live_host.c' else s for s in cmd];cmd[cmd.index('-o')+1]=str(out/'NFSUG-Source-Native-Preview.exe');cmd.insert(1,'-I'+str(src))
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
compiled=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90);(out/'build.log').write_text(compiled.stdout+compiled.stderr);compiled.check_returncode()
import shutil
assert sha(parent/'capture-host.dll')==b['core_sha256'];shutil.copy2(parent/'capture-host.dll',out/'capture-host.dll')
trace=out/'reserve.csv';report=out/'session.json';pcm=out/'audio.pcm';assert not trace.exists() and not report.exists()
env['NF_AUDIO_RESERVE_TRACE']=str(trace)
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE','NF_AUDIO_POSITION_CSV']:env.pop(name,None)
command=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'),'--state',str(root/'work/integration-0.state'),'--hidden','--script-diverse','--frames','6000','--geometry-cache','--report',str(report),'--audio-dump',str(pcm)]
p=subprocess.Popen(command,env=env);(out/'run-state.json').write_text(json.dumps(dict(phase='live',pid=p.pid,command=command)));print('RESERVE_TRACE_STARTED',p.pid,flush=True)
code=p.wait(timeout=240);r=json.loads(report.read_text());assert code==r['exit_code']==0
assert r['logic_frames']==6000 and r['audio_frames']==4430117 and sha(pcm)=='e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807'
assert r['timing_errors']==r['prepare_failures']==r['present_failures']==r['audio_dropped_frames']==r['capture_gap_fallback_count']==0
assert r['processed_sequence']==r['final_sequence'] and r['geometry_allocations']==r['geometry_releases'] and r['background_allocations']==r['background_releases']
assert all(sha(src/n)==d for n,d in b['source_sha256'].items())
result=dict(result='PASS_DIAGNOSTIC_DRIVER_RESERVE_CAPTURE_EXACT_PCM',command=command,compile_command=cmd,canonical_source_sha256=b['source_sha256'],diagnostic_host_sha256=sha(staged),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_sha256=b['core_sha256'],trace_sha256=sha(trace),pcm_sha256=sha(pcm),session=r,production_changed=False,physical_audible_quality_verified=False,full_scene_60fps=False,limits='Staged host adds read-only driver position queries and buffered CSV. Measurement may perturb timing; do not use as release or no-stutter acceptance.')
(out/'capture-report.json').write_text(json.dumps(result,indent=2));(out/'run-state.json').write_text(json.dumps(dict(phase='terminal',passed=True)))
print(result['result'],r['audio_queue_empty_events'],flush=True)

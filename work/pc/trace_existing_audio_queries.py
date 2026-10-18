"""Staged bounded in-memory audio history. No added driver position queries."""
from pathlib import Path
import hashlib,json,os,subprocess,shutil
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');src=root/'work/pc';base=Path('C:/NFSUG-Workspace');parent=base/'NFSUG-pc-present-deadline-tests';out=base/'NFSUG-pc-existing-audio-query-tests';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((parent/'live-build-report.json').read_text());canonical=(src/'live_host.c').read_text()
for n,d in b['source_sha256'].items():assert sha(src/n)==d,n
helper=r'''
/* Diagnostic-only main-thread memory history; no driver calls or file I/O. */
typedef struct {double time;uint64_t produced,submitted,remaining;unsigned id,phase,ring,queued,headers,result,type,played,valid;} AudioTraceRow;
static AudioTraceRow audio_trace_rows[60000];static unsigned audio_trace_count,audio_trace_overflow,audio_trace_id;
static void audio_trace(unsigned phase,unsigned result,unsigned type,unsigned played,int valid,uint64_t remaining){
 if(!phase)audio_trace_id++;
 if(audio_trace_count==60000){audio_trace_overflow++;return;}
 AudioTraceRow*r=&audio_trace_rows[audio_trace_count++];LARGE_INTEGER t;QueryPerformanceCounter(&t);r->time=(double)t.QuadPart/frequency.QuadPart;
 r->produced=audio_frames;r->submitted=audio_clock.submitted;r->remaining=remaining;r->id=audio_trace_id;r->phase=phase;r->ring=audio_count;r->result=result;r->type=type;r->played=played;r->valid=valid;
 for(unsigned i=0;i<8;i++)if(wave[i].dwFlags&WHDR_INQUEUE){r->queued++;r->headers+=wave[i].dwBufferLength/4;}
}
static int audio_trace_save(void){
 const char*path=getenv("NF_AUDIO_EXISTING_TRACE");if(!path)return 0;FILE*f=fopen(path,"w");if(!f)return 0;
 fputs("drain,phase,time,produced,submitted,ring,queued,header_frames,result,type,played,valid,remaining\n",f);
 for(unsigned i=0;i<audio_trace_count;i++){AudioTraceRow*r=audio_trace_rows+i;fprintf(f,"%u,%u,%.9f,%llu,%llu,%u,%u,%u,%u,%u,%u,%u,%llu\n",r->id,r->phase,r->time,(unsigned long long)r->produced,(unsigned long long)r->submitted,r->ring,r->queued,r->headers,r->result,r->type,r->played,r->valid,(unsigned long long)r->remaining);}
 int ok=!ferror(f)&&!audio_trace_overflow;return fclose(f)==0&&ok;
}
'''
text=canonical.replace('static int audio_buffered_frames(',helper+'\nstatic int audio_buffered_frames(')
old='if(waveOutGetPosition(audio_device,&position,sizeof(position))!=MMSYSERR_NOERROR||position.wType!=TIME_SAMPLES){audio_duration_unknown++;return 0;}'
new='MMRESULT result=waveOutGetPosition(audio_device,&position,sizeof(position));if(result!=MMSYSERR_NOERROR||position.wType!=TIME_SAMPLES){audio_duration_unknown++;audio_trace(1,result,position.wType,position.u.sample,0,0);return 0;}'
assert text.count(old)==1;text=text.replace(old,new)
old='if(valid)audio_duration_valid++;else audio_duration_unknown++;return valid;'
assert text.count(old)==1;text=text.replace(old,'if(valid)audio_duration_valid++;else audio_duration_unknown++;audio_trace(1,result,position.wType,position.u.sample,valid,valid?*remaining:0);return valid;')
text=text.replace('audio_queue_empty_events++;','audio_queue_empty_events++;audio_trace(3,0,0,0,0,0);')
marker='static void audio_drain(FILE*dump){';text=text.replace(marker,marker+'\n audio_trace(0,0,0,0,0,0);')
a=text.index(marker);start=text.index('{',a);depth=0
for end in range(start,len(text)):
 if text[end]=='{':depth+=1
 elif text[end]=='}':
  depth-=1
  if not depth:break
text=text[:end]+' audio_trace(2,0,0,0,0,0);\n'+text[end:]
old='DeleteCriticalSection(&presentation_mutex);DeleteCriticalSection(&mutex);return result;'
assert text.count(old)==1;text=text.replace(old,'DeleteCriticalSection(&presentation_mutex);DeleteCriticalSection(&mutex);if(!audio_trace_save())return 3;return result;')
assert text.count('waveOutGetPosition(')==canonical.count('waveOutGetPosition(')==1
staged=out/'existing-query-host.c';staged.write_text(text,encoding='utf-8')
cmd=[str(staged) if Path(s).name=='live_host.c' else s for s in b['command']];cmd[cmd.index('-o')+1]=str(out/'NFSUG-Source-Native-Preview.exe');cmd.insert(1,'-I'+str(src))
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90);(out/'build.log').write_text(r.stdout+r.stderr);r.check_returncode();shutil.copy2(parent/'capture-host.dll',out/'capture-host.dll')
assert sha(out/'capture-host.dll')==b['core_sha256']
trace=out/'existing-query.csv';report=out/'session.json';pcm=out/'audio.pcm';assert not trace.exists() and not report.exists()
env['NF_AUDIO_EXISTING_TRACE']=str(trace)
for n in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE','NF_AUDIO_POSITION_CSV']:env.pop(n,None)
command=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'),'--state',str(root/'work/integration-0.state'),'--hidden','--script-diverse','--frames','6000','--geometry-cache','--report',str(report),'--audio-dump',str(pcm)]
p=subprocess.Popen(command,env=env);(out/'run-state.json').write_text(json.dumps(dict(phase='live',pid=p.pid,command=command)));print('EXISTING_QUERY_TRACE_STARTED',p.pid,flush=True)
code=p.wait(timeout=240);r=json.loads(report.read_text());assert code==r['exit_code']==0
assert r['logic_frames']==6000 and r['audio_frames']==4430117 and sha(pcm)=='e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807'
assert r['timing_errors']==r['prepare_failures']==r['present_failures']==r['audio_dropped_frames']==r['capture_gap_fallback_count']==0
assert r['processed_sequence']==r['final_sequence'] and r['geometry_allocations']==r['geometry_releases'] and r['background_allocations']==r['background_releases']
assert all(sha(src/n)==d for n,d in b['source_sha256'].items())
result=dict(result='PASS_EXISTING_QUERY_IN_MEMORY_AUDIO_TRACE_EXACT_PCM',command=command,compile_command=cmd,canonical_source_sha256=b['source_sha256'],diagnostic_source_sha256=sha(staged),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_sha256=b['core_sha256'],trace_sha256=sha(trace),pcm_sha256=sha(pcm),session=r,additional_driver_queries=0,file_writes_during_playback=0,production_changed=False,physical_audio_verified=False,full_scene_60fps=False)
(out/'capture-report.json').write_text(json.dumps(result,indent=2));(out/'run-state.json').write_text(json.dumps(dict(phase='terminal',passed=True)))
print(result['result'],r['audio_queue_empty_events'],flush=True)

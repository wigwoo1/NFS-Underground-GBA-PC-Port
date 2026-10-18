"""Exact audio_drain/reset under finite consumption and recorded producer times."""
from pathlib import Path
import hashlib,json,os,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');source=root/'work/pc';base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-audio-duration-tests';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=root/'outputs/nfsug-native-renderer/camera-research/pc-audio-duration-20261017/before/live_host.c'
frozen=base/'NFSUG-pc-audio-partial-live-tests/candidate-partial-simulation.c';s=frozen.read_text()
prefix=s[:s.index('static WAVEHDR wave[8]')]
prefix+='\nstatic uint64_t epoch_base;static unsigned fake_position_error,fake_position_type=TIME_SAMPLES;\nstatic MMRESULT __attribute__((unused)) fake_position(HWAVEOUT,MMTIME*,UINT);\n#define waveOutGetPosition fake_position\n'
suffix=s[s.index('static void advance_driver(void)'):s.index('int main(int argc')]
assert suffix.count('assert(h);queued=head=0;')==1;suffix=suffix.replace('assert(h);queued=head=0;','assert(h);epoch_base=submitted;queued=head=0;')
suffix+='''
static MMRESULT __attribute__((unused)) fake_position(HWAVEOUT h,MMTIME*p,UINT size){assert(h&&size==sizeof(*p));if(fake_position_error)return MMSYSERR_ERROR;p->wType=fake_position_type;double reserve=0;for(unsigned i=0;i<queued;i++)reserve+=remaining[(head+i)%8];double played=(double)(submitted-epoch_base)-reserve;p->u.sample=(DWORD)(played>0?played+1e-6:0);return MMSYSERR_NOERROR;}
int main(int argc,char**argv){assert(argc==2);core.audio=fake_audio;audio_device=(HWAVEOUT)(uintptr_t)1;for(unsigned i=0;i<8;i++)wave[i].lpData=(char*)samples[i];audio_reset();
#ifdef NF_DURATION_CANDIDATE
 if(!strcmp(argv[1],"guards")){
  pending_samples=4095;audio_drain(NULL);assert(!writes&&audio_count==4095&&!audio_queue_started);
  pending_samples=1;audio_drain(NULL);assert(writes==2&&queued==2&&audio_count==0&&audio_clock.submitted==4096);
  pending_samples=1770;audio_drain(NULL);assert(writes==2&&audio_count==1770);
  fake_time=.010;advance_driver();audio_drain(NULL);assert(writes==3&&queued==3&&audio_count==0&&audio_clock.submitted==5866);
  fake_position_type=TIME_BYTES;pending_samples=10;audio_drain(NULL);assert(audio_count==0&&submitted==produced);
  fake_position_type=TIME_SAMPLES;fake_position_error=1;pending_samples=11;audio_drain(NULL);assert(audio_count==0&&submitted==produced);fake_position_error=0;
  audio_reset();assert(!audio_count&&!queued&&!audio_queue_started&&!audio_clock.submitted&&!audio_clock.valid);
  pending_samples=4096;audio_drain(NULL);assert(queued==2&&audio_clock.submitted==4096);
  for(unsigned i=0;i<6;i++){pending_samples=2048;audio_drain(NULL);}assert(queued==8);
  pending_samples=31;audio_drain(NULL);assert(queued==8&&audio_count==31);
  audio_reset();audio_device=NULL;pending_samples=123;audio_drain(NULL);assert(!audio_count&&!queued&&audio_dropped==0);
  audio_device=(HWAVEOUT)(uintptr_t)1;audio_reset();pending_samples=4096;fail_write=1;audio_drain(NULL);assert(audio_dropped==4096&&!queued&&!audio_clock.submitted);
  puts("PASS_DURATION_RESERVE_TAIL_UNKNOWN_UNITS_ERRORS_RESET_CAPACITY_FAILURE_NO_DEVICE");return 0;
 }
#endif
 FILE*f=fopen(argv[1],"r");assert(f);double t;unsigned n;while(fscanf(f,"%lf %u",&t,&n)==2){fake_time=t;advance_driver();pending_samples=n;audio_drain(NULL);}fclose(f);
 assert(audio_dropped==0&&submitted+audio_count==produced&&audio_frames==produced);
 printf("{\\"empty_events\\":%llu,\\"first_submit_ms\\":%.6f,\\"produced_frames\\":%llu,\\"submitted_frames\\":%llu,\\"pending_frames\\":%u,\\"partial_writes\\":%u,\\"sample_order_exact\\":true}\\n",(unsigned long long)audio_queue_empty_events,first_write*1000,(unsigned long long)produced,(unsigned long long)submitted,audio_count,partial_writes);return 0;}
'''
def function(text,name):
 a=text.index('static void '+name+'(');start=text.index('{',a);depth=0
 for i in range(start,len(text)):
  if text[i]=='{':depth+=1
  elif text[i]=='}':
   depth-=1
   if not depth:return text[a:i+1]
 raise AssertionError(name)
trace=base/'NFSUG-pc-audio-partial-live-tests/measured-service-times.txt';assert len(trace.read_text().splitlines())==6000
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');results={}
cases={'measured':trace}
for label,stall in [('steady',0),('extreme_stall',.150)]:
 t=0;rows=[]
 for i in range(1,301):t=max(t,i*.01)+.007+(stall if i==30 else 0);rows.append(f'{t:.9f} 441\n')
 path=out/(label+'.txt');path.write_text(''.join(rows));cases[label]=path
for mode,path in [('baseline',old),('candidate',source/'live_host.c')]:
 text=path.read_text();globals=text[text.index('static WAVEHDR wave[8]'):text.index('static double now(void)')]
 staged=out/(mode+'.c');staged.write_text(prefix+globals+function(text,'audio_drain')+suffix)
 exe=staged.with_suffix('.exe');command=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(source)]
 if mode=='candidate':command+=['-DNF_DURATION_CANDIDATE=1']
 command += [str(staged),'-o',str(exe)]
 run=subprocess.run(command,env=env,capture_output=True,text=True);(out/(mode+'-compile.log')).write_text(run.stdout+run.stderr);run.check_returncode()
 results[mode]={}
 for name,case in cases.items():
  run=subprocess.run([str(exe),str(case)],env=env,capture_output=True,text=True);(out/(mode+'-'+name+'.log')).write_text(run.stdout+run.stderr);run.check_returncode();results[mode][name]=json.loads(run.stdout)
 if mode=='candidate':
  run=subprocess.run([str(exe),'guards'],env=env,capture_output=True,text=True);(out/'guards.log').write_text(run.stdout+run.stderr);run.check_returncode();assert 'PASS_DURATION_RESERVE' in run.stdout
assert results['baseline']['measured']['empty_events']==1
assert results['candidate']['measured']['empty_events']==0
assert results['candidate']['steady']['empty_events']==0 and results['candidate']['extreme_stall']['empty_events']>0
for name in cases:
 assert results['baseline'][name]['first_submit_ms']==results['candidate'][name]['first_submit_ms']
 assert results['baseline'][name]['produced_frames']==results['candidate'][name]['produced_frames']
report=dict(result='VERIFIED_DURATION_AUDIO_REFILL_CONTROLLED_ONLY',rows=results,source_sha256=sha(source/'live_host.c'),header_sha256=sha(source/'audio_queue_duration.h'),baseline_sha256=sha(old),service_trace_sha256=sha(trace),script_sha256=sha(Path(__file__)),full_scene_60fps=False,physical_audio_verified=False,limits='Exact actual host functions with a finite ideal consuming-device queue and recorded producer service times. Zero modeled empty observations is not audible hardware proof. No new PCM, logic acceleration, latency measurement or runnable-release acceptance.')
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

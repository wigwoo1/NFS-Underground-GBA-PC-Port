"""Actual host audio functions under deterministic device consumption and stalls."""
from pathlib import Path
import hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-prefill-live-tests';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def function(s,name):
 a=s.index('static void '+name+'(');start=s.index('{',a);depth=0
 for i in range(start,len(s)):
  if s[i]=='{':depth+=1
  elif s[i]=='}':
   depth-=1
   if not depth:return s[a:i+1]
 raise AssertionError(name)
prefix=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static HWAVEOUT audio_device;
static double fake_time,driver_time,first_write=-1;
static double remaining[8];static unsigned driver_ids[8],head,queued,writes;
static uint64_t produced,submitted;
static size_t pending_samples;
static void*game;
static struct {size_t(*audio)(void*,int16_t*,size_t);}core;
static double now(void){return fake_time;}
static MMRESULT fake_reset(HWAVEOUT);
static MMRESULT fake_write(HWAVEOUT,WAVEHDR*,UINT);
#define waveOutReset fake_reset
#define waveOutWrite fake_write
'''
suffix=r'''
static void advance_driver(void){double due=(fake_time-driver_time)*44100;driver_time=fake_time;while(queued&&due>=remaining[head]){due-=remaining[head];wave[driver_ids[head]].dwFlags=0;head=(head+1)%8;queued--;}if(queued)remaining[head]-=due;}
static MMRESULT fake_reset(HWAVEOUT h){assert(h);queued=head=0;for(unsigned i=0;i<8;i++)wave[i].dwFlags=0;return MMSYSERR_NOERROR;}
static int16_t value(uint64_t i){return(int16_t)(i%30001);}
static MMRESULT fake_write(HWAVEOUT h,WAVEHDR*w,UINT bytes){assert(h&&bytes==sizeof(*w)&&queued<8&&w->dwBufferLength==8192);unsigned at=(head+queued)%8;driver_ids[at]=(unsigned)(w-wave);remaining[at]=2048;queued++;w->dwFlags|=WHDR_INQUEUE;int16_t*pcm=(int16_t*)w->lpData;for(unsigned i=0;i<2048;i++){assert(pcm[i*2]==value(submitted+i)&&pcm[i*2+1]==-value(submitted+i));}submitted+=2048;writes++;if(first_write<0)first_write=fake_time;return MMSYSERR_NOERROR;}
static size_t fake_audio(void*h,int16_t*out,size_t maximum){(void)h;size_t n=pending_samples<maximum?pending_samples:maximum;pending_samples-=n;for(size_t i=0;i<n;i++){out[i*2]=value(produced+i);out[i*2+1]=-value(produced+i);}produced+=n;return n;}
int main(int argc,char**argv){assert(argc==2);double stall=atof(argv[1]);core.audio=fake_audio;audio_device=(HWAVEOUT)(uintptr_t)1;for(unsigned i=0;i<8;i++)wave[i].lpData=(char*)samples[i];for(unsigned i=1;i<=300;i++){double deadline=i*.010;if(fake_time<deadline)fake_time=deadline;if(i==30)fake_time+=stall/1000;fake_time+=.007;advance_driver();pending_samples=441;audio_drain(NULL);}assert(audio_dropped==0&&produced==132300&&audio_frames==produced&&submitted+audio_count==produced);printf("{\"first_submit_ms\":%.6f,\"empty_events\":%llu,\"produced_frames\":%llu,\"submitted_frames\":%llu,\"pending_frames\":%u,\"writes\":%u,\"sample_order_exact\":true}\n",first_write*1000,(unsigned long long)audio_queue_empty_events,(unsigned long long)produced,(unsigned long long)submitted,audio_count,writes);audio_reset();assert(!audio_queue_started&&!audio_count);return 0;}
'''
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');rows={};commands=[]
for name,path in [('baseline',out/'before/live_host.c'),('candidate',source/'live_host.c')]:
 s=path.read_text();globals=s[s.index('static WAVEHDR wave[8]'):s.index('static double now(void)')];staged=out/(name+'-prefill-simulation.c');staged.write_text(prefix+globals+function(s,'audio_drain')+suffix);exe=out/(name+'-prefill-simulation.exe');cmd=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror',str(staged),'-o',str(exe)];subprocess.run(cmd,env=env,check=True);commands.append(cmd);rows[name]={}
 for label,stall in [('steady',0),('measured_interval',50.2619),('beyond_reserve',150)]:
  run=subprocess.run([str(exe),str(stall)],env=env,check=True,capture_output=True,text=True);rows[name][label]=json.loads(run.stdout)
assert rows['candidate']['steady']['empty_events']==0 and rows['baseline']['steady']['empty_events']>0
assert rows['baseline']['measured_interval']['empty_events']>0 and rows['candidate']['measured_interval']['empty_events']==0
assert rows['candidate']['beyond_reserve']['empty_events']>0
assert rows['baseline']['steady']['first_submit_ms']==57 and rows['candidate']['steady']['first_submit_ms']==107
for mode in rows:
 for case in rows[mode].values():assert case['produced_frames']==132300 and case['sample_order_exact']
report=dict(result='VERIFIED_TWO_BLOCK_RESERVE_MEASURED_STALL_AND_LATENCY',rows=rows,controlled_poll_interval_ms=60.2619,controlled_added_start_delay_ms=50,nominal_added_reserve_ms=2048/44100*1000,not_hardware_latency_measurement=True,source_sha256=sha(source/'live_host.c'),baseline_source_sha256=sha(out/'before/live_host.c'),script_sha256=sha(Path(__file__)),commands=commands,full_scene_60fps=False)
(out/'audio-prefill-simulation-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

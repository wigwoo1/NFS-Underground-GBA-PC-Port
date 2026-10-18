"""Compile actual staged audio/reset and probe against a controlled position API."""
from pathlib import Path
import hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-position-probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();s=(out/'live_host_position_probe.c').read_text()
def function(name):
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
static double fake_time;static double now(void){return fake_time;}
static size_t pending_samples;static uint64_t submitted_pcm;static unsigned position_calls,writes,position_value,position_type=TIME_SAMPLES,position_error;
static void*game;static struct {size_t(*audio)(void*,int16_t*,size_t);}core;
enum {M_CORE,M_CAPTURE,M_PUBLISH,M_LOCK,M_PREPARE,M_GPU,M_PRESENT,M_AUDIO,M_LOGIC,M_INTERVAL,M_COUNT};
typedef struct {uint64_t count,over16,over33;double total,max;}Metric;static Metric metrics[M_COUNT];
static MMRESULT fake_reset(HWAVEOUT);static MMRESULT fake_write(HWAVEOUT,WAVEHDR*,UINT);static MMRESULT fake_position(HWAVEOUT,LPMMTIME,UINT);
#define waveOutReset fake_reset
#define waveOutWrite fake_write
#define waveOutGetPosition fake_position
'''
suffix=r'''
static MMRESULT fake_reset(HWAVEOUT h){assert(h);for(unsigned i=0;i<8;i++)wave[i].dwFlags=0;position_value=0;return MMSYSERR_NOERROR;}
static MMRESULT fake_write(HWAVEOUT h,WAVEHDR*w,UINT n){assert(h&&n==sizeof(*w));int16_t*p=(int16_t*)w->lpData;for(unsigned i=0;i<2048;i++){assert(p[i*2]==(int16_t)((submitted_pcm+i)%20001));assert(p[i*2+1]==-p[i*2]);}submitted_pcm+=2048;writes++;w->dwFlags|=WHDR_INQUEUE;return MMSYSERR_NOERROR;}
static MMRESULT fake_position(HWAVEOUT h,LPMMTIME p,UINT n){assert(h&&n==sizeof(*p)&&p->wType==TIME_SAMPLES);position_calls++;if(position_error)return position_error;p->wType=position_type;p->u.sample=position_value;return MMSYSERR_NOERROR;}
static size_t fake_audio(void*h,int16_t*out,size_t max){(void)h;size_t n=pending_samples<max?pending_samples:max;pending_samples-=n;for(size_t i=0;i<n;i++){out[i*2]=(int16_t)((audio_frames+i)%20001);out[i*2+1]=-out[i*2];}return n;}
int main(int argc,char**argv){assert(argc==3);_putenv_s("NF_AUDIO_POSITION_CSV",strcmp(argv[2],"off")==0?"":argv[1]);audio_device=(HWAVEOUT)(uintptr_t)1;core.audio=fake_audio;for(unsigned i=0;i<8;i++)wave[i].lpData=(char*)samples[i];nf_ap_context(1,0);pending_samples=2048;audio_drain(NULL);assert(!audio_queue_started&&audio_count==2048);pending_samples=2048;audio_drain(NULL);assert(audio_queue_started&&writes==2&&audio_frames==4096&&audio_count==0);
 if(strcmp(argv[2],"off")==0){assert(!position_calls&&!nf_ap_count);nf_ap_finish();puts("PASS_POSITION_PROBE_DISABLED_PCM_EXACT");return 0;}
 assert(nf_ap_submitted==4096&&nf_ap_count==4);position_value=1024;fake_time=.030;nf_ap_context(3,.020);metrics[M_CORE].total=7.25;metrics[M_CAPTURE].total=2.125;audio_drain(NULL);NFAPRow*r=nf_ap_rows+nf_ap_count-1;assert(r->valid&&r->comparable&&r->remaining==3072&&r->played==1024&&r->queued==2&&r->core==7.25&&r->capture==2.125&&r->lag>9.999&&r->lag<10.001);
 position_type=TIME_MS;audio_drain(NULL);r=nf_ap_rows+nf_ap_count-1;assert(!r->valid&&!r->comparable&&r->type==TIME_MS);
 position_type=TIME_SAMPLES;position_error=MMSYSERR_NODRIVER;audio_drain(NULL);r=nf_ap_rows+nf_ap_count-1;assert(r->error==MMSYSERR_NODRIVER&&!r->valid&&!r->comparable);
 position_error=0;position_value=100;audio_drain(NULL);r=nf_ap_rows+nf_ap_count-1;assert(!r->valid&&!r->comparable);
 position_value=5000;audio_drain(NULL);r=nf_ap_rows+nf_ap_count-1;assert(r->valid&&!r->comparable&&r->played==5000);
 nf_ap_last_valid=1;nf_ap_last=UINT32_MAX-10;nf_ap_high=0;nf_ap_submitted=(1ull<<32)+100;position_value=20;audio_drain(NULL);r=nf_ap_rows+nf_ap_count-1;assert(r->valid&&r->comparable&&r->played==(1ull<<32)+20&&r->remaining==80);
 audio_reset();assert(nf_ap_epoch==1&&!nf_ap_last_valid&&!nf_ap_high&&!nf_ap_submitted);audio_drain(NULL);r=nf_ap_rows+nf_ap_count-1;assert(r->epoch==1&&r->valid&&r->comparable&&!r->produced&&!r->submitted&&!r->played);
 unsigned count=nf_ap_count;nf_ap_count=16384;nf_ap_sample(0);assert(nf_ap_count==16384&&nf_ap_overflow==1);nf_ap_count=count;nf_ap_finish();assert(audio_frames==4096&&submitted_pcm==4096&&writes==2&&!audio_dropped);puts("PASS_POSITION_PROBE_UNITS_RESET_WRAP_BOUNDS_PCM_EXACT");return 0;}
'''
globals=s[s.index('static WAVEHDR wave[8]'):s.index('static double now(void)')];code=prefix+globals+'\n#include "audio_position_probe.h"\n'+function('audio_drain')+suffix;file=out/'position-component.c';file.write_text(code);exe=out/'position-component.exe';cmd=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(source),str(file),'-o',str(exe)];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(cmd,env=env,check=True)
for mode in ['off','on']:
 r=subprocess.run([str(exe),str(out/(mode+'-component.csv')),mode],env=env,check=True,capture_output=True,text=True);print(r.stdout.strip());assert ('DISABLED' in r.stdout)==(mode=='off')
assert not (out/'off-component.csv').exists() and (out/'on-component.csv').exists()
report=dict(result='PASS_ACTUAL_AUDIO_POSITION_PROBE_COMPONENT',verified=['nonzero_stereo_sample_order_unchanged','disabled_probe_no_driver_queries','per_channel_samples_remaining_not_buffer_count','alternate_units_rejected','driver_error_rejected','backwards_position_rejected','position_ahead_not_subtracted','one32bit_wrap_unwrapped','reset_starts_new_epoch','trace_capacity_bounded','owner_phase_and_deadline_context_recorded'],header_sha256=sha(source/'audio_position_probe.h'),staged_host_sha256=sha(out/'live_host_position_probe.c'),test_c_sha256=sha(file),binary_sha256=sha(exe),script_sha256=sha(Path(__file__)),hardware_playback=False)
(out/'position-component-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

"""Compile the real host audio functions with a fake driver to test queue signals.

Only the device/core boundary is mocked; audio_drain and reset are extracted from
maintained live_host.c. Hardware playback is covered by the separate long run.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-queue-tests';out.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=out);out=parser.parse_args().output_dir;out.mkdir(exist_ok=True)
s=(source/'live_host.c').read_text();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def function(name):
 start=s.index('static void '+name+'(');body=s.index('{',start);depth=0
 for i in range(body,len(s)):
  if s[i]=='{':depth+=1
  elif s[i]=='}':
   depth-=1
   if depth==0:return s[start:i+1]
 raise AssertionError(name)
globals=s[s.index('static WAVEHDR wave[8]'):s.index('static double now(void)')]
# globals already includes the unchanged real reset function.
assert function('audio_reset') in globals
prefix=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static HWAVEOUT audio_device;
static double fake_time;
static double now(void){return fake_time;}
static size_t pending_samples;
static int write_failure;
static void *game;
static struct {size_t(*audio)(void*,int16_t*,size_t);} core;
static MMRESULT fake_reset(HWAVEOUT);
static MMRESULT fake_write(HWAVEOUT,WAVEHDR*,UINT);
#define waveOutReset fake_reset
#define waveOutWrite fake_write
'''
suffix=r'''
static MMRESULT fake_reset(HWAVEOUT handle){assert(handle);for(unsigned i=0;i<8;i++)wave[i].dwFlags=0;return MMSYSERR_NOERROR;}
static MMRESULT fake_write(HWAVEOUT handle,WAVEHDR*h,UINT size){assert(handle&&h&&size==sizeof(*h));if(write_failure)return MMSYSERR_ERROR;h->dwFlags|=WHDR_INQUEUE;return MMSYSERR_NOERROR;}
static size_t fake_audio(void*unused,int16_t*out,size_t maximum){(void)unused;size_t n=pending_samples<maximum?pending_samples:maximum;pending_samples-=n;memset(out,0,n*4);return n;}
int main(void){
 core.audio=fake_audio;audio_device=(HWAVEOUT)(uintptr_t)1;
 pending_samples=2048;audio_drain(NULL);assert(!audio_queue_started&&audio_count==2048&&audio_queue_polls==0);
 pending_samples=2048;audio_drain(NULL);assert(audio_queue_started&&audio_queue_polls==0&&(wave[0].dwFlags&WHDR_INQUEUE)&&(wave[1].dwFlags&WHDR_INQUEUE));
 audio_drain(NULL);assert(audio_queue_polls==1&&!audio_queue_empty_polls&&!audio_queue_empty_events&&audio_queue_min==2&&audio_queue_max==2);
 fake_time=.050;for(unsigned i=0;i<8;i++)wave[i].dwFlags=0;audio_drain(NULL);assert(audio_queue_polls==2&&audio_queue_empty_polls==1&&audio_queue_empty_events==1&&audio_queue_empty_pcm[0]==4096);
 assert(audio_queue_empty_interval_ms[0]>49.999&&audio_queue_empty_interval_ms[0]<50.001);
 assert(audio_queue_empty_context[0][0]==4096&&audio_queue_empty_context[0][1]==2&&audio_queue_empty_context[0][2]==0&&audio_queue_empty_context[0][3]==0&&audio_queue_empty_context[0][4]==1);
 audio_drain(NULL);assert(audio_queue_empty_polls==2&&audio_queue_empty_events==1);
 pending_samples=2048;audio_drain(NULL);assert(audio_queue_empty_polls==3&&audio_queue_empty_events==1&&audio_queue_started);
 wave[0].dwFlags=0;audio_drain(NULL);assert(audio_queue_empty_polls==4&&audio_queue_empty_events==2&&audio_queue_log_count==2&&audio_queue_empty_pcm[1]==6144);
 uint64_t polls=audio_queue_polls;audio_reset();audio_drain(NULL);assert(audio_queue_polls==polls&&!audio_queue_started&&!audio_count&&!audio_queue_last_valid);
 audio_device=NULL;pending_samples=2048;audio_drain(NULL);assert(audio_frames==8192&&!audio_count&&audio_queue_polls==polls);
 audio_device=(HWAVEOUT)(uintptr_t)1;write_failure=1;pending_samples=4096;audio_drain(NULL);assert(audio_dropped==4096&&!audio_queue_started);
 write_failure=0;pending_samples=2048;audio_drain(NULL);assert(!audio_queue_started&&audio_count==2048&&audio_queue_polls==polls);
 pending_samples=2048;audio_drain(NULL);assert(audio_queue_started&&audio_queue_polls==polls);
 for(unsigned i=0;i<40;i++){for(unsigned j=0;j<8;j++)wave[j].dwFlags=0;pending_samples=2048;audio_drain(NULL);}
 assert(audio_queue_empty_events==42&&audio_queue_log_count==32);
 assert(audio_queue_empty_context[2][4]==0&&audio_queue_empty_interval_ms[2]==0);
 audio_reset();assert(!audio_queue_started&&!audio_count);
 puts("PASS_REAL_HOST_AUDIO_QUEUE_COUNTER_POSITIVE_NEGATIVE_RESET");return 0;
}
'''
staged=out/'test-audio-queue-component.c';staged.write_text(prefix+globals+function('audio_drain')+suffix)
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
cmd=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror',str(staged),'-o',str(out/'test-audio-queue-component.exe')]
subprocess.run(cmd,env=env,check=True);r=subprocess.run([str(out/'test-audio-queue-component.exe')],env=env,check=True,capture_output=True,text=True)
assert r.stdout.strip()=='PASS_REAL_HOST_AUDIO_QUEUE_COUNTER_POSITIVE_NEGATIVE_RESET'
report=dict(result='PASS_REAL_HOST_AUDIO_QUEUE_COMPONENT',source_sha256=sha(source/'live_host.c'),script_sha256=sha(Path(__file__)),staged_sha256=sha(staged),binary_sha256=sha(out/'test-audio-queue-component.exe'),command=cmd,verified=['empty_driver_queue_detected','nonempty_queue_not_flagged','consecutive_empty_polls_coalesce','requeue_then_empty_starts_new_event','initial_fill_ignored','two_blocks_required_at_start_and_after_reset','deliberate_reset_ignored','no_audio_device_ignored','write_failure_preserves_drop_accounting','event_log_capped_at_32','preceding_queue_and_ring_snapshot_recorded','controlled_50ms_poll_interval_exact','reset_discards_prior_poll_context'],hardware_playback=False)
(out/'audio-queue-component-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

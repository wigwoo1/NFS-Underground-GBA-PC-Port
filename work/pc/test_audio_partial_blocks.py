"""Actual production audio functions: finite consuming queue and recorded service times."""
from pathlib import Path
import ast,csv,hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-partial-live-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tree=ast.parse((source/'test_audio_prefill_reserve.py').read_text());literals={}
for x in tree.body:
 if isinstance(x,ast.Assign) and isinstance(x.value,ast.Constant):
  for n in x.targets:
   if isinstance(n,ast.Name):literals[n.id]=x.value.value
def function(s,name):
 a=s.index('static void '+name+'(');start=s.index('{',a);depth=0
 for i in range(start,len(s)):
  if s[i]=='{':depth+=1
  elif s[i]=='}':
   depth-=1
   if not depth:return s[a:i+1]
 raise AssertionError(name)
prefix=literals['prefix']+'\nstatic unsigned partial_writes,fail_write;\n'
suffix=literals['suffix'];suffix=suffix[:suffix.index('int main(')]
suffix=suffix.replace('w->dwBufferLength==8192','w->dwBufferLength>0&&w->dwBufferLength<=8192&&w->dwBufferLength%4==0')
suffix=suffix.replace('unsigned at=(head+queued)%8;','if(fail_write)return MMSYSERR_ERROR;unsigned count=w->dwBufferLength/4;if(count<2048)partial_writes++;unsigned at=(head+queued)%8;').replace('remaining[at]=2048','remaining[at]=count').replace('i<2048','i<count').replace('submitted+=2048','submitted+=count')
suffix+=r"""
int main(int argc,char**argv){assert(argc==2);core.audio=fake_audio;audio_device=(HWAVEOUT)(uintptr_t)1;for(unsigned i=0;i<8;i++)wave[i].lpData=(char*)samples[i];
 if(!strcmp(argv[1],"guards")){
  pending_samples=4095;audio_drain(NULL);assert(!writes&&audio_count==4095&&!audio_queue_started);
  pending_samples=1;audio_drain(NULL);assert(writes==2&&queued==2&&audio_count==0);
  pending_samples=1770;audio_drain(NULL);assert(writes==2&&audio_count==1770);
  fake_time=2048.0/44100+.000001;advance_driver();audio_drain(NULL);assert(queued==2&&partial_writes==1&&audio_count==0&&submitted==produced);
  audio_reset();assert(!queued&&!audio_count&&!audio_queue_started);
  submitted=produced=0;pending_samples=4096;fail_write=1;audio_drain(NULL);assert(audio_dropped==4096&&!queued&&!audio_count&&!audio_queue_started);
  fail_write=0;audio_dropped=0;pending_samples=4096;submitted=produced;audio_drain(NULL);assert(queued==2);
  for(unsigned i=0;i<6;i++){pending_samples=2048;audio_drain(NULL);}assert(queued==8);
  pending_samples=31;audio_drain(NULL);assert(queued==8&&audio_count==31);
  audio_reset();audio_device=NULL;pending_samples=123;audio_drain(NULL);assert(!audio_count&&!queued&&audio_dropped==0);
  puts("PASS_START_PARTIAL_RESET_FAILURE_CAPACITY_NO_DEVICE");return 0;
 }
 FILE*f=fopen(argv[1],"r");assert(f);double t;unsigned n;while(fscanf(f,"%lf %u",&t,&n)==2){fake_time=t;advance_driver();pending_samples=n;audio_drain(NULL);}fclose(f);
 assert(audio_dropped==0&&submitted+audio_count==produced&&audio_frames==produced);
 printf("{\"empty_events\":%llu,\"first_submit_ms\":%.6f,\"produced_frames\":%llu,\"submitted_frames\":%llu,\"pending_frames\":%u,\"partial_writes\":%u,\"sample_order_exact\":true}\n",(unsigned long long)audio_queue_empty_events,first_write*1000,(unsigned long long)produced,(unsigned long long)submitted,audio_count,partial_writes);return 0;}
"""
trace=base/'NFSUG-pc-audio-position-probe/audio-position-6000.csv';rows=list(csv.DictReader(trace.open()));assert len(rows)==12000
origin=float(rows[0]['time']);lines=[]
for a,b in zip(rows[::2],rows[1::2]):
 assert a['stage']=='0' and b['stage']=='1' and a['frame']==b['frame']
 lines.append(f"{float(a['time'])-origin:.9f} {int(b['produced_frames'])-int(a['produced_frames'])}\n")
(out/'measured-service-times.txt').write_text(''.join(lines))
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');results={}
for name,path in [('baseline',out/'before/live_host.c'),('candidate',source/'live_host.c')]:
 s=path.read_text();globals=s[s.index('static WAVEHDR wave[8]'):s.index('static double now(void)')];c=out/(name+'-partial-simulation.c');c.write_text(prefix+globals+function(s,'audio_drain')+suffix);exe=c.with_suffix('.exe')
 subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],env=env,check=True)
 results[name]={}
 cases={'measured':out/'measured-service-times.txt'}
 for label,stall in [('steady',0),('extreme_stall',.15)]:
  t=0;case=out/(label+'-service-times.txt');data=[]
  for i in range(1,301):
   t=max(t,i*.01)+.007+(stall if i==30 else 0);data.append(f'{t:.9f} 441\n')
  case.write_text(''.join(data));cases[label]=case
 for label,case in cases.items():results[name][label]=json.loads(subprocess.run([str(exe),str(case)],env=env,check=True,capture_output=True,text=True).stdout)
 if name=='candidate':assert subprocess.run([str(exe),'guards'],env=env,check=True,capture_output=True,text=True).stdout.strip()=='PASS_START_PARTIAL_RESET_FAILURE_CAPACITY_NO_DEVICE'
assert results['candidate']['measured']['empty_events']<results['baseline']['measured']['empty_events'],results
assert results['candidate']['steady']['empty_events']==0
assert results['candidate']['extreme_stall']['empty_events']>0
for label in cases:
 assert results['candidate'][label]['first_submit_ms']==results['baseline'][label]['first_submit_ms']
 assert results['candidate'][label]['produced_frames']==results['baseline'][label]['produced_frames']
report=dict(result='VERIFIED_ACTUAL_PARTIAL_AUDIO_BLOCKS_CONTROLLED_ONLY',rows=results,source_sha256=sha(source/'live_host.c'),baseline_source_sha256=sha(out/'before/live_host.c'),script_sha256=sha(Path(__file__)),trace_sha256=sha(trace),no_physical_audio_or_latency_claim=True,full_scene_60fps=False)
(out/'partial-audio-component-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

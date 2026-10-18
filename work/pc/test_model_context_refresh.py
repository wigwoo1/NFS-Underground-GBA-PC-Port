"""Compile actual context handoff helper with mocked context reads."""
from pathlib import Path
import hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;out=Path(r"C:\NFSUG-Workspace\NFSUG-pc-model-context-helper-tests");out.mkdir(exist_ok=True)
code=r'''
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
static struct {uint64_t epoch;unsigned serial,frame,object,verified;uint8_t context[68];uint32_t address,stats[6];unsigned active,expected;} live_object_model_context;
static struct {unsigned begin;} live_scene;
static uint8_t actual[68];static int read_ok=1;
static int native_surface_read(void*user,uint32_t address,void*out,size_t size){(void)user;if(!read_ok||address!=0x03007dc8||size!=68)return 0;memcpy(out,actual,68);return 1;}
#include "model_context_refresh.inc"
static void reset(void){memset(&live_object_model_context,0,sizeof(live_object_model_context));memset(nf_context_refresh_stats,0,sizeof(nf_context_refresh_stats));live_scene.begin=90;read_ok=1;for(unsigned i=0;i<68;i++)actual[i]=(uint8_t)i;memcpy(live_object_model_context.context,actual,68);live_object_model_context.epoch=2;live_object_model_context.serial=458;live_object_model_context.frame=100;live_object_model_context.object=0x02004458;live_object_model_context.address=0x03007dc8;live_object_model_context.verified=live_object_model_context.expected=1;}
static int commit(void){return nf_context_refresh_commit(0x03007dc8,0x02004458,2,458,101);}
#define REJECT(change) do{reset();change;unsigned char before[sizeof(live_object_model_context)];memcpy(before,&live_object_model_context,sizeof(before));assert(!commit());assert(!memcmp(before,&live_object_model_context,sizeof(before)));assert(nf_context_refresh_stats[1]==0&&nf_context_refresh_stats[2]==1);}while(0)
int main(void){
 reset();assert(commit()&&live_object_model_context.frame==101&&live_object_model_context.verified&&nf_context_refresh_stats[1]==1);
 assert(nf_context_refresh_commit(0x03007dc8,0x02004458,2,458,101)&&nf_context_refresh_stats[3]==1);
 REJECT(live_object_model_context.verified=0);REJECT(live_object_model_context.expected=0);
 REJECT(live_object_model_context.address^=4);REJECT(live_object_model_context.object^=4);
 REJECT(live_object_model_context.epoch^=1);REJECT(live_object_model_context.serial^=1);
 REJECT(live_object_model_context.frame=99);REJECT(live_object_model_context.frame=102);REJECT(live_object_model_context.frame=UINT32_MAX);
 REJECT(live_scene.begin=101);REJECT(actual[67]^=1);REJECT(read_ok=0);
 reset();nf_context_rejection_capture(0x03007dc8,0x02004458,2,458,101);
 assert(nf_context_rejection_detail[5]==101&&nf_context_rejection_detail[11]==100&&nf_context_rejection_detail[12]&&nf_context_rejection_detail[13]&&live_object_model_context.frame==100);
 puts("PASS_GUARDED_ONE_REFRESH_CONTEXT_HANDOFF");return 0;
}
'''
p=out/'test-context-handoff.c';p.write_text(code);env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
cmd=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(source),str(p),'-o',str(out/'test-context-handoff.exe')];subprocess.run(cmd,env=env,check=True);r=subprocess.run([str(out/'test-context-handoff.exe')],env=env,capture_output=True,text=True,check=True);assert r.stdout.strip()=='PASS_GUARDED_ONE_REFRESH_CONTEXT_HANDOFF'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report=dict(result='PASS_GUARDED_ONE_REFRESH_CONTEXT_HANDOFF',source_sha256=sha(source/'model_context_refresh.inc'),script_sha256=sha(Path(__file__)),command=cmd,binary_sha256=sha(out/'test-context-handoff.exe'),verified=['one_refresh_commit','same_frame_no_change','unverified_or_unexpected_reject','address_object_epoch_serial_reject','two_refresh_future_overflow_reject','prior_scene_frame_reject','changed_context_bytes_or_read_failure_reject','failure_atomic','diagnostic_readonly'])
(out/'context-handoff-helper-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

from pathlib import Path
import hashlib,json,os,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');src=root/'work/pc';out=Path('C:/NFSUG-Workspace/NFSUG-pc-present-deadline-tests')
code=r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "present_deadline.h"
int main(void){
 NFPresentDeadline c={100.0};double period=1.0/60.0;
 assert(nf_present_due(&c,100.0));nf_present_completed(&c,100.0);
 assert(!nf_present_due(&c,100.001));assert(nf_present_wait(&c,100.001)==16);
 /* 20 source wakeups in every slot cannot authorize an extra presentation. */
 for(unsigned i=0;i<60000;i++){
  double due=c.next;
  for(unsigned j=1;j<=20;j++)assert(!nf_present_due(&c,due-period*(21-j)/21));
  assert(nf_present_due(&c,due));assert(nf_present_wait(&c,due)==0);
  nf_present_completed(&c,due+0.001);
  assert(c.next>due+0.001);assert(fabs(c.next-(due+period))<1e-9);
 }
 double phase=c.next,late=phase+0.153;
 nf_present_completed(&c,late);assert(c.next>late&&c.next<=late+period+1e-9);
 assert(!nf_present_due(&c,late));assert(nf_present_wait(&c,late)>0);
 /* A blocked swap spanning seconds skips missed slots with bounded wait. */
 late=c.next+3.7;nf_present_completed(&c,late);
 assert(c.next>late&&c.next<=late+period+1e-9);assert(nf_present_wait(&c,late)<=17);
 puts("PASS_60000_DEADLINES_1200000_EARLY_WAKEUPS_AND_STALLS");return 0;
}
'''
p=out/'test_present_deadline.c';p.write_text(code)
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-I'+str(src),str(p),'-o',str(out/'test_present_deadline.exe')]
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=60);(out/'deadline-component-build.log').write_text(r.stdout+r.stderr);r.check_returncode()
r=subprocess.run([str(out/'test_present_deadline.exe')],env=env,capture_output=True,text=True,timeout=30);r.check_returncode();print(r.stdout)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(out/'deadline-component-report.json').write_text(json.dumps(dict(result=r.stdout.strip(),header_sha256=sha(src/'present_deadline.h'),test_sha256=sha(p),command=cmd),indent=2))
